from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from typing import List, Tuple
from outputtx import OutputTx
from math import sqrt
from poolstatus import PairwiseTokenPoolStatus, PoolStatusInterface
from copy import deepcopy
from price import Price
from random import shuffle


class AMM(MarketMakerInterface):
    def __init__(self, token_pairs: List[Tuple[str]], token_amounts: List[Tuple[float]],
                 reset_batch: str = "False", reset_tx: str = "False", arb: str = "True"):
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

        reset_batch: True if reset AMM to initial state after every batch

        reset_tx: True if reset AMM to initial state after every InputTx

        arb: True if need to perform arbitrage
        """
        self.token_info = PairwiseTokenPoolStatus(token_pairs, token_amounts)
        self.already_executed_txs = []

        self.pair_to_mult_const = {}
        for pair in self.token_info.keys():
            self.pair_to_mult_const[pair] = self.token_info[pair][0] * \
                self.token_info[pair][1]

        self.reset_batch = reset_batch == "True"
        self.reset_tx = reset_tx == "True"
        self.arb = arb == "True"

    def _calc_price(self, in_type: str, in_value: float, out_type: str) -> float:
        in_balance, out_balance = self._get_in_out_balance(in_type, out_type)

        return (in_balance + in_value)/out_balance

    # equalizes all pairs to market price
    def arbitrage(self, all: bool = True):
        if all:
            for pair in self.token_info.keys():
                oracle_price_ratio = self.oracle_price[pair[0]] / \
                    self.oracle_price[pair[1]]
                self.token_info[pair] = (sqrt(self.pair_to_mult_const[pair]/oracle_price_ratio),
                                         sqrt(self.pair_to_mult_const[pair]*oracle_price_ratio))
        else:
            keys = list(self.token_info.keys())
            shuffle(keys)

            for pair in keys[:self.arb_actions]:
                oracle_price_ratio = self.oracle_price[pair[0]] / \
                    self.oracle_price[pair[1]]
                self.token_info[pair] = (sqrt(self.pair_to_mult_const[pair]/oracle_price_ratio),
                                         sqrt(self.pair_to_mult_const[pair]*oracle_price_ratio))

    def complex_arb(self):
        for i in range(self.arb_actions):
            rates = [(p, self.get_rate(p)) for p in self.token_info.keys()]
            rates.sort(key=lambda tup: tup[1])
            pool = rates[0][0]
            stop_rate = rates[1][1]
            if stop_rate > 1:
                break
            self.execute_complex_arb(pool, stop_rate)

    def get_rate(self, pool):
        internal_rate = self.pair_to_mult_const[pool] / (self.token_info[pool][1]) ** 2
        market_rate = self.oracle_price[pool[1]] / self.oracle_price[pool[0]]

        return internal_rate / market_rate

    def execute_complex_arb(self, pool, stop_rate):
        market_rate = self.oracle_price[pool[0]] / self.oracle_price[pool[1]]
        new_out = market_rate * self.pair_to_mult_const[pool] * stop_rate / self.token_info[pool][1]

        new_in = self.pair_to_mult_const[pool] / new_out
        self.token_info[pool] = (new_in, new_out)
        self.token_info[(pool[1], pool[0])] = (new_out, new_in)

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Price]
                         ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]], PoolStatusInterface, PoolStatusInterface, List[float], List[float]]:
        txs, stats, initial_status, final_status, initial_rates, after_rates = self._multiple_swaps(traffic, external_price)
        return (txs, stats, initial_status, final_status, initial_rates, after_rates)

    def _get_in_out_balance(self, in_type, out_type):
        assert((in_type, out_type) in self.token_info.keys() and (
            out_type, in_type) in self.token_info.keys())

        return self.token_info[(in_type, out_type)]

    def _calc_delta_out(self, in_type: str, in_value: float, out_type: str) -> float:
        in_balance, out_balance = self._get_in_out_balance(in_type, out_type)

        return (out_balance*in_value)/(in_balance + in_value)

    def configure_arbitrage(self, arb_period: int, arb_actions: int):
        assert arb_period > 0 and arb_actions > 0
        self.arb_period = arb_period
        self.arb_actions = arb_actions

    def initialize_pool_status(self, status: PoolStatusInterface):
        pass

    def _multiple_swaps(self, input_list, oracle_list):
        self.oracle_price = oracle_list[0]
        self.arbitrage(True)
        initial_copy = deepcopy(self.token_info)

        txs = []
        stats = []
        initial_rates = []
        after_rates = []

        if self.reset_batch or self.reset_tx:
            token_info_copy = deepcopy(self.token_info)

        for middle_elem_input, oracle_price in zip(input_list, oracle_list):
            inner_tx = []
            inner_stats = []

            if self.reset_batch or self.reset_tx:
                self.token_info = token_info_copy
                self.already_executed_txs = []
                token_info_copy = deepcopy(self.token_info)

            for tx in middle_elem_input:
                if tx.is_arb:
                    self.complex_arb()
                else:
                    self.oracle_price = oracle_price
                    probe = InputTx(0, tx.intype, tx.outtype, 1)
                    inital_rate = initial_rates.append(self.swap(probe))
                    output, stat = self.swap(tx, True)
                    after_rate = after_rates.append(self.swap(probe))
                    inner_tx.append(output)
                    inner_stats.append(stat)
                    self.already_executed_txs.append(tx)

                if self.reset_tx:
                    self.token_info = token_info_copy
                    self.already_executed_txs = []
                    token_info_copy = deepcopy(self.token_info)

            txs.append(inner_tx)
            stats.append(inner_stats)

        self.arb_actions = len(self.token_info) / 2
        self.complex_arb()

        return txs, stats, initial_copy, self.token_info, initial_rates, after_rates

    def _update_balance(self, in_type, in_val, out_type, out_val):
        assert((in_type, out_type) in self.token_info.keys() and (
            out_type, in_type) in self.token_info.keys())

        self.token_info[(in_type, out_type)] = (self.token_info[(
            in_type, out_type)][0] + in_val, self.token_info[(in_type, out_type)][1] - out_val)

        self.token_info[(out_type, in_type)] = (self.token_info[(
            out_type, in_type)][0] - out_val, self.token_info[(out_type, in_type)][1] + in_val)

    # Swap one token for another token

    def swap(self, tx, execute=False):
        in_type, in_val, out_type = tx.intype, tx.inval, tx.outtype

        out_price = self._calc_price(in_type, in_val, out_type)
        if not execute:
            return out_price

        out_val = self._calc_delta_out(in_type, in_val, out_type)
        self._update_balance(in_type, in_val, out_type, out_val)

        input_token_pool_inventory_value, output_token_pool_inventory_value = self.token_info[(
            in_type, out_type)]

        oracle_price_ratio = self.oracle_price[out_type] / \
            self.oracle_price[in_type]

        output_tx = OutputTx(index=tx.index,
                             input_token_type=in_type,
                             output_token_type=out_type,
                             input_token_value=in_val,
                             output_token_value=out_val,
                             input_token_pool_initial_value=input_token_pool_inventory_value - in_val,
                             output_token_pool_initial_value=output_token_pool_inventory_value + out_val,
                             input_token_pool_inventory_value=input_token_pool_inventory_value,
                             output_token_pool_inventory_value=output_token_pool_inventory_value,
                             marginal_market_price=out_price,
                             oracle_market_price=oracle_price_ratio,
                             market_maker_type="AMM"
                             )

        output_status = deepcopy(self.token_info)

        return (output_tx, output_status)
