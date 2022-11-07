from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from typing import List, Tuple
from outputtx import OutputTx
from poolstatus import PairwiseTokenPoolStatus

class AMM(MarketMakerInterface):
    def __init__(self, pairwise_pools: List[Tuple[str, str]],
    pairwise_infos: List[Tuple[float, float, float]], single_pools = None, single_infos = None):
        """
        Creates a constant product pairwise liquidity pool market maker

        Parameters:
        1. pairwise_pools: specifies pairwise liquidity pools
        2. pairwise_infos: specifies liquidity pool starting token balances
        3. single_pools: irrelevant (for multi token market makers)
        4. single_infos: irrelevant (for multi token market makers)
        """
        self.token_info = PairwiseTokenPoolStatus(pairwise_pools, pairwise_infos)
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
        1. equilibrium balance for input token
        2. equilibrium balance for output token
        """
        pool = (intype, outtype)
        const = self.token_info[pool][1] * self.token_info[pool][0]
        market_rate = self.prices[pool[1]] / self.prices[pool[0]]
        new_out = (const / market_rate) ** 0.5

        return const / new_out, new_out
