import numpy as np
import statistics
import matplotlib.pyplot as plt
import json
from typing import List, Tuple, Dict
from outputtx import OutputTx
from poolstatus import PoolStatusInterface

def get_stats(data: List[float], title: str) -> Dict[str, float]:
    """
    Computes and prints statistics given data

    Parameters:
    1. data: data
    2. title: label for data (to be printed)

    Returns:
    1. statistics on Data
    """
    print("\n{} data:".format(title))
    sliced_data = [i[1] for i in data]
    stat_dict = {}
    
    if len(sliced_data):
        stat_dict["avg"] = sum(sliced_data) / len(sliced_data)
        stat_dict["med"] = statistics.median(sliced_data)
        
        plot = plt.boxplot(sliced_data)
        plt.close()
        quartiles = [item.get_ydata()[0] for item in plot['whiskers']]
        ends = [item.get_ydata()[1] for item in plot['whiskers']]
        stat_dict["quart_1"],  stat_dict["quart_3"] = quartiles[0], quartiles[1]
        stat_dict["min"], stat_dict["max"] = ends[0], ends[1]

        stat_dict["stdv"] = np.std(sliced_data)
        print(json.dumps(stat_dict, indent=4))
    else:
        print("    no {} data".format(title))

    return stat_dict

def price_impact(output: List[List[OutputTx]], crash_types: List[str], file: str
) -> Tuple[List[Tuple[float, float]], Dict[str, float]]:
    """
    Measures magnitude of price impact for transaction pairs before and after 
    transactions' execution as function of proportion of output token balance 
    removed.

    Lower magnitudes are better since they indicate a greater ability to handle
    large volume swaps. It's also expected that as proportionately more of the
    output token balance is drained, the magnitude is higher.

    Parameters:
    1. output: swap metrics
    2. crash_types: what token types crashed in price (are excluded from metrics)
    3. file: name of file running simulation from

    Returns:
    1. magnitude of percentage changes of exchange rates after each swap
    2. statistics of results
    """
    result = []
    
    for lst in output:
        for info in lst:
            if info.outpool_after_val < info.outpool_init_val and \
                 not info.in_type in crash_types:
                try:
                    rate = (info.inpool_after_val - info.inpool_init_val) / \
                        (info.outpool_init_val - info.outpool_after_val)
                    drained = 1 - info.outpool_after_val / info.outpool_init_val
                    result.append([drained, abs((info.after_rate - rate) / rate)])
                except:
                    continue
    
    return result, get_stats(result, "{} price impact".format(file))

def capital_efficiency(output: List[List[OutputTx]], crash_types: List[str], file: str
) -> Tuple[List[Tuple[float, float]], Dict[str, float]]:
    """
    Measures internal swap rate against market rate as function of proportion of
    output token balance removed

    The ratio internal swap rate / market rate should desireably be near 1 and
    be as low as possible. It's also expected that as proportionately more of
    the output token balance is drained, the ratio is higher.
    
    Parameters:
    1. output: swap metrics
    2. crash_types: what token types crashed in price (are excluded from metrics)
    3. file: name of file running simulation from

    Returns:
    1. ratios of internal vs market exchange rate for each swap
    2. statistics of results
    """
    result = []

    for batch in output:
        for info in batch:
            if info.outpool_after_val < info.outpool_init_val and \
                 not info.in_type in crash_types:
                try:
                    rate = (info.inpool_after_val - info.inpool_init_val) / \
                        (info.outpool_init_val - info.outpool_after_val)
                    drained = 1 - info.outpool_after_val / info.outpool_init_val
                    result.append([drained, rate / info.market_rate])
                except:
                    continue
    
    return result, get_stats(result, "{} capital efficiency".format(file))

def impermanent_loss(initial: PoolStatusInterface, history: List[List[PoolStatusInterface]],
crash_types: List[str], file: str) -> Tuple[List[float], List[float], Dict[str, float], Dict[str, float]]:
    """
    Measures the amount of impermanent loss or gain between batches

    Parameters:
    1. initial: pool state before any swaps
    2. history: pool state after each transaction
    3. crash_types: what token types crashed in price (are excluded from metrics)
    4. file: name of file running simulation from

    Returns:
    1. percentage increases of token balances after each swap (relative to start)
    2. percentage decreases of token balances after each swap (relative to start)
    3. statistics on token balance increases
    4. statistics on token balance decreases
    """
    pos_results = []
    neg_results = []
    swap_counter = 1
    last_loss = 0
    last_gain = 0

    for batch in history:
        for status in batch:
            for token in initial:
                if not token in crash_types:
                    change = status[token][0] / initial[token][0] - 1
                    if change > 0:
                        last_gain = swap_counter
                        pos_results.append((swap_counter, abs(change)))
                    else:
                        last_loss = swap_counter
                        neg_results.append((swap_counter, abs(change)))            
            
            swap_counter += 1
    
    pos_dict = get_stats(pos_results, "{} impermanent gain".format(file))
    neg_dict = get_stats(neg_results, "{} impermanent loss".format(file))
    pos_dict["last_gain"], pos_dict["last_swap"] = last_gain, swap_counter
    neg_dict["last_loss"], pos_dict["last_swap"] = last_loss, swap_counter
    
    return pos_results, neg_results, pos_dict, neg_dict
