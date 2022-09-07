from typing import List, Tuple
from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from outputtx import OutputTx
from price import Price
from poolstatus import PoolStatusInterface, MultiTokenPoolStatus
from copy import deepcopy

class MPMM(MarketMakerInterface):
    def __init__(self, tokens: List[str], token_info: List[float], reset_batch: str = "False",
                 reset_tx: str = "False", arb: str = "True", final_arb: int = 100):
        """
        tokens of the form: ["BTC", "ETH", "USDT"]

        token_info of the form: [[1100, 0.2], [2000, 0.1], [1000, 0.5]]

        reset_batch: True if reset MPMM to initial state after every batch

        reset_tx: True if reset PMM to initial state after every InputTx

        arb: True if need to perform arbitrage

        final_arb: number or arbitrage actions to perform at very end
        """
        self.token_info = {}
        for i, name in enumerate(tokens):
            self.token_info[name] = tuple(token_info[i])
        self.balances = {t: self.token_info[t][0] for t in self.token_info}

        self.reset_batch = reset_batch == "True"
        self.reset_tx = reset_tx == "True"
        self.arb = arb == "True"
        self.final_arb = final_arb

    def configure_arbitrage(self, arb_period: int, arb_actions: int):
        assert arb_period > 0 and arb_actions > 0
        self.arb_period = arb_period
        self.arb_actions = arb_actions

    def __newtonMethod(self, approx, s, k, p, l, S, L, precision=1e-8):
        new_approx = self.__updateApprox(approx, s, k, p, l, S, L)

        while abs(new_approx - approx) > precision:
            approx = new_approx
            new_approx = self.__updateApprox(approx, s, k, p, l, S, L)

        return new_approx

    def __updateApprox(self, x, s, k, p, l, S, L):
        func = (2*(1-((s*(((4*k*(l-x))/(p*s)+1)**0.5-1))/(2*k)+s)/S))/(S*p*((4*k*(l-x))/(p*s)+1)**0.5)-(2*(1-x/L))/L
        deriv = 2/(S**2*p**2*((4*k*(l-x))/(p*s)+1))+(4*k*(1-((s*(((4*k*(l-x))/(p*s)+1)**0.5-1))/(2*k)+s)/S))/(S*p**2*s*((4*k*(l-x))/(p*s)+1)**(3/2))+2/L**2

        new_x = x - func / deriv
        while(True):
            new_func = (2*(1-((s*(((4*k*(l-new_x))/(p*s)+1)**0.5-1))/(2*k)+s)/S))/(S*p*((4*k*(l-new_x))/(p*s)+1)**0.5)-(2*(1-new_x/L))/L
            new_deriv = 2/(S**2*p**2*((4*k*(l-new_x))/(p*s)+1))+(4*k*(1-((s*(((4*k*(l-new_x))/(p*s)+1)**0.5-1))/(2*k)+s)/S))/(S*p**2*s*((4*k*(l-new_x))/(p*s)+1)**(3/2))+2/L**2

            if new_func != new_func or new_deriv != new_deriv or isinstance(new_func, complex) or isinstance(new_deriv, complex):
                new_x = (x + new_x) / 2
            else:
                break

        return new_x

    def __shortFunc(self, l_e, s, S, l, L, p, k):
        return s + s / (2*k) * ((1 + (4*k * (l - l_e)) / (s * p))**0.5 - 1)

    def __getEquilibrium(self, short, long, k, p, precision=1e-8):
        s = self.balances[short]
        S = self.token_info[short][0]
        l = self.balances[long]
        L = self.token_info[long][0]
        approx = min(s/S, l/L) * min([s, S, l, L])

        l_e = self.__newtonMethod(approx, s, k, p, l, S, L, precision)

        return self.__shortFunc(l_e, s, S, l, L, p, k), l_e

    def __distSq(self, x0, y0, x1, y1):
        return (1 - x1 / x0) ** 2 + (1 - y1 / y0) ** 2

    def __optimizeEquilibrium(self, intype, outtype, k, p, precision=1e-8):
        lst = []
        I, O = self.token_info[intype][0], self.token_info[outtype][0]

        in_0, out_0 = self.balances[intype], self.balances[outtype]
        lst.append(((in_0, out_0), self.__distSq(I, O, in_0, out_0)))

        in_1, out_1 = self.__getEquilibrium(intype, outtype, k, 1 / p, precision)
        if in_1 != None and in_1 > 0 and out_1 > 0 and ((in_1 > in_0 and out_1 < out_0) or (out_1 > out_0 and in_1 < in_0)):
            lst.append(((in_1, out_1), self.__distSq(I, O, in_1, out_1)))

        out_2, in_2 = self.__getEquilibrium(outtype, intype, k, p, precision)
        if in_2 != None and in_2 > 0 and out_2 > 0 and ((in_2 > in_0 and out_2 < out_0) or (out_2 > out_0 and in_2 < in_0)):
            lst.append(((in_2, out_2), self.__distSq(I, O, in_2, out_2)))

        return lst

    def __priceCurve(self, x, l_e, s_e, p, k):
        return l_e - p * (x - s_e) * (1 - k + k * s_e / x)

    def __curveTraverse(self, y, l_e, s_e, p, k, tolerance=1e-8):
        p0 = 0
        p1 = s_e
        m = (p0 + p1) / 2
        y_m = self.__priceCurve(m, l_e, s_e, p, k)

        while abs(y - y_m) > tolerance and p1 - p0 > tolerance:
            if y_m > y:
                p0 = m
            else:
                p1 = m
            m = (p0 + p1) / 2
            y_m = self.__priceCurve(m, l_e, s_e, p, k)

        return m

    def swap(self, tx: InputTx, execute=False, tolerance=1e-8, precision=1e-8):
        intype = tx.intype
        outtype = tx.outtype
        d = tx.inval
        k = max(self.token_info[intype][1], self.token_info[outtype][1])
        p = self.prices[outtype] / self.prices[intype]
        p_i = 1 / p
        equilibriums = self.__optimizeEquilibrium(intype, outtype, k, p, precision)

        input_balance_0 = self.balances[intype]
        output_balance_0 = self.balances[outtype]
        i_1 = input_balance_0 + d

        in_e = input_balance_0
        out_e = output_balance_0
        dist = equilibriums[0][1]
        for lst in equilibriums[1:]:
            if lst[1] < dist:
                temp_in_e = lst[0][0]
                temp_out_e = lst[0][1]
                if output_balance_0 / temp_out_e > input_balance_0 / temp_in_e:
                    s_e, l_e = temp_in_e, temp_out_e

                    if s_e + tolerance >= input_balance_0 and l_e <= output_balance_0 + tolerance:
                        test_val = self.__priceCurve(input_balance_0, l_e, s_e, p_i, k)

                        if abs(test_val - output_balance_0) < tolerance:
                            in_e = temp_in_e
                            out_e = temp_out_e
                            dist = lst[1]

                else:
                    s_e, l_e = temp_out_e, temp_in_e

                    if s_e + tolerance >= input_balance_0 and l_e <= output_balance_0 + tolerance:
                        test_val = self.__priceCurve(output_balance_0, l_e, s_e, p, k)

                        if abs(test_val - input_balance_0) < tolerance:
                            in_e = temp_in_e
                            out_e = temp_out_e
                            dist = lst[1]

        if output_balance_0 / out_e > input_balance_0 / in_e:
            s_e, l_e = in_e, out_e
            assert s_e + tolerance >= input_balance_0 and l_e <= output_balance_0 + tolerance, str({"s_e": s_e, "l_e": l_e, "s": input_balance_0, "l": output_balance_0, "S": self.token_info[intype][0], "L": self.token_info[outtype][0], "p": p, "k": k})
            static_amt = s_e - input_balance_0

            if static_amt < d:
                amt = output_balance_0 - l_e
                l_1 = d - static_amt + s_e
                new_pt = self.__curveTraverse(l_1, s_e, l_e, p, k, precision)
                amt += l_e - new_pt
            else:
                new_pt = self.__priceCurve(i_1, l_e, s_e, p_i, k)
                amt = output_balance_0 - new_pt

            assert self.balances[outtype] > amt and amt > 0, str({"d": d, "s_e": s_e, "l_e": l_e, "s": input_balance_0, "l": output_balance_0, "S": self.token_info[intype][0], "L": self.token_info[outtype][0], "p": p, "k": k, "new_pt": new_pt})
        else:
            s_e, l_e = out_e, in_e
            assert s_e + tolerance >= output_balance_0 and l_e <= input_balance_0 + tolerance, str({"s_e": s_e, "l_e": l_e, "s": output_balance_0, "l": input_balance_0, "S": self.token_info[outtype][0], "L": self.token_info[intype][0], "p": p, "k": k})
            new_pt = self.__curveTraverse(i_1, l_e, s_e, p, k, precision)
            amt = output_balance_0 - new_pt

            assert self.balances[outtype] > amt and amt > 0, str({"d": d, "s_e": s_e, "l_e": l_e, "s": output_balance_0, "l": input_balance_0, "S": self.token_info[outtype][0], "L": self.token_info[intype][0], "p": p, "k": k, "new_pt": new_pt})

        if execute:
            self.balances[outtype] -= amt
            self.balances[intype] += d

            return {"amt": amt,
                    "market_rate": p,
                    "swap_rate": d / amt,
                    "in_equilibrium": in_e,
                    "out_equilibrium": out_e,
                    "input_balance_0": input_balance_0,
                    "output_balance_0": output_balance_0,
                    "input_balance_1": self.balances[intype],
                    "output_balance_1": self.balances[outtype]}

        return {"amt": amt,
                "market_rate": p,
                "swap_rate": d / amt,
                "in_equilibrium": in_e,
                "out_equilibrium": out_e,
                "input_balance_0": input_balance_0,
                "output_balance_0": output_balance_0,
                "input_balance_1": self.balances[intype] + d,
                "output_balance_1": self.balances[outtype] - amt}

    def arbitrage(self):
        tokens = list(self.token_info.keys())
        for i in range(self.arb_actions):
            pair = None
            rate = 1
            input_amt = 0

            for t1 in tokens:
                for t2 in tokens:
                    if t1 != t2:
                        info = self.swap(InputTx(0, t1, t2, 1))
                        d = info["in_equilibrium"] - self.balances[t1]
                        amt = info["output_balance_0"] - info["out_equilibrium"]

                        if d == 0 or amt == 0:
                            curr_rate = 1
                        else:
                            curr_rate = d / amt / info["market_rate"]

                        if curr_rate < rate:
                            rate = curr_rate
                            pair = (t1, t2)
                            input_amt = d

            if input_amt > 0:
                self.swap(InputTx(0, pair[0], pair[1], input_amt), True)
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

        pool_dict = {}
        for t in self.balances:
            pool_dict[t] = (self.balances[t], self.token_info[t][1])
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
                                            "MPMM"))

                for t in self.balances:
                    pool_dict[t] = (self.balances[t], self.token_info[t][1])
                batch_status.append(MultiTokenPoolStatus(deepcopy(pool_dict)))

                if self.arb and tx.index != 0 and tx.index % self.arb_period == 0:
                    self.arbitrage()

                if self.reset_tx:
                    self.balances = balance_copy
                    balance_copy = deepcopy(self.balances)

            outputs.append(batch_output)
            status.append(batch_status)

        self.arb_actions = self.final_arb
        self.arbitrage()
        for t in self.balances:
            pool_dict[t] = (self.balances[t], self.token_info[t][1])

        return outputs, status, initial_copy, MultiTokenPoolStatus(pool_dict), initial_rates, after_rates
