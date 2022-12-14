from typing import List, Tuple, Dict
from inputtx import InputTx
from outputtx import OutputTx
from poolstatus import PoolStatusInterface
from copy import deepcopy

class MarketMakerInterface:
    def configure_simulation(self, reset_tx: str = "False", arb: str = "True",
    arb_actions: int = 1, multi_token: str = "True"):
        """
        Configures settings for traffic simulation

        Parameters:
        1. reset_tx: whether or not the pool should be reset after every swap
        2. arb: whether or not arbitrage opportunities are acted on
        3. arb_actions: how many swaps can occur for one arbitrage opportunity
        4. multi_token: indicates if there are multi token pools
        """
        self.reset_tx = reset_tx == "True"
        self.arb = arb == "True"
        self.arb_actions = arb_actions
        self.multi_token = multi_token == "True"
    
    def configure_crash_types(self, crash_type: List[str] = []):
        """
        Configures crashing price tokens

        Parameters:
        1. crash type: if not empty, specifies the token type(s) that will never be
        removed from the pool
        """
        self.crash_type = crash_type

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Dict[str, float]]
    ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]],
    PoolStatusInterface, List[str]]:
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
        self.prices = external_price[0]
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
                if tx.is_arb and self.arb:
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

        return txs, stats, initial_copy, self.crash_type
    
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
                in0, out0 = self.token_info[tx.intype][0], self.token_info[tx.outtype][0]
                
                if execute:
                    self.token_info[tx.intype][0] += tx.inval
                    self.token_info[tx.outtype][0] -= out_amt
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
                in_type = tx.intype,
                out_type = tx.outtype,
                inpool_init_val = in0,
                outpool_init_val = out0,
                inpool_after_val = in0 + tx.inval,
                outpool_after_val = out0 - out_amt,
                market_rate = self.prices[tx.outtype] / self.prices[tx.intype],
                after_rate = 1
            ), deepcopy(self.token_info)
    
    def calculate_equilibriums(self, intype: str, outtype: str) -> Tuple[float, float, float]:
        """
        Calculates and returns equilibrium balances

        Parameters:
        1. intype: input token type
        2. outtype: output token type

        Returns:
        1. equilibrium balance for input token
        2. equilibrium balance for output token
        3. k value, if it is relevant
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
                        if not tok2 in self.crash_type:
                            rate_dict = self.getRate(pool)
                            if rate_dict["rate"] > info[1]["rate"] and \
                                rate_dict["in_amt"] > lim:
                                info[0] = pool
                                info[1] = rate_dict
                        if not tok1 in self.crash_type:
                            rate_dict = self.getRate(reverse_pool)
                            if rate_dict["rate"] > info[1]["rate"] and \
                                rate_dict["in_amt"] > lim:
                                info[0] = reverse_pool
                                info[1] = rate_dict
            else:
                for p in self.token_info.keys():
                    if not p[1] in self.crash_type:
                        rate_dict = self.getRate(p)
                        if rate_dict["rate"] > info[1]["rate"] and \
                            rate_dict["in_amt"] > lim:
                            info[0] = p
                            info[1] = rate_dict

            if info[1]["rate"] > 1 and info[1]["in_amt"] > 0:
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
        market_rate = self.prices[pool[1]] / self.prices[pool[0]]

        if self.multi_token:
            in_amt, out_amt = \
                in_e - self.token_info[pool[0]][0], self.token_info[pool[1]][0] - out_e
        else:
            in_amt, out_amt = \
                in_e - self.token_info[pool][0], self.token_info[pool][1] - out_e
        
        try:
            internal_rate = in_amt / out_amt
        except:
            internal_rate = 1
        if internal_rate == 0:
            internal_rate = 1

        return {
                "in_amt": in_amt,
                "out_amt": out_amt,
                "rate": market_rate / internal_rate
            }
