import argparse
import os
import json
import pickle
import matplotlib
from types import SimpleNamespace

import oracles
import marketmakers
import metrics
import visualizers
import trafficgens

KEYWORDS = [
    'traffics',
    'ext_prices',
    'outputs',
    'statuses',
    'slippage',
    # 'iloss'
]


def simulate(config, reload):
    matplotlib.use('Agg')

    if reload:
        with open(os.path.join(config['path'], 'simulation_data.pkl'), 'rb') as f:
            sim_data = pickle.load(f)
    else:
        if not os.path.exists(config['path']):
            os.makedirs(config['path'])

        _TrafficGenClass = getattr(trafficgens, config['traffic']['type'])
        _traffic_generator = _TrafficGenClass(
            **config['traffic']['init_kwargs'])

        _OracleClass = getattr(oracles, config['oracle']['type'])
        _oracle = _OracleClass(**config['oracle']['init_kwargs'])

        _MMClass = getattr(marketmakers, config['market_maker']['type'])
        mm = _MMClass(**config['market_maker']['init_kwargs'])

        mm.configure_arbitrage(**config['market_maker']['arb_kwargs'])

        traffics = _traffic_generator.generate_traffic()
        ext_prices = _oracle.simulate_ext_prices(traffics)
        outputs, statuses = mm.simulate_traffic(traffics, ext_prices)
        slippage = metrics.slippage(outputs)
        #iloss = metrics.impermanent_loss(ext_prices, statuses)
        # TODO: Fill in other metrics !!

        sim_data = SimpleNamespace()
        for keyword in KEYWORDS:
            setattr(sim_data, keyword, eval(keyword))

        with open(os.path.join(config['path'], 'simulation_data.pkl'), 'wb') as f:
            pickle.dump(sim_data, f)

    for visname, info in config['visualization'].items():
        visfunc, kwargs = getattr(visualizers, visname), info
        for keyword in KEYWORDS:
            if keyword in visfunc.__code__.co_varnames:
                kwargs[keyword] = getattr(sim_data, keyword)

        fig = visfunc(**kwargs)
        fig.savefig(os.path.join(config['path'], f'{visname}.jpg'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Market Maker Simulator')
    parser.add_argument('-c', '--config', type=str, required=True,
                        help='Path to configuration file (json)')
    parser.add_argument('-r', '--reload', action='store_true',
                        help='Set flag to directly load result if run before')

    args = parser.parse_args()

    print(args)
    with open(args.config, 'r') as f:
        config = json.load(f)

    simulate(config, args.reload)
