from price import Price
from typing import List, Tuple

class PoolStatusInterface:
    def get_total_value(self, price: Price):
        raise NotImplementedError


class MultiTokenPoolStatus(PoolStatusInterface, dict):
    def __init__(self, status: dict):
        dict.__init__(self, status)
        for key, value in self.items():
            if not isinstance(key, str) and isinstance(value[0], float):
                raise TypeError(f'Cannot read token amount {value[0]} or token type {key}')
            elif value[0] < 0:
                raise ValueError(f'Cannot accept negative token amount {value[0]} of type {key}')
            elif value[1] <= 0 or value[1] >= 1:
                raise ValueError(f'Cannot accept k value of {value[0]} of type {key}')

    def get_total_value(self, price: Price):
        total_value = 0.
        for key, value in self.items():
            if key not in price:
                raise KeyError(f'Price of {key} not defined')

            total_value += value[0] * price[key]
        
        return total_value


class PairwiseTokenPoolStatus(PoolStatusInterface, dict):
    def __init__(self, token_pairs: List[Tuple[str]], token_amounts: List[Tuple[float]]):
        for (tokenA, tokenB), (amountA, amountB) in zip(token_pairs, token_amounts):
            self[(tokenA, tokenB)] = (amountA, amountB)
            self[(tokenB, tokenA)] = (amountB, amountA)

    def get_total_value(self, price: Price):
        visited = set()
        total_value = 0.
        for (ka, kb), (va, vb) in self.items():
            if (ka, kb) in visited or (kb, ka) in visited:
                continue

            if ka not in price:
                raise KeyError(f'Price of {ka} not defined')
            if kb not in price:
                raise KeyError(f'Price of {kb} not defined')

            visited.add((ka, kb))
            total_value += va * price[ka] + vb * price[kb]
        
        return total_value
    
class PMMPoolStatus(PoolStatusInterface, dict):
    def __init__(self, token_infos: dict):
        for k, v in token_infos.items():
            self[k] = v

    def get_total_value(self, price: Price):
        visited = set()
        total_value = 0.
        for (ka, kb), (va, vb, k) in self.items():
            if (ka, kb) in visited or (kb, ka) in visited:
                continue

            if ka not in price:
                raise KeyError(f'Price of {ka} not defined')
            if kb not in price:
                raise KeyError(f'Price of {kb} not defined')

            visited.add((ka, kb))
            total_value += va * price[ka] + vb * price[kb]

        return total_value
