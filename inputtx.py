from typing import str, float, bool

class InputTx:
    def __init__(self, input_token_type : str, output_token_type : str, input_token_value : float, is_arb : bool = False):
        """
        Represents one transaction to in traffic

        Parameters:
        input_token_type: input token name
        output_token_type: output token name
        input_token_value: amount of input token to be inserted in market maker's liquidity pool
        is_arb: whether or not this transaction is processed or will result in call to arbitrage() in market maker
        """
        self.input_token_type  = input_token_type
        self.output_token_type = output_token_type
        self.input_token_value = input_token_value
        self.is_arb = is_arb

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
