from typing import List, Tuple
from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from outputtx import OutputTx
from price import Price
from poolstatus import PoolStatusInterface, MultiTokenPoolStatus
from copy import deepcopy


class MCSMM(MarketMakerInterface):
    def __init__(self, tokens: List[str], token_info: List[float], reset_batch: str = "False",
                 reset_tx: str = "False"):
        """
        tokens of the form: ["BTC", "ETH", "USDT"]

        token_info of the form: [[1100, 0], [2000, 0], [1000, 0]]

        reset_batch: True if reset CSMM to initial state after every batch

        reset_tx: True if reset CSMM to initial state after every InputTx
        """
        self.balances = {tokens[i]: token_info[i][0] for i in range(len(tokens))}

        self.reset_batch = reset_batch == "True"
        self.reset_tx = reset_tx == "True"

    def configure_arbitrage(self, arb_period: int, arb_actions: int):
        # there is no arbitrage
        pass

    def swap(self, tx: InputTx):
        intype = tx.intype
        outtype = tx.outtype
        d = tx.inval
        p = self.prices[outtype] / self.prices[intype]

        input_balance_0 = self.balances[intype]
        output_balance_0 = self.balances[outtype]

        # Balance cannot go negative
        if (d / p > output_balance_0):
            # refuse transaction if amt drains balance
            amt = 0
            d = 0
        else:
            amt = d / p

        self.balances[intype] += d
        self.balances[outtype] -= amt

        return {"amt": amt,
                "market_rate": p,
                "swap_rate": p,
                "input_balance_0": input_balance_0,
                "output_balance_0": output_balance_0,
                "input_balance_1": self.balances[intype], #enabled
                "output_balance_1": self.balances[outtype] #enabled
                }

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Price]
                         ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]], PoolStatusInterface, PoolStatusInterface, List[float], List[float]]:
        outputs = []
        status = []
        rates = []

        pool_dict = {}
        for t in self.balances:
            pool_dict[t] = (self.balances[t], 0.5)
        initial_copy = MultiTokenPoolStatus(deepcopy(pool_dict))

        if self.reset_batch or self.reset_tx:
            balance_copy = deepcopy(self.balances)

        for j, batch in enumerate(traffic):
            self.prices = external_price[j]

            batch_output = []
            batch_status = []

            if self.reset_batch or self.reset_tx:
                self.balances = balance_copy
                balance_copy = deepcopy(self.balances)

            for c, tx in enumerate(batch):
                info = self.swap(tx)
                rates.append(info["swap_rate"])

                batch_output.append(OutputTx(tx.index,
                                            tx.intype, tx.outtype,
                                            tx.inval, info["amt"],
                                            info["input_balance_0"], info["output_balance_0"],
                                            info["input_balance_0"], info["output_balance_0"],
                                            info["swap_rate"], info["market_rate"],
                                            "MCSMM"))

                for t in self.balances:
                    pool_dict[t] = (self.balances[t], 0.5)
                batch_status.append(MultiTokenPoolStatus(pool_dict))

                if self.reset_tx:
                    self.balances = balance_copy
                    balance_copy = deepcopy(self.balances)

            outputs.append(batch_output)
            status.append(batch_status)

        for t in self.balances:
            pool_dict[t] = (self.balances[t], 0.5)

        return outputs, status, initial_copy, MultiTokenPoolStatus(pool_dict), rates, rates
