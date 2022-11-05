import numpy as np
import random
from typing import List, Tuple, str, float
from inputtx import InputTx
from price import Price

class TrafficGeneratorInterface:
    def generate_traffic(self, prices: List[Price]) -> List[List[InputTx]]:
        """
        Generates traffic

        Parameters:
        prices: details token prices at each batch
        """
        raise NotImplementedError
    
class AmountTraverser(TrafficGeneratorInterface):
    def __init__(self, intype: str, outtype: str, amount_lo: float, amount_hi: float, amount_gap: float):
        """
        Generates increasingingly larger swap volumes

        Parameters:
        intype: deposit token type
        outtype: output token type
        amount_lo: starting swap volume
        amount_hi: ending swap volume
        amount_gap: amount of increment
        """
        self.intype = intype
        self.outtype = outtype
        self.amount_lo = amount_lo
        self.amount_hi = amount_hi
        self.amount_gap = amount_gap

    def generate_traffic(self, prices: List[Price]) -> List[List[InputTx]]:
        """
        Generates increasingingly larger swap volumes

        Parameters:
        prices: details token prices at each batch
        """
        return [[InputTx(self.intype, self.outtype, amount) for amount in \
            np.arange(self.amount_lo, self.amount_hi, self.amount_gap)]]

class NormallyDistributed(TrafficGeneratorInterface):
    def __init__(self, tokens: List[str], sigma: float, mean: float, arb_probability: float,
    shape: Tuple[int], max_price: float = None):
        """
        Generates swaps between all possible token types with normally distributed swap volumes

        Parameters:
        tokens: list of token types
        sigma: standard deviation of swap amount (in dollars)
        mean: mean of swap amount (in dollars)
        arb_probability: probability any swap should be for arbitrage
        shape: output shape of traffic
        max_price: upper bound on how much (in dollars) a swap can be
        """
        self.tokens = tokens
        self.sigma = sigma
        self.mean = mean
        self.arb_probability = [1 - arb_probability, arb_probability]
        self.batches = shape[0]
        self.batch_size = shape[1]
        self.max_price = max_price
    
    def generate_traffic(self, prices: List[Price]) -> List[List[InputTx]]:
        """
        Generates swaps between all possible token types with normally distributed swap volumes

        Parameters:
        prices: details token prices at each batch
        """
        txs = []
        index = 0
        choices = [0, 1]

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = np.random.normal(self.mean, self.sigma, self.batch_size)
                
                for e in s:
                    tok1 = random.choice(self.tokens)
                    tok2 = random.choice(self.tokens)
                    while tok2 == tok1:
                        tok2 = random.choice(self.tokens)
                    
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
    def __init__(self, tokens: List[str], arb_probability: float, shape: Tuple[int],
    max_price: float = None):
        """
        Generates swaps between all possible token types with randomly distributed swap volumes

        Parameters:
        tokens: list of token types
        arb_probability: probability any swap should be for arbitrage
        shape: output shape of traffic
        max_price: upper bound on how much (in dollars) a swap can be
        """
        self.tokens = tokens
        self.arb_probability = [1 - arb_probability, arb_probability]
        self.batches = shape[0]
        self.batch_size = shape[1]
        self.max_price = max_price
    
    def generate_traffic(self, prices: List[Price]) -> List[List[InputTx]]:
        """
        Generates swaps between all possible token types with randomly distributed swap volumes

        Parameters:
        prices: details token prices at each batch
        """
        txs = []
        index = 0
        choices = [0, 1]

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = []
                for s in range(self.batch_size):
                    s.append(random.randrange(0, 100 * (self.max_price + 1)) / 100)
                
                for e in s:
                    tok1 = random.choice(self.tokens)
                    tok2 = random.choice(self.tokens)
                    while tok2 == tok1:
                        tok2 = random.choice(self.tokens)
                    
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
    def __init__(self, tokens: List[str], sell_type: str, arb_probability: float,
    shape: Tuple[int], max_price: float = None):
        """
        Generates swaps where only 1 token type is added to pools

        Parameters:
        tokens: list of token types
        sell_type: the token that is always added to pools
        arb_probability: probability any swap should be for arbitrage
        shape: output shape of traffic
        max_price: upper bound on how much (in dollars) a swap can be
        """
        self.tokens = tokens
        self.sell_type = sell_type
        self.arb_probability = [1 - arb_probability, arb_probability]
        self.batches = shape[0]
        self.batch_size = shape[1]
        self.max_price = max_price
    
    def generate_traffic(self, prices: List[Price]) -> List[List[InputTx]]:
        """
        Generates swaps where only 1 token type is added to pools

        Parameters:
        prices: details token prices at each batch
        """
        txs = []
        index = 0
        choices = [0, 1]

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = []
                for s in range(self.batch_size):
                    s.append(random.randrange(0, 100 * (self.max_price + 1)) / 100)
                
                for e in s:
                    tok2 = random.choice(self.tokens)
                    while tok2 == self.sell_type:
                        tok2 = random.choice(self.tokens)
                    
                    is_arb = random.choices(choices, self.arb_probability) == [1]

                    if e > 0:
                        batch_txs.append(InputTx(self.sell_type, tok2, \
                            e / prices[len(batch_txs)][self.sell_type,], is_arb))
                        index += 1
                    elif e < 0:
                        batch_txs.append(InputTx(self.sell_type, tok2, \
                            (2 * self.mean - e) / prices[len(batch_txs)][self.sell_type,], is_arb))
                        index += 1

            txs.append(batch_txs[:self.batch_size])

        return txs
