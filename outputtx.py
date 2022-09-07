import numpy as np

AMM = "AMM"
PMM = "PMM"


class OutputTx:
    def __init__(self,
                 index: int,
                 input_token_type: str,
                 output_token_type: str,
                 input_token_value: float,
                 output_token_value: float,
                 input_token_pool_initial_value: float,
                 output_token_pool_initial_value: float,
                 input_token_pool_inventory_value: float,
                 output_token_pool_inventory_value: float,
                 marginal_market_price: float,
                 oracle_market_price: float,
                 market_maker_type: str
                 ) -> None:
        self.index = index
        self.input_token_type = input_token_type
        self.output_token_type = output_token_type
        self.input_token_value = input_token_value
        self.output_token_value = output_token_value
        self.input_token_pool_initial_value = input_token_pool_initial_value
        self.output_token_pool_initial_value = output_token_pool_initial_value
        self.input_token_pool_inventory_value = input_token_pool_inventory_value
        self.output_token_pool_inventory_value = output_token_pool_inventory_value
        self.marginal_market_price = marginal_market_price
        self.oracle_market_price = oracle_market_price
        self.market_maker_type = market_maker_type

    def show(self) -> None:
        print(f'Transaction #{self.index:>7d}: '
              'Input  {self.input_token_type} w/ amount {self.input_token_value:12.6f}, '
              'Output {self.output_token_type} w/amount {self.output_token_value:12.6f}, '
              'Input  {self.input_token_type} w/inital amount in pool  {self.input_token_pool_initial_value:12.6f}, '
              'Output {self.output_token_type} w/inital amount in pool {self.output_token_pool_initial_value:12.6f}, '
              'Input  {self.input_token_type} w/inventory amount in pool  {self.input_token_pool_inventory_value:12.6f}, '
              'Output {self.output_token_type} w/inventory amount in pool {self.output_token_pool_inventory_value:12.6f}, '
              'Marginal Market Price {self.marginal_market_price} and Oracle Market Price{oracle_market_price}')

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

    @property
    def outval(self) -> float:
        return self.output_token_value

    @property
    def inpoolinitval(self) -> float:
        return self.input_token_pool_initial_value

    @property
    def outpoolinvval(self) -> float:
        return self.output_token_pool_initial_value

    @property
    def inpoolinvval(self) -> float:
        return self.input_token_pool_inventory_value

    @property
    def outpoolinitval(self) -> float:
        return self.output_token_pool_inventory_value

    @property
    def mmp(self) -> float:
        return self.marginal_market_price

    @property
    def omp(self) -> float:
        return self.oracle_market_price

    @property
    def mmt(self) -> str:
        return self.market_maker_type


if __name__ == '__main__':
    otx = OutputTx(9, 'A', 'B', 100, 100, 1000, 1000, 500, 500, 1, 1, AMM)
    otx.show()
    print(otx.id,
          otx.inval, otx.intype,
          otx.outtype, otx.outval,
          otx.intype, otx.inpoolinitval,
          otx.outtype, otx.outpoolinitval,
          otx.intype, otx.inpoolinvval,
          otx.outtype, otx.outpoolinvval,
          otx.mmp, otx.omp, otx.mmt)
