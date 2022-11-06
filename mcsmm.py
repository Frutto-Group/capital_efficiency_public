from typing import List, Tuple
from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from outputtx import OutputTx
from poolstatus import MultiTokenPoolStatus

class MCSMM(MarketMakerInterface):
    def __init__(self, tokens: List[str], token_infos: List[Tuple[float, float]]):
        """
        Creates a multi token constant sum liquidity pool market maker

        Parameters:
        1. tokens: specifies tokens in liquidity pool; of the form:
        ["BTC", "ETH", "USDT"]
        2. token_infos: specifies starting token balances; of the form:
        [[1100, 0], [2000, 0], [1000,0]]
        """
        self.token_info = MultiTokenPoolStatus({tokens[i]: token_infos[i] \
            for i in range(len(tokens))})
        self.equilibriums = None

    def arbitrage(self, lim: float = 1e-8) -> Tuple[None, None]:
        """
        Performs no arbitrage since it is impossible on MCSMM
        """
        return [], []

    def swap(self, tx: InputTx, out_amt: float = None) -> Tuple[OutputTx, MultiTokenPoolStatus]:
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
            if (tx.inval / p > self.token_info[tx.outtype][0]):
                out_amt = 0
                tx.inval = 0
            else:
                out_amt = tx.inval / p

        output_tx, pool_stat = super().swap(tx, out_amt)
        output_tx.after_rate = p

        return output_tx, pool_stat
