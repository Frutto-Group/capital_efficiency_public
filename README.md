# capital_efficiency_public

DODO exchange's proactive market maker generalizes the concepts of constant product market making, which is the pricing system employed by most AMM-based DEXs today. PMM utilizes an adjustable parameter k to increase capital efficiency and incorporates oracle price data to reduce impermanent loss. Key to both of these functioning is a trading pair's liquidity. We expanded PMM into the multitoken setting (where we replace trading pairs with a liquidity pool consisting of all tokens) to propose MPMM. We hypothesized the increased total pool liquidity could amplify PMM's effects on capital efficiency and impermanent loss.

We compared MPMM's performance against PMM, constant product market makers, and constant sum market makers through simulations and found it performs orders of magnitude better than its counterparts in efficiency metrics due to tokens' liquidities being available across all trading pairs. Similarly, this increased liquidity also dampened the effects of impermanent loss significantly more than PMM.

An issue worth further investigating are the effects of a token price crash on impermanent loss. This is especially a concern for the multi token setting since liquidity providers supplying any token would be effected. Simulations showed that MPMM performed well in impermanent loss, so we are hopeful the price crash scenario would not have outsized effects.

simulation results here:
https://drive.google.com/drive/folders/1lVF7ZpfTh2vQi-zJ8_nl84kiJHpaa9eo?usp=sharing

run simulation with command:
```
python simulator.py -d <folder for results>
```
