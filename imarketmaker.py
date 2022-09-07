from typing import List, Tuple
from inputtx import InputTx
from outputtx import OutputTx
from price import Price
from poolstatus import PoolStatusInterface


class MarketMakerInterface:
    def configure_arbitrage(self, arb_period: int, arb_actions: int):
        """
        arb_period: between how many consecutive transactions before arbitrage() is called

        arb_actions: how many pools are allowed to be arbed
        """
        raise NotImplementedError

    def swap(self, tx: InputTx, execute: bool = False):
        """
        Initiate a swap specified by tx

        execute: whether or not to execute the swap
        """
        raise NotImplementedError

    def simulate_traffic(self,
                         traffic: List[List[InputTx]],
                         external_price: List[Price]
    ) -> Tuple[List[List[OutputTx]], List[List[PoolStatusInterface]], PoolStatusInterface, PoolStatusInterface]:
        """
        Given a traffic and price data, simulate swaps
        """
        raise NotImplementedError
