from typing import List
from inputtx import InputTx

class TrafficGeneratorInterface:
    # def load_input(self, traffic: List[List[List[InputTx]]]) -> None:
    #     """ Implementation """
    #     pass

    def generate_traffic(self, **kwargs) -> List[List[InputTx]]:
        """ Implementation """
        raise NotImplementedError
