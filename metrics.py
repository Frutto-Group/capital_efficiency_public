import numpy as np
from typing import List, Tuple
from outputtx import OutputTx
from price import Price
from poolstatus import PoolStatusInterface

def slippage(output: List[List[OutputTx]], initial: List[float], after: List[float]) -> List[Tuple[float]]:
    """
    Measures the exchange rate before and after a transaction has executed
    """
    result = []

    for batch in output:
        for tx in batch:
            if tx.outval > 0:
                result.append([tx.index, abs((after[tx.index] - initial[tx.index]) / initial[tx.index])])

    return result

def new_capital_efficiency(output: List[List[OutputTx]]) -> Tuple[List[List[float]], List[int]]:
    """
    Measures how the internal swap rate compares to the market rate

    In the graph, a value > 1 indicates the internal rate is more expensive than
    the market rate. Supposedly, increasing how much of the outtype pool we should
    also increase the internal rate.
    """
    result = []

    for batch in output:
        for tx in batch:
            if tx.outval > 0:
                result.append([(tx.outpoolinvval - tx.outpoolinitval) / tx.outpoolinvval, tx.mmp / tx.omp])
                # if tx.mmp / tx.omp > 100:
                #     print({
                #         "input_token_type": tx.intype,
                #         "output_token_type": tx.outtype,
                #         "input_token_value": tx.inval,
                #         "output_token_value": tx.outval,
                #         "input_token_pool_initial_value": tx.inpoolinitval,
                #         "output_token_pool_initial_value": tx.outpoolinvval,
                #         "input_token_pool_inventory_value": tx.inpoolinvval,
                #         "output_token_pool_inventory_value": tx.outpoolinitval,
                #         "marginal_market_price": tx.mmp,
                #         "oracle_market_price": tx.omp,
                #     })
    return result

def new_impermanent_loss(external_price: List[Price], status: List[List[PoolStatusInterface]]) -> List[float]:
    """
    Measures the percentage change of the value of the pool, with respect to a fixed
    currency like USD, as prices change from batch to batch (and token balances
    also change)
    """
    result = []

    if len(status) == 1: #single_batch
        for i, stat in enumerate(status[0][:-1]):
            start_value = stat.get_total_value(external_price[0])
            end_value = status[0][i + 1].get_total_value(external_price[0])
            result.append([i, (end_value - start_value) / start_value])
    else: #multi_batch
        for i, stat in enumerate(status[:-1]):
            next_status = status[i + 1][0]
            start_value = stat[0].get_total_value(external_price[i])
            end_value = next_status.get_total_value(external_price[i + 1])
            result.append([i, (end_value - start_value) / start_value])

    return result

def holding_changes(external_price: List[Price], status: List[List[PoolStatusInterface]]) -> List[float]:
    """
    Measures the percentage change of the value of the pool assuming no swaps occur
    (the tokens were just held and token prices changed). This hould be completely
    random.
    """
    result = []

    for i, status_list in enumerate(status[:-1]):
        start = status_list[0].get_total_value(external_price[i])
        end = status_list[-1].get_total_value(external_price[i + 1])
        result.append([i, (end - start) / start])

    return result

def lp_impermanent_loss(initial: PoolStatusInterface, after: PoolStatusInterface) -> float:
    """
    Measures how far away from initial equilibrium balances a pool will end up after
    handling all traffic and it's been arbitraged
    """
    pos_diff = 0
    pos_pools = 0
    neg_diff = 0
    neg_pools = 0
    neg_lst = []
    pos_lst = []
    for k in initial.keys():
        change = (after[k][0] - initial[k][0]) / initial[k][0]
        if change > 0:
            pos_lst.append(change)
            pos_diff += change
            pos_pools += 1
        else:
            neg_lst.append(change)
            neg_diff += change
            neg_pools += 1

    neg, pos = -1, -1
    if neg_pools != 0:
        neg = neg_diff / neg_pools
    if pos_pools != 0:
        pos = pos_diff / pos_pools

    return neg, pos, neg_lst, pos_lst
