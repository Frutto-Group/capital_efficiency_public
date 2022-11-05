import argparse
import os
import json
import pickle
import matplotlib

import oracles
import marketmakers
import metrics
import trafficgens

import matplotlib.pyplot as plt
import json

def simulate(config, reload):
    matplotlib.use('Agg')

    if not os.path.exists(config['path']):
        os.makedirs(config['path'])

    _TrafficGenClass = getattr(trafficgens, config['traffic']['type'])
    _traffic_generator = _TrafficGenClass(
        **config['traffic']['init_kwargs'])

    _OracleClass = getattr(oracles, config['oracle']['type'])
    _oracle = _OracleClass(**config['oracle']['init_kwargs'])

    _MMClass = getattr(marketmakers, config['market_maker']['type'])
    mm = _MMClass(**config['market_maker']['init_kwargs'])

    mm.configure_simulation(**config['market_maker']['simulate_kwargs'])

    # generate prices, traffic and store in files
    # ext_prices = _oracle.simulate_ext_prices()
    # traffics = _traffic_generator.generate_traffic(ext_prices)
    # f = open("traffic.obj", "wb")
    # pickle.dump(traffics, f)
    # f.close()
    # f = open("prices.obj", "wb")
    # pickle.dump(ext_prices, f)
    # f.close()

    # load prices, traffic frome files
    f = open("traffic.obj", "rb")
    traffics = pickle.load(f)
    f.close()
    f = open("prices.obj", "rb")
    ext_prices = pickle.load(f)
    f.close()

    outputs, statuses, status0, status1 = mm.simulate_traffic(traffics, ext_prices)

    # # compute metrics
    capital_efficiency = metrics.capital_efficiency(outputs)
    impermanent_loss = metrics.impermanent_loss(status0, statuses)
    rate_change = metrics.price_impact(outputs)

    # # rate change
    # plt.scatter([x[0] for x in rate_change], [x[1] for x in rate_change], s=1)
    # plt.savefig('images/multi_batch/multi_tok/rate_change/mpmm.png')
    # plt.clf()
    # pickle.dump(rate_change, open("raw_data/multi_batch/multi_tok/rate_change/mpmm.pkl", "wb"))
    
    # # capital efficiency
    # plt.scatter([x[0] for x in capital_efficiency], [x[1] for x in capital_efficiency], s=1)
    # plt.savefig('images/multi_batch/multi_tok/cap_eff/amm.png')
    # plt.clf()
    # pickle.dump(capital_efficiency, open("raw_data/multi_batch/multi_tok/cap_eff/amm.pkl", "wb"))
    
    # # impermanent loss
    # plt.scatter([x[0] for x in impermanent_loss], [x[1] for x in impermanent_loss], s=1)
    # plt.savefig('images/multi_batch/multi_tok/imp_los/amm.png')
    # plt.clf()
    # pickle.dump(impermanent_loss, open("raw_data/multi_batch/multi_tok/imp_los/amm.pkl", "wb"))

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
