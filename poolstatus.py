from typing import List, Dict, Tuple, float
from price import Price

class PoolStatusInterface:
    def get_total_value(self, price: Price) -> float:
        """
        Get the value (in dollars) of the pool

        Parameters:
        price: token prices
        """
        raise NotImplementedError


class MultiTokenPoolStatus(PoolStatusInterface):
    def __init__(self, status: Dict[str, Tuple[float, float]]):
        """
        Represents pool status for multi token liquidity pool market makers

        Parameters:
        status: dictionary indicating tokens' counts and k values; of the form:
        {
            "Token a": [100, 0.5]
        }
        """
        dict.__init__(self, status)

    def get_total_value(self, price: Price) -> float:
        """
        Get the value (in dollars) of the pool

        Parameters:
        price: token prices
        """
        total_value = 0.
        for key, value in self.items():
            total_value += value[0] * price[key]
        
        return total_value


class PairwiseTokenPoolStatus(PoolStatusInterface, dict):
    def __init__(self, token_pairs: List[Tuple[str, str]],
    token_infos: List[Tuple[float, float, float]]):
        """
        Represents pool status for 2 token liquidity pool market makers

        Parameters:
        token_pairs: tuples of trading pairs, i.e "['BTC. 'ETH']"; should not 
        have redundant pairs; of the form:
        [
        ["BTC", "ETH"],
        ["ETH", "BTC"],
        ["BTC", "USDT"],
        ["USDT", "BTC"],
        ]
        token_infos: token counts and k values for each trading pair; of the form:
        [
        [1100, 500, 0],
        [500, 1100, 0],
        [200, 500, 0],
        [500, 200, 0],
        ]
        """
        for (tokenA, tokenB), (amountA, amountB, k) in zip(token_pairs, token_infos):
            self[(tokenA, tokenB)] = [amountA, amountB, k]
            self[(tokenB, tokenA)] = [amountB, amountA, k]

    def get_total_value(self, price: Price) -> float:
        """
        Get the value (in dollars) of the pool

        Parameters:
        price: token prices
        """
        visited = set()
        total_value = 0.
        for (ka, kb), (va, vb) in self.items():
            if (ka, kb) in visited or (kb, ka) in visited:
                continue

            visited.add((ka, kb))
            total_value += va * price[ka] + vb * price[kb]
        
        return total_value
