from typing import List, Tuple, Dict
from inputtx import InputTx
from outputtx import OutputTx
from price import Price
from poolstatus import PoolStatusInterface
from copy import deepcopy

class MarketMakerInterface:
    def configure_simulation(self, reset_tx: str = "False", arb: str = "True",
    arb_actions: int = 1, crash_type: str = "None", multi_token: str = "True"):
        """
        Configures settings for traffic simulation

        Parameters:
        1. reset_tx: whether or not the pool should be reset after every swap
        2. arb: whether or not arbitrage opportunities are acted on
        3. arb_actions: how many swaps can occur for one arbitrage opportunity
        4. crash_type: if not "None", specifies the token type that will never be
        removed from the pool
        5. multi_token: indicates if there are multi token pools
        """
        self.reset_tx = reset_tx == "True"
        self.arb = arb == "True"
        self.arb_actions = arb_actions
        self.crash_type = crash_type
        self.multi_token = multi_token == "True"

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Price]
    ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]],
         PoolStatusInterface, PoolStatusInterface]:
        """
        Given a traffic and price data, simulate swaps

        Parameters:
        1. traffic: 2-d list of transactions to simulate
        2. external_price: 1-d list of token prices (defined per batch)

        Returns:
        1. output information associated with each swap
        2. status of pool after each swap
        3. initial status of pool
        4. final status of pool
        """
        self.external_price = external_price[0]
        initial_copy = deepcopy(self.token_info)

        txs = []
        stats = []

        if self.reset_tx:
            token_info_copy = deepcopy(self.token_info)
            equilibrium_copy = deepcopy(self.equilibriums)

        for j, batch in enumerate(traffic):
            self.prices = external_price[j]
            batch_txs = []
            batch_stats = []

            if self.reset_tx:
                self.token_info = token_info_copy
                self.equilibriums = equilibrium_copy
                token_info_copy = deepcopy(self.token_info)
                equilibrium_copy = deepcopy(self.equilibriums)

            for tx in batch:
                if tx.is_arb:
                    output_lst, stat_lst = self.arbitrage()
                    for i in output_lst:
                        batch_txs.append(i)
                    for i in stat_lst:
                        batch_stats.append(i)
                else:
                    info, stat = self.swap(tx, None)
                    batch_txs.append(info)
                    batch_stats.append(stat)

                if self.reset_tx:
                    self.token_info = token_info_copy
                    token_info_copy = deepcopy(self.token_info)

            txs.append(batch_txs)
            stats.append(batch_stats)

        return txs, stats, initial_copy, self.token_info
    
    def swap(self, tx: InputTx, out_amt: float, execute: bool = True
    ) -> Tuple[OutputTx, PoolStatusInterface]:
        """
        Initiate a swap specified by tx given that the amount of output token removed
        is known

        Parameters:
        1. tx: transaction
        2. out_amt: specifies the amount of output token removed
        3. execute: whether or not to execute the swap
        
        Returns:
        1. output information associated with swap (after_rate is incorrect)
        2. status of pool ater swap
        """
        if out_amt == None:
            raise NotImplementedError
        else:
            if self.multi_token:
                in0, out0 = self.token_info[tx.intype], self.token_info[tx.outtype]
                
                if execute:
                    self.token_info[tx.intype] += tx.inval
                    self.token_info[tx.outtype] -= out_amt
            else:
                pool_info = self.token_info[(tx.intype, tx.outtype)]
                in0, out0 = pool_info[0], pool_info[1]

                if execute:
                    pool_info[0] += tx.inval
                    pool_info[1] -= out_amt

                    reverse_pool = self.token_info[(tx.outtype, tx.intype)]
                    reverse_pool[0] -= out_amt
                    reverse_pool[1] += tx.inval
            
            return OutputTx(
                input_token_type = in0,
                output_token_type = out0,
                inpool_init_val = in0,
                outpool_init_val = out0,
                inpool_after_val = in0 + tx.inval,
                outpool_after_val = out0 - out_amt,
                market_rate = self.external_price[tx.outtype] / self.external_price[tx.intype],
                after_rate = 1
            ), deepcopy(self.token_info)
    
    def calculate_equilibriums(self, intype: str, outtype: str) -> Tuple[float, float]:
        """
        Calculates and returns equilibrium balances

        Parameters:
        1. intype: input token type
        2. outtype: output token type

        Returns:
        1. Equilibrium balance for input token
        2. Equilibrium balance for output token
        """
        raise NotImplementedError
    
    def arbitrage(self, lim: float = 1e-8) -> Tuple[List[OutputTx], List[PoolStatusInterface]]:
        """
        Performs self.arb_actions arbitrage swaps by returning token pairs "furthest"
        from equilibrium to an equilibrium defined by market exchange rates

        Parameters:
        1. lim: how large the input token amount must be to execute the arbitrage

        Returns:
        1. list of OutputTx detailing arbitrage swap details
        2. list of pool statuses after each arbitrage swap
        """
        outputtx_lst, poolstatus_lst = [], []
        info = [("str", "str"), {"rate": -1}]

        for i in range(self.arb_actions):
            if self.multi_token:
                tokens = list(self.token_info.keys())
                for c, tok1 in enumerate(tokens):
                    for tok2 in tokens[c+1:]:
                        pool = (tok1, tok2)
                        reverse_pool = (tok2, tok1)
                        if tok2 != self.crash_type:
                            rate_dict = self.getRate(pool)
                            if rate_dict["rate"] > info[0]["rate"] and \
                                rate_dict["in_amt"] > lim:
                                info[0] = pool
                                info[1] = rate_dict
                        if tok1 != self.crash_type:
                            rate_dict = self.getRate(reverse_pool)
                            if rate_dict["rate"] > info[0]["rate"] and \
                                rate_dict["in_amt"] > lim:
                                info[0] = reverse_pool
                                info[1] = rate_dict
            else:
                for p in self.token_info.keys():
                    if not p[1] == self.crash_type:
                        rate_dict = self.getRate(p)
                        if rate_dict["rate"] > info[0]["rate"] and \
                            rate_dict["in_amt"] > lim:
                            info[0] = p
                            info[1] = rate_dict

            if info[1]["rate"] > 0 and info[1]["in_amt"]> 0:
                output, token_info = self.swap(InputTx(info[0][0], info[0][1], \
                    info[1]["in_amt"]), info[1]["out_amt"])
                outputtx_lst.append(output)
                poolstatus_lst.append(token_info)
            else:
                break
        
        return outputtx_lst, poolstatus_lst         
    
    def getRate(self, pool: Tuple[str, str]) -> Dict[str, float]:
        """
        Returns statistics about moving the intype and outtype to an equilibrium

        Parameters:
        1. token pool, in order of intype and outtype

        Returns:
        1. A dictionary of the form:
        {
            "in_amt": amount of intype token to input to reach equilibrium,
            "out_amt": amount of outtype token to remove to reach equilibrium,
            "rate": ratio of internal exchange rate to market rate
        }
        """
        in_e, out_e = self.calculate_equilibriums(pool[0], pool[1])
        market_rate = self.external_price[pool[1]] / self.external_price[pool[0]]

        if self.multi_token:
            in_amt, out_amt = \
                in_e - self.token_info[pool[0]], self.token_info[pool[1]] - out_e
        else:
            in_amt, out_amt = \
                in_e - self.token_info[pool][0], self.token_info[pool][1] - out_e

        return {
                "in_amt": in_amt,
                "out_amt": out_amt,
                "rate": market_rate / abs(in_amt / out_amt)
            }
