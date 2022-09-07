import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from inputtx import InputTx
from typing import List


def plot_slippage_by_1st_tx(
    traffics: List[List[List[InputTx]]],
    slippage: List[List[List[float]]],
    fig_kwargs={},
    plot_kwargs={}
) -> plt.Figure:
    # print(traffics, slippage)

    size, slippage_ = zip(*[
        (traffics[0][0].inval, slippage_traffics[0][0])
        for traffics, slippage_traffics in zip(traffics, slippage)])

    fig, ax = plt.subplots(ncols=1, nrows=1, **fig_kwargs)
    ax.plot(size, slippage_, **plot_kwargs)
    ax.set_xlabel('Input Value')
    ax.set_ylabel('Slippage')


    return fig


def plot_two_traffics(
    traffics: List[List[List[InputTx]]],
    intype: str,
    outtype: str,
    mu: float,
    sigma: float,
    fig_kwargs={},
    plot_kwargs={}
) -> plt.Figure:

    fig, ax = plt.subplots(nrows=1, ncols=1, **fig_kwargs)

    s = []
    for traffic in traffics:
        for task in traffic:
            for tx in task:
                if (tx.input_token_type == intype):
                    s.append(tx.input_token_value)
                else:
                    s.append(-tx.input_token_value)

    count, bins, ignored = ax.hist(s, 30, density=True, **plot_kwargs)
    ax.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) *
            np.exp(- (bins - mu)**2 / (2 * sigma**2)), linewidth=2, color='r')
    return fig
