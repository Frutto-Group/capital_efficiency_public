from typing import List, Tuple, float, str
from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from outputtx import OutputTx
from poolstatus import PairwiseTokenPoolStatus

class CSMM(MarketMakerInterface):
    def __init__(self, token_pairs: List[Tuple[str, str]],
    token_amounts: List[Tuple[float, float, float]]):
        """
        Creates a constant sum pairwise liquidity pool market maker

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
    
    def arbitrage(self, lim: float = 1e-8) -> Tuple[None, None]:
        """
        Performs no arbitrage since it is impossible on CSMM
        """
        return [], []

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
        p = self.prices[tx.outtype] / self.prices[tx.intype]
        if out_amt == None:
            if (tx.inval / p > self.token_info[(tx.intype, tx.outtype)][1]):
                out_amt = 0
                tx.inval = 0
            else:
                out_amt = tx.inval / p

        output_tx, pool_stat = super().swap(tx, out_amt)
        output_tx.after_rate = p

        return output_tx, pool_stat
