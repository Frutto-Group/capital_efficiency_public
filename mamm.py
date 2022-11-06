from imarketmaker import MarketMakerInterface
from inputtx import InputTx
from typing import List, Tuple
from outputtx import OutputTx
from poolstatus import MultiTokenPoolStatus

class MAMM(MarketMakerInterface):
    def __init__(self, tokens: List[str], token_infos: List[Tuple[float, float]]):
        """
        Creates a multi token constant product liquidity pool market maker

        Parameters:
        1. tokens: specifies tokens in liquidity pool; of the form:
        ["BTC", "ETH", "USDT"]
        2. token_infos: specifies starting token balances; of the form:
        [[1100, 0], [2000, 0], [1000,0]]
        """
        self.token_info = MultiTokenPoolStatus({tokens[i]: token_infos[i] \
            for i in range(len(tokens))})
        self.equilibriums = None

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
        in_type, in_val, out_type = tx.intype, tx.inval, tx.outtype
        in_balance, out_balance = self.token_info[in_type][0], self.token_info[out_type][0]
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
        const = self.token_info[intype][0] * self.token_info[outtype][0]
        market_rate = self.prices[outtype] / self.prices[intype]
        new_out = (const / market_rate) ** 0.5

        return const / new_out, new_out
