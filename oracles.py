from typing import List, Dict
from inputtx import InputTx
from price import Price
from copy import deepcopy
import random
import numpy as np

class RandomPriceMovement():
    def __init__(self, prices: Dict, mean: float, stdv: float, change_probability: float, batches: int):
        """
        Generates prices for each batch in the traffic; price percentage changes are normally distributed

        Parameters:
        prices: initial token prices; of the form:
        {
            "Token 1": 100,
            "Token 2": 50
        }
        mean: average percent price change between batches
        stdv: standard deviation of percent price changes between batches
        change_probability: probability of any token's price changing between batches
        batches: number of batches in traffic
        """        
        self.prices = prices
        self.batches = batches
        self.mean = mean
        self.stdv = stdv
        self.probabilities = [1 - change_probability, change_probability]

    def simulate_ext_prices(self) -> List[Price]:
        """
        Generates prices for each batch in the traffic; price percentage changes are normally distributed
        """
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

class PriceCrash():
    def __init__(self, prices: Dict, crash_type: str, mean: float, stdv: float, batches: int):
        """
        Generates prices for each batch in the traffic; all token prices stay constant except crash_type's which crashes

        Parameters:
        prices: initial token prices; of the form:
        {
            "Token 1": 100,
            "Token 2": 50
        }
        crash_type: token type that will crash in price
        mean: average percent of price decrease of crash_type between batches
        stdv: standard deviation of percent of price decrease of crash_type between batches
        batches: number of batches in traffic
        """
        self.prices = prices
        self.crash_type = crash_type
        self.mean = mean
        self.stdv = stdv
        self.batches = batches

    def simulate_ext_prices(self) -> List[Price]:
        """
        Generates prices for each batch in the traffic; all token prices stay constant except crash_type's which crashes
        """
        prices = [deepcopy(self.prices)]

        for batch in range(self.batches - 1):
            change = np.random.normal(self.mean, self.stdv, 1)[0]
            while change <= 0:
                change = np.random.normal(self.mean, self.stdv, 1)[0]
            self.prices[self.crash_type] *= (1 - change)

            prices.append(deepcopy(self.prices))

        return prices
