from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from typing import List, Tuple, str, float
from outputtx import OutputTx
from poolstatus import PairwiseTokenPoolStatus

class AMM(MarketMakerInterface):
    def __init__(self, token_pairs: List[Tuple[str, str]],
    token_amounts: List[Tuple[float, float, float]]):
        """
        Creates a constant product pairwise liquidity pool market maker

        Parameters:
        1. token_pairs: specifies pairwise liquidity pools; of the form:
        [["BTC", "ETH"],
         ["ETH", "BTC"],
         ["BTC", "USDT"],
         ["USDT", "BTC"]]
        2. token_info: specifies liquidity pool starting token balances; of the form:
        [[1100, 500, 0],
         [500, 1100, 0],
         [200, 500, 0],
         [500, 200, 0]]
        """
        self.token_info = PairwiseTokenPoolStatus(token_pairs, token_amounts)
        self.equilibriums = None

    def swap(self, tx: InputTx, out_amt: float = None) -> Tuple[OutputTx, PairwiseTokenPoolStatus]:
        """
        Initiate a swap specified by tx

        Parameters:
        1. tx: transaction
        2. out_amt: specifies the amount of output token removed

        Returns:
        1. output information associated with swap (after_rate is incorrect)
        2. status of pool ater swap
        """
        if out_amt == None:
            in_type, in_val, out_type = tx.intype, tx.inval, tx.outtype
            in_balance, out_balance, k = self.token_info[(in_type, out_type)]
            const = in_balance * out_balance
            out_amt = const*(1/in_balance - (1/(in_balance + in_val)))
        
        output_tx, pool_stat = super().swap(tx, out_amt)
        output_tx.after_rate = in_val / \
                (const*(1/(in_balance + in_val) - (1/(in_balance + 2*in_val))))
        
        return output_tx, pool_stat
    
    def calculate_equilibriums(self, intype: str, outtype: str) -> Tuple[float, float]:
        """
        Calculates and returns equilibrium balances

        Parameters:
        1. intype: input token type
        2. outtype: output token type

        Returns:
        1. Equilibrium balance for input token
        2. Equilibrium balance for output token
        """
        pool = (intype, outtype)
        const = self.token_info[pool][1] * self.token_info[pool][0]
        market_rate = self.external_price[pool[1]] / self.external_price[pool[0]]
        new_out = (const / market_rate) ** 0.5

        return const / new_out, new_out
