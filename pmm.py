from typing import List, Tuple
from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from outputtx import OutputTx
from copy import deepcopy
from poolstatus import PoolStatusInterface, PMMPoolStatus, MultiTokenPoolStatus
from price import Price

class PMM(MarketMakerInterface):
    def __init__(self, token_pairs: List[List[str]], token_info: List[List[float]],
                 reset_batch: str = "False", reset_tx: str = "False", arb: str = "True"):
        """
        token_pairs of form: [
                             ["BTC", "ETH"]
                             ["ETH", "BTC"]
                             ["BTC", "USDT"]
                             ["USDT", "BTC"]
                             ]

        token_info of form: [
                            [1100, 500, 0.2],
                            [500, 1100, 0.2],
                            [200, 500, 0.5],
                            [500, 200, 0.5],
                            ]

        reset_batch: True if reset PMM to initial state after every batch

        reset_tx: True if reset PMM to initial state after every InputTx

        arb: True if need to perform arbitrage
        """
        dictionary = {}
        for i, tup in enumerate(token_pairs):
            dictionary[tuple(tup)] = tuple(token_info[i])

        self.balances = dictionary
        self.equilibriums = deepcopy(dictionary)

        self.reset_batch = reset_batch == "True"
        self.reset_tx = reset_tx == "True"
        self.arb = arb == "True"

    def configure_arbitrage(self, arb_period: int, arb_actions: int):
        assert arb_period > 0
        self.arb_period = arb_period

    def __setEquilibrium(self, pool: tuple, execute: bool = False):
        firstIsLong = True
        if self.balances[pool][0] / self.equilibriums[pool][0] >= self.balances[pool][1] / self.equilibriums[pool][1]:
            l_b = self.balances[pool][0]
            s_b = self.balances[pool][1]
            l_e = self.equilibriums[pool][0]
            p = self.prices[pool[1]] / self.prices[pool[0]]
        else:
            l_b = self.balances[pool][1]
            s_b = self.balances[pool][0]
            l_e = self.equilibriums[pool][1]
            p = self.prices[pool[0]] / self.prices[pool[1]]
            firstIsLong = False

        k = self.balances[pool][2]
        s_e = s_b + s_b / (2 * k) * ((1 + (4 * k * (l_b - l_e)) / (s_b * p)) ** 0.5 - 1)

        other_pool = (pool[1], pool[0])
        if firstIsLong:
            in_e = l_e
            out_e = s_e
            if execute:
                self.equilibriums[pool] = (l_e, s_e)
                self.equilibriums[other_pool] = (s_e, l_e)
        else:
            in_e = s_e
            out_e = l_e
            if execute:
                self.equilibriums[pool] = (s_e, l_e)
                self.equilibriums[other_pool] = (l_e, s_e)

        return in_e, out_e # in equilibrium, out equilibrium

    def __priceCurve(self, x, l_e, s_e, p, k):
        return l_e - p * (x - s_e) * (1 - k + k * s_e / x)

    def __curveTraverse(self, y, l_e, s_e, p, k, precision=1e-8):
        p0 = 0
        p1 = s_e
        m = (p0 + p1) / 2
        y_m = self.__priceCurve(m, l_e, s_e, p, k)

        while abs(y - y_m) > precision and p1 - p0 > precision:
            if y_m > y:
                p0 = m
            else:
                p1 = m
            m = (p0 + p1) / 2
            y_m = self.__priceCurve(m, l_e, s_e, p, k)

        return m

    def swap(self, tx: InputTx, execute: bool = False, precision: float = 1e-8):
        intype = tx.intype
        outtype = tx.outtype
        pool = (intype, outtype)
        assert pool in self.balances, "nonexistent trading pair"

        d = tx.inval
        k = self.balances[pool][2]
        p = self.prices[outtype] / self.prices[intype]
        p_i = 1 / p
        in_e, out_e = self.__setEquilibrium(pool, execute)

        input_balance_0 = self.balances[pool][0]
        output_balance_0 = self.balances[pool][1]
        i_1 = input_balance_0 + d

        if self.balances[pool][1] / out_e > self.balances[pool][0] / in_e:
            s_e, l_e = in_e, out_e
            static_amt = s_e - input_balance_0

            if static_amt < d:
                amt = output_balance_0 - l_e
                l_1 = d - static_amt + s_e
                new_pt = self.__curveTraverse(l_1, s_e, l_e, p, k, precision)
                amt += l_e - new_pt
            else:
                new_pt = self.__priceCurve(i_1, l_e, s_e, p_i, k)
                amt = output_balance_0 - new_pt

            assert self.balances[pool][1] > amt and amt > 0, str({"d": d, "s_e": s_e, "l_e": l_e, "s": input_balance_0, "l": output_balance_0, "S": self.balances[pool][0], "L": self.balances[pool][1], "p": p, "k": k, "new_pt": new_pt})
        else:
            s_e, l_e = out_e, in_e
            new_pt = self.__curveTraverse(i_1, l_e, s_e, p, k, precision)
            amt = output_balance_0 - new_pt

            assert self.balances[pool][1] > amt and amt > 0, str({"d": d, "s_e": s_e, "l_e": l_e, "s": output_balance_0, "l": input_balance_0, "S": self.balances[pool][1], "L": self.balances[pool][0], "p": p, "k": k, "new_pt": new_pt})

        if execute:
            self.balances[pool] = (self.balances[pool][0] + d, self.balances[pool][1] - amt, self.balances[pool][-1])
            self.balances[(pool[1], pool[0])] = (self.balances[pool][1], self.balances[pool][0], self.balances[pool][-1])

            return {"amt": amt,
                    "market_rate": p,
                    "swap_rate": d / amt,
                    "in_equilibrium": in_e,
                    "out_equilibrium": out_e,
                    "input_balance_0": input_balance_0,
                    "output_balance_0": output_balance_0,
                    "input_balance_1": i_1,
                    "output_balance_1": self.balances[pool][1]}

        return {"amt": amt,
                "market_rate": p,
                "swap_rate": d / amt,
                "in_equilibrium": in_e,
                "out_equilibrium": out_e,
                "input_balance_0": input_balance_0,
                "output_balance_0": output_balance_0,
                "input_balance_1": i_1,
                "output_balance_1": self.balances[pool][1] - amt}

    def arbitrage(self, precision: float = 1e-8):
        while True:
            pair = None
            amt = 0
            for tup in self.balances:
                tx = InputTx(0, tup[0], tup[1], 1)
                info = self.swap(tx)
                if info["in_equilibrium"] - self.balances[tup][0] > precision:
                    pair = tup
                    amt = info["in_equilibrium"] - self.balances[tup][0]

            if pair != None and amt != 0:
                self.swap(InputTx(0, pair[0], pair[1], amt), True)
            else:
                break

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Price]
    ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]], PoolStatusInterface, PoolStatusInterface, List[float], List[float]]:
        outputs = []
        status = []
        initial_rates = []
        after_rates = []

        initial_copy = PMMPoolStatus(deepcopy(self.balances))

        if self.reset_batch or self.reset_tx:
            balance_copy = deepcopy(self.balances)
            equilibrium_copy = deepcopy(self.equilibriums)

        for j, batch in enumerate(traffic):
            self.prices = external_price[j]

            batch_output = []
            batch_status = []

            if self.reset_batch or self.reset_tx:
                self.balances = balance_copy
                self.equilibriums = equilibrium_copy
                balance_copy = deepcopy(self.balances)
                equilibrium_copy = deepcopy(self.equilibriums)

            for tx in batch:
                probe = InputTx(0, tx.intype, tx.outtype, 1)
                initial_rate = initial_rates.append(self.swap(probe)["swap_rate"])
                info = self.swap(tx, True)
                after_rate = after_rates.append(self.swap(probe)["swap_rate"])

                batch_output.append(OutputTx(tx.index,
                                            tx.intype, tx.outtype,
                                            tx.inval, info["amt"],
                                            info["input_balance_0"], info["output_balance_0"],
                                            info["input_balance_1"], info["output_balance_1"],
                                            info["swap_rate"], info["market_rate"],
                                            "PMM"))

                batch_status.append(PMMPoolStatus(deepcopy(self.balances)))

                if self.arb and tx.index != 0 and tx.index % self.arb_period == 0:
                    self.arbitrage()

                if self.reset_tx:
                    self.balances = balance_copy
                    self.equilibriums = equilibrium_copy
                    balance_copy = deepcopy(self.balances)
                    equilibrium_copy = deepcopy(self.equilibriums)

            outputs.append(batch_output)
            status.append(batch_status)

        self.arbitrage()

        return outputs, status, initial_copy, PMMPoolStatus(self.balances), initial_rates, after_rates
