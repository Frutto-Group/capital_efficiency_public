import numpy as np
import random
from typing import List, Tuple, Dict
from inputtx import InputTx

class TrafficGeneratorInterface:
    def generate_traffic(self, prices: List[Dict[str, float]]) -> List[List[InputTx]]:
        """
        Generates traffic

        Parameters:
        1. prices: details token prices at each batch

        Returns:
        1. list of batches of swaps
        """
        raise NotImplementedError
    
class AmountTraverser(TrafficGeneratorInterface):
    def __init__(self, intype: str, outtype: str, amount_lo: float, amount_hi: float, amount_gap: float):
        """
        Generates increasingingly larger swap volumes

        Parameters:
        1. intype: deposit token type
        2. outtype: output token type
        3. amount_lo: starting swap volume
        4. amount_hi: ending swap volume
        5. amount_gap: amount of increment
        """
        self.intype = intype
        self.outtype = outtype
        self.amount_lo = amount_lo
        self.amount_hi = amount_hi
        self.amount_gap = amount_gap

    def generate_traffic(self, prices: List[Dict[str, float]]) -> List[List[InputTx]]:
        """
        Generates increasingingly larger swap volumes

        Parameters:
        1. prices: details token prices at each batch

        Returns:
        1. list of batches of swaps
        """
        return [[InputTx(self.intype, self.outtype, amount) for amount in \
            np.arange(self.amount_lo, self.amount_hi, self.amount_gap)]]

class NormallyDistributed(TrafficGeneratorInterface):
    def __init__(self, sigma: float, mean: float, arb_probability: float,
    shape: Tuple[int], max_price: float = None):
        """
        Generates swaps between all possible token types with normally distributed swap volumes

        Parameters:
        1. sigma: standard deviation of swap amount (in dollars)
        2. mean: mean of swap amount (in dollars)
        3. arb_probability: probability any swap should be for arbitrage
        4. shape: output shape of traffic
        5. max_price: upper bound on how much (in dollars) a swap can be
        """
        self.sigma = sigma
        self.mean = mean
        self.arb_probability = [1 - arb_probability, arb_probability]
        self.batches = shape[0]
        self.batch_size = shape[1]
        self.max_price = max_price
    
    def generate_traffic(self, prices: List[Dict[str, float]]) -> List[List[InputTx]]:
        """
        Generates swaps between all possible token types with normally distributed swap volumes

        Parameters:
        1. prices: details token prices at each batch

        Returns:
        1. list of batches of swaps
        """
        txs = []
        index = 0
        choices = [0, 1]
        tokens = list(prices[0].keys())

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = np.random.normal(self.mean, self.sigma, self.batch_size)
                
                for e in s:
                    tok1 = random.choice(tokens)
                    tok2 = random.choice(tokens)
                    while tok2 == tok1:
                        tok2 = random.choice(tokens)
                    
                    is_arb = random.choices(choices, self.arb_probability) == [1]

                    e = min(self.max_price, e)
                    if e > 0:
                        batch_txs.append(InputTx(tok1, tok2, \
                            e / prices[len(batch_txs)][tok1], is_arb))
                        index += 1
                    elif e < 0:
                        batch_txs.append(InputTx(tok1, tok2, \
                            (2 * self.mean - e) / prices[len(batch_txs)][tok1], is_arb))
                        index += 1

            txs.append(batch_txs[:self.batch_size])

        return txs

class RandomlyDistributed(TrafficGeneratorInterface):
    def __init__(self, arb_probability: float, shape: Tuple[int], max_price: float = None):
        """
        Generates swaps between all possible token types with randomly distributed swap volumes

        Parameters:
        1. arb_probability: probability any swap should be for arbitrage
        2. shape: output shape of traffic
        3. max_price: upper bound on how much (in dollars) a swap can be
        """
        self.arb_probability = [1 - arb_probability, arb_probability]
        self.batches = shape[0]
        self.batch_size = shape[1]
        self.max_price = max_price
    
    def generate_traffic(self, prices: List[Dict[str, float]]) -> List[List[InputTx]]:
        """
        Generates swaps between all possible token types with randomly distributed swap volumes

        Parameters:
        1. prices: details token prices at each batch

        Returns:
        1. list of batches of swaps
        """
        txs = []
        index = 0
        choices = [0, 1]
        tokens = list(prices[0].keys())

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = []
                for s in range(self.batch_size):
                    s.append(random.randrange(0, 100 * (self.max_price + 1)) / 100)
                
                for e in s:
                    tok1 = random.choice(tokens)
                    tok2 = random.choice(tokens)
                    while tok2 == tok1:
                        tok2 = random.choice(tokens)
                    
                    is_arb = random.choices(choices, self.arb_probability) == [1]

                    if e > 0:
                        batch_txs.append(InputTx(tok1, tok2, \
                            e / prices[len(batch_txs)][tok1], is_arb))
                        index += 1
                    elif e < 0:
                        batch_txs.append(InputTx(tok1, tok2, \
                            (2 * self.mean - e) / prices[len(batch_txs)][tok1], is_arb))
                        index += 1

            txs.append(batch_txs[:self.batch_size])

        return txs

class SellOff(TrafficGeneratorInterface):
    def __init__(self, sell_type: List[str], arb_probability: float,
    shape: Tuple[int], max_price: float = None):
        """
        Generates swaps where only 1 token type is added to pools

        Parameters:
        1. sell_type: the token(s) that is/are always added to pools
        2. arb_probability: probability any swap should be for arbitrage
        3. shape: output shape of traffic
        4. max_price: upper bound on how much (in dollars) a swap can be
        """
        self.sell_type = sell_type
        self.arb_probability = [1 - arb_probability, arb_probability]
        self.batches = shape[0]
        self.batch_size = shape[1]
        self.max_price = max_price
    
    def generate_traffic(self, prices: List[Dict[str, float]]) -> List[List[InputTx]]:
        """
        Generates swaps where only 1 token type is added to pools

        Parameters:
        1. prices: details token prices at each batch

        Returns:
        1. list of batches of swaps
        """
        txs = []
        index = 0
        choices = [0, 1]
        tokens = list(prices[0].keys())

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = []
                for i in range(self.batch_size):
                    s.append(random.randrange(0, 100 * (self.max_price + 1)) / 100)
                
                for e in s:
                    tok2 = random.choice(tokens)
                    while tok2 in self.sell_type:
                        tok2 = random.choice(tokens)
                    
                    is_arb = random.choices(choices, self.arb_probability) == [1]

                    intype = random.choice(self.sell_type)
                    if e > 0:
                        batch_txs.append(InputTx(intype, tok2, \
                            e / prices[len(batch_txs)][intype], is_arb))
                        index += 1
                    elif e < 0:
                        batch_txs.append(InputTx(intype, tok2, \
                            (2 * self.mean - e) / prices[len(batch_txs)][intype], is_arb))
                        index += 1

            txs.append(batch_txs[:self.batch_size])

        return txs
