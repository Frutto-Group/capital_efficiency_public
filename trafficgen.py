import numpy as np
import random
from typing import List, Tuple, Dict
from inputtx import InputTx

class TrafficGenerator():
    def __init__(self, sigma: float, mean: float, arb_probability: float, shape: Tuple[int, int],
    max_price: float, is_norm: str = "True"):
        """
        Generates traffic

        Parameters:
        1. sigma: standard deviation of swap amount (in dollars)
        2. mean: mean of swap amount (in dollars)
        3. arb_probability: probability any swap should be for arbitrage
        4. shape: output shape of traffic
        5. max_price: upper bound on how much (in dollars) a swap can be
        6. is_norm: whether or not swap amounts should be normally distributed
        """
        self.mean = mean
        self.sigma = sigma
        self.arb_probability = [1 - arb_probability, arb_probability]
        self.batches = shape[0]
        self.batch_size = shape[1]
        self.max_price = max_price
        self.is_norm = is_norm == "True"
        self.token_list = None
        self.token_info = None
        self.intype_probabilities = []
        self.outtype_probabilities = []
        
    
    def configure_tokens(self, token_list: List[str], token_info: Dict[str, Dict[str, float]]):
        """
        Configures parameters related to tokens

        Parameters:
        1. token_list: list of tokens
        2. token_info: contains token data for if non default values should be
        used; of the form:
        {
            "LUNA": {
                    "intype_percent": 0.45,
                    "outtype_percent": 0.05,
                    "amt_mean": 10000,
                    "amt_stdv": 2000,
                    "amt_max": 20000
                },
            "UST": {
                    "intype_percent": 0.5,
                    "outtype_percent": 0.05,
                    "amt_mean": 15000,
                    "amt_stdv": 2000,
                    "amt_max": 20000
                }
        }
        """
        self.token_list = token_list
        self.token_info = token_info
        tokens = len(token_list)
        self.intype_probabilities = [0] * tokens
        self.outtype_probabilities = [0] * tokens
        
        custom_ins, custom_outs = 0, 0
        for i, tok in enumerate(token_list):
            if tok in token_info:
                info = token_info[tok]
                if "intype_percent" in info:
                    self.intype_probabilities[i] = info["intype_percent"]
                    custom_ins += 1
                if "outtype_percent" in info:
                    self.outtype_probabilities[i] = info["outtype_percent"]
                    custom_outs += 1
        
        remainder = tokens - custom_ins
        if remainder:
            avg = (1 - sum(self.intype_probabilities)) / remainder
            for i, percent in enumerate(self.intype_probabilities):
                if not percent:
                    self.intype_probabilities[i] = avg
        
        remainder = tokens - custom_outs
        if remainder:
            avg = (1 - sum(self.outtype_probabilities)) / remainder
            for i, percent in enumerate(self.outtype_probabilities):
                if not percent:
                    self.outtype_probabilities[i] = avg

    def __get_amt(self, intype: str, price: float) -> float:
        """
        Given the token price, generates a swap amount

        Parameters:
        1. intype: deposit token type
        2. price: token price

        Returns:
        1. token swap amount
        """
        sigma = self.sigma
        mean = self.mean
        max_price = self.max_price
        if intype in self.token_info:
            info = self.token_info[intype]
            if "amt_stdv" in info:
                sigma = info["amt_stdv"]
            if "amt_mean" in info:
                mean = info["mean"]
            if "amt_max" in info:
                max_price = info["amt_max"]
        
        if self.is_norm:
            deviation = np.random.normal(0, sigma)
            while deviation <= -1 * mean:
                deviation = np.random.normal(0, sigma)
            
            return min((deviation + mean), max_price) / price
        else:

            return random.randrange(0, max_price * 1000) / (1000 * price)
    
    def __get_pair(self) -> Tuple[str, str]:
        """
        Randomly picks 2 tokens to swap between

        Returns:
        1. input token type
        2. output token type
        """
        intype = random.choices(self.token_list, weights=self.intype_probabilities, k=1)[0]
        outtype = random.choices(self.token_list, weights=self.outtype_probabilities, k=1)[0]
        while outtype == intype:
            outtype = random.choices(self.token_list, weights=self.outtype_probabilities, k=1)[0]
        
        return intype, outtype

    def generate_traffic(self, prices: List[Dict[str, float]]) -> List[List[InputTx]]:
        """
        Generates traffic

        Parameters:
        1. prices: details token prices at each batch; of the form:
        {
            "BTC": 23004,
            "UST": 1
        }

        Returns:
        1. list of batches of swaps
        """
        txs = []
        choices = [0,1]
        for batch in range(self.batches):
            batch_txs = []
            for tx in range(self.batch_size):
                intype, outtype = self.__get_pair()
                amt = self.__get_amt(intype, prices[batch][intype])
                arb = random.choices(choices, self.arb_probability) == [1]
                batch_txs.append(InputTx(intype, outtype, amt, arb))
            
            txs.append(batch_txs)
        
        return txs