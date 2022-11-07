from typing import List, Tuple
from outputtx import OutputTx
from poolstatus import PoolStatusInterface

def price_impact(output: List[List[OutputTx]]) -> List[Tuple[float, float]]:
    """
    Measures magnitude of price impact for transaction pairs before and after 
    transactions' execution as function of proportion of output token balance 
    removed.

    Lower magnitudes are better since they indicate a greater ability to handle
    large volume swaps. It's also expected that as proportionately more of the
    output token balance is drained, the magnitude is higher.

    Parameters:
    1. output: swap metrics

    Returns:
    1. percentage changes of exchange rates after each swap
    """
    result = []
    
    i = 0
    for lst in output:
        for info in lst:
            if info.outpool_after_val < info.outpool_init_val:
                rate = (info.inpool_after_val - info.inpool_init_val) / (info.outpool_init_val - info.outpool_after_val)
                drained = 1 - info.outpool_after_val / info.outpool_init_val
                result.append([drained, abs((info.after_rate - rate) / rate)])
                i += 1
    
    print("avg price impact: " + str(sum([i[1] for i in result]) / len(result)))
    return result

def capital_efficiency(output: List[List[OutputTx]]) -> List[Tuple[float, float]]:
    """
    Measures internal swap rate against market rate as function of proportion of
    output token balance removed

    The ratio internal swap rate / market rate should desireably be near 1 and
    be as low as possible. It's also expected that as proportionately more of
    the output token balance is drained, the ratio is higher.
    
    Parameters:
    1. output: swap metrics

    Returns:
    1. ratios of internal vs market exchange rate for each swap
    """
    result = []

    for batch in output:
        for info in batch:
            if info.outpool_after_val < info.outpool_init_val:
                rate = (info.inpool_after_val - info.inpool_init_val) / (info.outpool_init_val - info.outpool_after_val)
                drained = 1 - info.outpool_after_val / info.outpool_init_val
                result.append([drained, rate / info.market_rate])
    
    print("avg capital efficiency: " + str(sum([i[1] for i in result]) / len(result)))
    return result

def impermanent_loss(initial: PoolStatusInterface,
    history: List[List[PoolStatusInterface]]) -> Tuple[List[float], List[float]]:
    """
    Measures the amount of impermanent loss or gain between batches

    Parameters:
    1. initial: pool state before any swaps
    1. history: pool state after each transaction

    Returns:
    1. percentage increases of token balances after each swap (relative to start)
    2. percentage decreases of token balances after each swap (relative to start)
    """
    pos_results = []
    neg_results = []

    for batch in history:
        for status in batch:
            pos_changes = []
            neg_changes = []
            for token in initial:
                change = status[token][0] / initial[token][0] - 1
                if change > 0:
                    pos_changes.append(change)
                else:
                    neg_changes.append(change)

            if len(pos_changes):
                pos_results.append(sum(pos_changes) / len(pos_changes))
            if len(neg_changes):
                neg_results.append(abs(sum(neg_changes)) / len(neg_changes))
    
    print("avg impermanent gain: " + str(sum(pos_results) / len(pos_results)))
    print("avg impermanent loss: " + str(sum(neg_results) / len(neg_results)))
    return pos_results, neg_results
