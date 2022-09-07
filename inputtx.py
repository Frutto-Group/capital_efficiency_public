import numpy as np

class InputTx:
    def __init__(self, index : int, input_token_type : str, output_token_type : str, input_token_value : float) -> None:
        self.index = index
        self.input_token_type  = input_token_type
        self.output_token_type = output_token_type
        self.input_token_value = input_token_value

    def show(self) -> None:
        print(f'Transaction #{self.index:>7d}: Input {self.input_token_type} w/ amount {self.input_token_value:12.6f}, Outputting {self.output_token_type}')

    @property
    def id(self) -> int:
        return self.index

    @property
    def intype(self) -> str:
        return self.input_token_type

    @property
    def outtype(self) -> str:
        return self.output_token_type

    @property
    def inval(self) -> float:
        return self.input_token_value

    def example():
        raise NotImplementedError
