from itrafficgen import TrafficGeneratorInterface
from price import Price
from inputtx import InputTx
from typing import List

import numpy as np
import random


class AmountTraverser(TrafficGeneratorInterface):
    def __init__(self, intype: str, outtype: str, amount_lo: float, amount_hi: float, amount_gap: float) -> None:
        self.intype = intype
        self.outtype = outtype
        self.amount_lo = amount_lo
        self.amount_hi = amount_hi
        self.amount_gap = amount_gap

    def generate_traffic(self) -> List[List[InputTx]]:
        return [[InputTx(index, self.intype, self.outtype, amount) for index, amount in enumerate(np.arange(self.amount_lo, self.amount_hi, self.amount_gap))]]


class SimpleGaussianTwoTokenTrafficGen(TrafficGeneratorInterface):
    def __init__(self, intype: str, outtype: str, mu: float, sigma: float, size: int) -> None:
        self.intype = intype
        self.outtype = outtype
        self.mu = mu
        self.sigma = sigma
        self.size = size

    def generate_traffic(self) -> List[List[List[InputTx]]]:
        s = np.random.normal(self.mu, self.sigma, self.size)
        itxss = []
        index = 0
        for e in s:
            if (e > 0):
                itx = InputTx(index, self.intype, self.outtype, e)
            else:
                itx = InputTx(index, self.outtype, self.intype, -e)

            index += 1
            itxs = [[itx]]
            itxss.append(itxs)
        return itxss


class RandomTokenPair(TrafficGeneratorInterface):
    def __init__(self, tokens: List[str], sigma: float, mean: float, batches: int,
                 batch_size: int) -> None:
        """
        Generates swaps between all possible token types
        """
        assert len(tokens) >= 2
        self.tokens = tokens
        self.batches = batches
        self.batch_size = batch_size
        self.sigma = sigma
        self.mean = mean

    def generate_traffic(self) -> List[List[InputTx]]:
        txs = []
        index = 0

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = np.random.normal(self.mean, self.sigma, self.batch_size)
                for e in s:
                    tok1 = random.choice(self.tokens)
                    tok2 = random.choice(self.tokens)
                    while tok2 == tok1:
                        tok2 = random.choice(self.tokens)

                    if e > 0:
                        batch_txs.append(InputTx(index, tok1, tok2, e))
                        index += 1
                    elif e < 0:
                        batch_txs.append(InputTx(index, tok1, tok2, 2 * self.mean - e))
                        index += 1

            txs.append(batch_txs[:self.batch_size])

        return txs

class PriceBased(TrafficGeneratorInterface):
    def __init__(self, tokens: List[str], sigma: float, mean: float,
                 batches: int, batch_size: int) -> None:
        """
        Generates swaps between all possible token types
        """
        assert len(tokens) >= 2
        assert sigma > 0 and mean > 0 and batches > 0 and batch_size > 0
        self.tokens = tokens
        self.prices = None
        self.batches = batches
        self.batch_size = batch_size
        self.sigma = sigma
        self.mean = mean

    def generate_traffic(self, prices: List[Price]) -> List[List[InputTx]]:
        assert len(prices) == self.batches
        self.prices = prices
        txs = []
        index = 0

        while len(txs) != self.batches:
            batch_txs = []

            while len(batch_txs) != self.batch_size:
                s = np.random.normal(self.mean, self.sigma, self.batch_size)
                for e in s:
                    tok1 = random.choice(self.tokens)
                    tok2 = random.choice(self.tokens)
                    while tok2 == tok1:
                        tok2 = random.choice(self.tokens)

                    if e > 0:
                        batch_txs.append(InputTx(index, tok1, tok2, e / self.prices[len(batch_txs)][tok1]))
                        index += 1
                    elif e < 0:
                        batch_txs.append(InputTx(index, tok1, tok2, (2 * self.mean - e) / self.prices[len(batch_txs)][tok1]))
                        index += 1

            txs.append(batch_txs[:self.batch_size])

        return txs
