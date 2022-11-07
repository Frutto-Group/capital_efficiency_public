from typing import List, Dict
from copy import deepcopy
import random
import numpy as np

class RandomPriceMovement():
    def __init__(self, mean: float, stdv: float, change_probability: float, batches: int):
        """
        Generates prices for each batch in the traffic; price percentage changes are normally distributed

        Parameters:
        1. mean: average percent price change between batches
        2. stdv: standard deviation of percent price changes between batches
        3. change_probability: probability of any token's price changing between batches
        4. batches: number of batches in traffic
        """
        self.batches = batches
        self.mean = mean
        self.stdv = stdv
        self.probabilities = [1 - change_probability, change_probability]

    def simulate_ext_prices(self, price_input: Dict[str, float]) -> List[Dict[str, float]]:
        """
        Generates prices for each batch in the traffic; price percentage changes are normally distributed

        Parameters:
        1. price_input: starting price of tokens

        Returns:
        1. prices for each batch of swaps
        """
        prices = [deepcopy(price_input)]
        options = [0, 1]
        even_split = [0.5, 0.5]

        for batch in range(self.batches - 1):
            for k in price_input:
                toChange = random.choices(options, self.probabilities) == [1]
                
                if toChange:
                    change = np.random.normal(self.mean, self.stdv, 1)[0]
                    while change <= 0:
                        change = np.random.normal(self.mean, self.stdv, 1)[0]

                    if random.choices(options, even_split) == [1]:
                        price_input[k] *= (1 + change)
                    else:
                        price_input[k] *= (1 - change)

            prices.append(deepcopy(price_input))

        return prices

class PriceCrash():
    def __init__(self, crash_type: List[str], mean: float, stdv: float, batches: int):
        """
        Generates prices for each batch in the traffic; all token prices stay constant except the crash_types' which crashes

        Parameters:
        1. crash_type: token type(s) that will crash in price
        2. mean: average percent of price decrease of crash_type(s) between batches
        3. stdv: standard deviation of percent of price decrease of crash_type(s) between batches
        4. batches: number of batches in traffic
        """
        self.crash_type = crash_type
        self.mean = mean
        self.stdv = stdv
        self.batches = batches

    def simulate_ext_prices(self, price_input: Dict[str, float]) -> List[Dict[str, float]]:
        """
        Generates prices for each batch in the traffic; all token prices stay constant except the crash_types' which crashes
        
        Parameters:
        1. price_input: starting price of tokens

        Returns:
        1. prices for each batch of swaps
        """
        prices = [deepcopy(price_input)]

        for batch in range(self.batches - 1):
            new_prices = deepcopy(prices[-1])
            for c in self.crash_type:
                change = np.random.normal(self.mean, self.stdv, 1)[0]
                while change <= 0:
                    change = np.random.normal(self.mean, self.stdv, 1)[0]
                new_prices[c] *= (1 - change)

            prices.append(new_prices)

        return prices
