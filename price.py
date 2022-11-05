class Price(dict):
    def __init__(self, price: dict = {}, **kwargs):
        """
        Dictionary like object indicating token prices for 1 batch of inputtxs:
        {
            "Token 1": 100,
            "Token 2": 50
        }

        Parameters:
        prices: dictionary mapping token types to prices
        """
        super(self).__init__(price)
        self.update(**kwargs)
