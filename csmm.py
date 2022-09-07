from typing import List, Tuple
from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from outputtx import OutputTx
from price import Price
from poolstatus import PoolStatusInterface, PairwiseTokenPoolStatus
from copy import deepcopy

class CSMM(MarketMakerInterface):
    def __init__(self, token_pairs: List[Tuple[str]], token_amounts: List[Tuple[float]],
                 reset_batch: str = "False", reset_tx: str = "False"):
        """
        token_pairs of form: [
                             ["BTC", "ETH"]
                             ["ETH", "BTC"]
                             ["BTC", "USDT"]
                             ["USDT", "BTC"]
                             ]

        token_info of form: [
                            [1100, 500],
                            [500, 1100],
                            [200, 500],
                            [500, 200],
                            ]

        reset_batch: True if reset CSMM to initial state after every batch

        reset_tx: True if reset CSMM to initial state after every InputTx
        """
        self.token_info = PairwiseTokenPoolStatus(token_pairs, token_amounts)
        self.reset_batch = reset_batch == "True"
        self.reset_tx = reset_tx == "True"

    def configure_arbitrage(self, arb_period: int, arb_actions: int):
        # there is no arbitrage
        pass

    def swap(self, tx: InputTx):
        intype = tx.intype
        outtype = tx.outtype
        pool = (intype, outtype)
        d = tx.inval
        p = self.prices[outtype] / self.prices[intype]

        input_balance_0 = self.token_info[pool][0]
        output_balance_0 = self.token_info[pool][1]

        # Balance cannot go negative
        if (d / p > output_balance_0):
            # refuse transaction if amt drains balance
            amt = 0
            d = 0
        else:
            amt = d / p

        self.token_info[pool] = (self.token_info[pool][0] + d, self.token_info[pool][1] - amt)
        self.token_info[(pool[1], pool[0])] = (self.token_info[pool][1], self.token_info[pool][0])

        return {"amt": amt,
                "market_rate": p,
                "swap_rate": p,
                "input_balance_0": input_balance_0,
                "output_balance_0": output_balance_0,
                "input_balance_1": self.token_info[pool][0],
                "output_balance_1": self.token_info[pool][1]}

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Price]
                         ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]], PoolStatusInterface, PoolStatusInterface, float, float]:
        outputs = []
        status = []
        rates = []

        initial_copy = deepcopy(self.token_info)

        if self.reset_batch or self.reset_tx:
            token_info_copy = deepcopy(self.token_info)

        for j, batch in enumerate(traffic):
            self.prices = external_price[j]
            batch_output = []
            batch_status = []

            if self.reset_batch or self.reset_tx:
                self.token_info = token_info_copy
                token_info_copy = deepcopy(self.token_info)

            for tx in batch:
                info = self.swap(tx)
                rates.append(info["swap_rate"])
                batch_output.append(OutputTx(tx.index,
                                            tx.intype, tx.outtype,
                                            tx.inval, info["amt"],
                                            info["input_balance_0"], info["output_balance_0"],
                                            info["input_balance_0"], info["output_balance_0"],
                                            info["swap_rate"], info["market_rate"],
                                            "CSMM"))

                batch_status.append(deepcopy(self.token_info))

                if self.reset_tx:
                    self.token_info = token_info_copy
                    token_info_copy = deepcopy(self.token_info)

            outputs.append(batch_output)
            status.append(batch_status)

        return outputs, status, initial_copy, self.token_info, rates, rates
