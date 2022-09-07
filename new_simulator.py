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

import matplotlib.pyplot as plt
import json

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

        # ext_prices = _oracle.simulate_ext_prices()
        # traffics = _traffic_generator.generate_traffic(ext_prices)
        # f = open("traffic_rand_10000_5_multitok_10000_5000.obj", "wb")
        # pickle.dump(traffics, f)
        # f.close()
        # f = open("prices_rand_10000_multitok_003_001_095.obj", "wb")
        # pickle.dump(ext_prices, f)
        # f.close()

        f = open("traffic_rand_10000_5_multitok_10000_5000.obj", "rb")
        traffics = pickle.load(f)
        f.close()
        f = open("prices_rand_10000_multitok_003_001_095.obj", "rb")
        ext_prices = pickle.load(f)
        f.close()

        outputs, statuses, status0, status1, rate0, rate1 = mm.simulate_traffic(traffics, ext_prices)

        new_capital_efficiency = metrics.new_capital_efficiency(outputs)
        new_impermanent_loss = metrics.new_impermanent_loss(ext_prices, statuses)
        slippage = metrics.slippage(outputs, rate0, rate1)
        losses, gains, neg_lst, pos_lst = metrics.lp_impermanent_loss(status0, status1)

        plt.scatter([x[0] for x in slippage], [x[1] for x in slippage], s=1)
        plt.savefig('images/multi_batch/multi_tok/slip/csmm.png')
        plt.clf()
        pickle.dump(slippage, open("raw_data/multi_batch/multi_tok/slip/csmm.pkl", "wb"))

        plt.scatter([x[0] for x in new_capital_efficiency], [x[1] for x in new_capital_efficiency], s=1)
        plt.savefig('images/multi_batch/multi_tok/cap_eff/csmm.png')
        plt.clf()
        pickle.dump(new_capital_efficiency, open("raw_data/multi_batch/multi_tok/cap_eff/csmm.pkl", "wb"))

        plt.scatter([x[0] for x in new_impermanent_loss], [x[1] for x in new_impermanent_loss], s=1)
        plt.savefig('images/multi_batch/multi_tok/imp_los/csmm.png')
        plt.clf()
        pickle.dump(new_impermanent_loss, open("raw_data/multi_batch/multi_tok/imp_los/csmm.pkl", "wb"))

        print("lp_impermanent_loss: " + str((losses, gains)))
        pickle.dump(neg_lst, open("raw_data/multi_batch/multi_tok/neg_lp_imp_los/csmm.pkl", "wb"))
        pickle.dump(pos_lst, open("raw_data/multi_batch/multi_tok/pos_lp_imp_los/csmm.pkl", "wb"))

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
