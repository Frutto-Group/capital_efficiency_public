from typing import List, Dict, Tuple
import random
from copy import deepcopy

class BalanceInitializer():
    def __init__(self, token_infos: Dict[str, float], constant: float, k: float, random_k: str = "False"):
        """
        Calculates a fair starting balance for all market makers (all token pools
        start at an equilibrium point)

        Parameters:
        1. token_infos: initial token prices
        2. constant: "size" each token balance should be
        3. k: k value for each pool
        4. random_k: whether or not to use random k for each pool
        """
        self.token_infos = token_infos
        self.constant = constant ** len(token_infos)
        self.k = k
        self.random_k = random_k == "True"

    def getBalances(self
    ) -> Tuple[List[Tuple[str, str]], List[Tuple[float, float, float]],
        List[str], List[Tuple[float, float]], Dict[str, float]]:
        """
        Balance and initialization information for market makers

        Returns:
        1. list of pairwise token pools
        2. balance and k values for pairwise token pools
        3. list of tokens
        4. balance and k values for single tokens
        5. token prices
        """
        token_info_copy = deepcopy(self.token_infos)
        tokens = list(self.token_infos.keys())
        base = tokens[0]
        num_tokens = len(self.token_infos)
        respective_prices = {}
        
        for i in self.token_infos:
            if i != base:
                price = self.token_infos[i] / self.token_infos[base]
                respective_prices[i] = price
                self.constant *= price
        self.constant = self.constant ** (1/num_tokens)

        for i in respective_prices:
            self.token_infos[i] = self.constant / respective_prices[i]
        self.token_infos[base] = self.constant

        num_pools = num_tokens / 2
        pairwise_pools = []
        pairwise_infos = []
        single_pools = list(self.token_infos.keys())
        single_infos = [[i] for i in self.token_infos.values()]
        token_k = {}
        
        for i, tok1 in enumerate(tokens):
            for tok2 in tokens[i:]:
                pool = [tok1, tok2]
                reverse_pool = [tok2, tok1]
                pairwise_pools.append(pool)
                pairwise_pools.append(reverse_pool)
                
                pool_balances = [self.token_infos[tok1] / num_pools, self.token_infos[tok2] / num_pools]
                reverse_pool_balances = [pool_balances[1], pool_balances[0]]
                pairwise_infos.append(pool_balances)
                pairwise_infos.append(reverse_pool_balances)

                if self.random_k:
                    token_k[tok1] = random.randrange(1, 1000) / 1000
                    token_k[tok2] = random.randrange(1, 1000) / 1000
                else:
                    token_k[tok1] = self.k
                    token_k[tok2] = self.k
        
        for i, pool in enumerate(pairwise_pools):
            pairwise_infos[i].append((token_k[pool[0]] + token_k[pool[1]]) / 2)
        
        for i, tok in enumerate(single_pools):
            single_infos[i].append(token_k[tok])
        
        return pairwise_pools, pairwise_infos, single_pools, single_infos, token_info_copy