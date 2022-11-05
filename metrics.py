from typing import List, Tuple, float
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
    output: swap metrics
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
    
    return result

def capital_efficiency(output: List[List[OutputTx]]) -> List[Tuple[float, float]]:
    """
    Measures internal swap rate against market rate as function of proportion of
    output token balance removed

    The ratio internal swap rate / market rate should desireably be near 1 and
    be as low as possible. It's also expected that as proportionately more of
    the output token balance is drained, the ratio is higher.
    
    Parameters:
    output: swap metrics
    """
    result = []

    for batch in output:
        for info in batch:
            if info.outpool_after_val < info.outpool_init_val:
                rate = (info.inpool_after_val - info.inpool_init_val) / (info.outpool_init_val - info.outpool_after_val)
                drained = 1 - info.outpool_after_val / info.outpool_init_val
                result.append([drained, rate / info.market_rate])
    
    return result

def impermanent_loss(initial: PoolStatusInterface,
    history: List[List[PoolStatusInterface]]) -> List[float]:
    """
    Measures the magnitude (percent) of the average impermanent loss or gain

    Parameters:
    initial: pool state before any swaps
    history: pool state after each transaction
    """
    results = []

    for batch in history:
        for status in batch:
            total_change = 0
            for token in initial:
                start = initial[token][0]
                total_change += abs((status[token][0] - start) / start)
            results.append(total_change / len(initial))
    
    return results
