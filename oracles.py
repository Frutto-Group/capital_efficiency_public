from typing import List
from inputtx import InputTx
from price import Price
from copy import deepcopy
import random
import numpy as np

class OracleInterface:
    def simulate_ext_prices(self, traffic: List[List[List[InputTx]]]) -> List[List[Price]]:
        pass

class MultiTokenPriceOracle(OracleInterface):
    """
    Generates price for all batches
    """
    def __init__(self, prices: dict, mean: float, stdv: float, change_probability: float,
                 batches: int) -> None:
        assert 0 <= change_probability and change_probability <= 1
        assert 0 <= stdv and stdv < 1
        assert batches > 0
        self.prices = prices
        self.batches = batches
        self.mean = mean
        self.stdv = stdv
        self.probabilities = [1 - change_probability, change_probability]

    def simulate_ext_prices(self) -> List[Price]:
        prices = [deepcopy(self.prices)]
        options = [0, 1]
        even_split = [0.5, 0.5]

        for batch in range(self.batches - 1):
            for k in self.prices:
                toChange = random.choices(options, self.probabilities) == [1]

                if toChange:
                    change = np.random.normal(self.mean, self.stdv, 1)[0]
                    while change <= 0:
                        change = np.random.normal(self.mean, self.stdv, 1)[0]

                    if random.choices(options, even_split) == [1]:
                        self.prices[k] *= (1 + change)
                    else:
                        self.prices[k] *= (1 - change)

            prices.append(deepcopy(self.prices))

        return prices
