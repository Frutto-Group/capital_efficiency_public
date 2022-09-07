from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from typing import List, Tuple
from outputtx import OutputTx
from poolstatus import MultiTokenPoolStatus, PoolStatusInterface
from price import Price
from copy import deepcopy
import math


class MAMM(MarketMakerInterface):
    def __init__(self, tokens: List[str], token_info: List[float], reset_batch: str = "False",
                 reset_tx: str = "False", arb: str = "True"):
        """
        tokens of the form: ["BTC", "ETH", "USDT"]

        token_info of the form: [[1100, 0], [2000, 0], [1000, 0]]

        reset_batch: True if reset AMM to initial state after every batch

        reset_tx: True if reset AMM to initial state after every InputTx

        arb: True if need to perform arbitrage
        """
        self.balances = {tokens[i]: token_info[i][0] for i in range(len(tokens))}
        self.const = 1
        for tup in token_info:
          self.const *= tup[0]

        self.reset_batch = reset_batch == "True"
        self.reset_tx = reset_tx == "True"
        self.arb = arb == "True"

    def _calc_price(self, in_type: str, in_value: float, out_type: str) -> float:
        in_balance, out_balance = self.balances[in_type], self.balances[out_type]
        return (in_balance + in_value)/out_balance

    # equalizes all pairs to market price
    def arbitrage(self):
        num_tokens = len(self.balances)

        for token2 in self.balances.keys():
            cur_token_price = self.oracle_price[token2]
            cur_mult = 1
            for token3 in self.balances.keys():
                if token3 != token2:
                    cur_mult /= cur_token_price
                    cur_mult *= self.oracle_price[token3]
            self.balances[token2] = math.pow(cur_mult * self.const, (1 / num_tokens))

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Price]
                         ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]], PoolStatusInterface, PoolStatusInterface, List[float], List[float]]:
        txs, stats, initial_status, final_status, initial_rates, after_rates = self._multiple_swaps(traffic, external_price)
        return txs, stats, initial_status, final_status, initial_rates, after_rates

    def _calc_delta_out(self, in_type: str, in_value: float, out_type: str) -> float:
        in_balance, out_balance = self.balances[in_type], self.balances[out_type]
        return (out_balance*in_value)/(in_balance + in_value)

    def configure_arbitrage(self, arb_period: int, arb_actions: int):
        assert arb_period > 0
        self.arb_period = arb_period

    def _multiple_swaps(self, input_list, oracle_list):
        self.oracle_price = oracle_list[0]
        self.arbitrage()

        pool_dict = {}
        for t in self.balances:
            pool_dict[t] = (self.balances[t], 0.5)
        initial_copy = MultiTokenPoolStatus(deepcopy(pool_dict))

        txs = []
        stats = []
        initial_rates = []
        after_rates = []

        if self.reset_batch or self.reset_tx:
            balance_copy = deepcopy(self.balances)

        for middle_elem_input, oracle_price in zip(input_list, oracle_list):
            inner_tx = []
            inner_stats = []

            if self.reset_batch or self.reset_tx:
                self.balances = balance_copy
                balance_copy = deepcopy(self.balances)

            for i, tx in enumerate(middle_elem_input):
                self.oracle_price = oracle_price
                probe = InputTx(0, tx.intype, tx.outtype, 1)
                initial_rates.append(self.swap(probe))
                output, stat = self.swap(tx, True)
                after_rates.append(self.swap(probe))
                inner_tx.append(output)
                inner_stats.append(stat)

                if self.arb and tx.index != 0 and tx.index % self.arb_period == 0:
                    self.arbitrage()

                if self.reset_tx:
                    self.balances = balance_copy
                    balance_copy = deepcopy(self.balances)

            txs.append(inner_tx)
            stats.append(inner_stats)

        self.arbitrage()
        for t in self.balances:
            pool_dict[t] = (self.balances[t], 0.5)

        return txs, stats, initial_copy, MultiTokenPoolStatus(pool_dict), initial_rates, after_rates

    def _update_balance(self, in_type, in_val, out_type, out_val):
        self.balances[in_type] += in_val
        self.balances[out_type] -= out_val

    # Swap one token for another token

    def swap(self, tx, execute=False):
        in_type, in_val, out_type = tx.intype, tx.inval, tx.outtype

        out_price = self._calc_price(in_type, in_val, out_type)
        if not execute:
            return out_price

        out_val = self._calc_delta_out(in_type, in_val, out_type)
        self._update_balance(in_type, in_val, out_type, out_val)

        input_token_pool_inventory_value, output_token_pool_inventory_value = self.balances[in_type], self.balances[out_type]

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
                             market_maker_type=MAMM
                             )

        pool_dict= {}
        for t in self.balances:
            pool_dict[t] = (self.balances[t], 0.5)
        output_status = MultiTokenPoolStatus(pool_dict)

        return (output_tx, output_status)
