class Price(dict):
    def __init__(self, price:dict = {}, **kwargs) -> None:
        super(self).__init__(price)
        self.update(**kwargs)

        for key, value in self.items():
            if not isinstance(key, str) and isinstance(value, float):
                raise TypeError(f'Cannot read price {value} or token type {key}')
            elif value < 0:
                raise ValueError(f'Cannot accept negative price {value} of type {key}')

        