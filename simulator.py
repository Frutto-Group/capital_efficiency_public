import argparse
import json
import pickle

import oracles
import marketmakers
import metrics
import trafficgens
from balance_initializer import BalanceInitializer
from price import Price

import matplotlib.pyplot as plt
import json

def simulate(config):
    _balance_initializer = BalanceInitializer(**config["balance_initializer"]["init_kwargs"])
    pairwise_pools, pairwise_infos, single_pools, single_infos, token_infos = _balance_initializer.getBalances()

    _TrafficGenClass = getattr(trafficgens, config['traffic']['type'])
    _traffic_generator = _TrafficGenClass(**config['traffic']['init_kwargs'])

    _OracleClass = getattr(oracles, config['oracle']['type'])
    _oracle = _OracleClass(**config['oracle']['init_kwargs'])

    _MMClass = getattr(marketmakers, config['market_maker']['type'])
    mm = _MMClass(
        pairwise_pools = pairwise_pools,
        pairwise_infos = pairwise_infos,
        single_pools = single_pools,
        single_infos = single_infos
    )
    mm.configure_simulation(**config['market_maker']['simulate_kwargs'])

    # generate prices, traffic and store in files
    # ext_prices = _oracle.simulate_ext_prices(token_infos)
    # traffics = _traffic_generator.generate_traffic(ext_prices)
    # f = open("{}_traffic.obj".format(market), "wb")
    # pickle.dump(traffics, f)
    # f.close()
    # f = open("{}_prices.obj".format(market), "wb")
    # pickle.dump(ext_prices, f)
    # f.close()

    # load prices, traffic frome files
    f = open("{}_traffic.obj".format(market), "rb")
    traffics = pickle.load(f)
    f.close()
    f = open("{}_prices.obj".format(market), "rb")
    ext_prices = pickle.load(f)
    f.close()

    outputs, statuses, status0 = mm.simulate_traffic(traffics, ext_prices)

    # compute metrics
    capital_efficiency = metrics.capital_efficiency(outputs)
    impermanent_gain, impermanent_loss = metrics.impermanent_loss(status0, statuses)
    price_impact = metrics.price_impact(outputs)

    # price_impact
    plt.scatter([x[0] for x in price_impact], [x[1] for x in price_impact], s=1)
    plt.savefig('images/price_impact/{m}/{n}.png'.format(m=market, n=file_name))
    plt.clf()
    pickle.dump(price_impact, open("data/price_impact/{m}/{n}.pkl".format(m=market, n=file_name), "wb"))
    
    # capital efficiency
    plt.scatter([x[0] for x in capital_efficiency], [x[1] for x in capital_efficiency], s=1)
    plt.savefig('images/capital_efficiency/{m}/{n}.png'.format(m=market, n=file_name))
    plt.clf()
    pickle.dump(capital_efficiency, open("data/capital_efficiency/{m}/{n}.pkl".format(m=market, n=file_name), "wb"))
    
    # impermanent loss
    plt.scatter([i for i in range(len(impermanent_gain))], impermanent_gain, s=1)
    plt.savefig('images/impermanent_loss/{m}/gain/{n}.png'.format(m=market, n=file_name))
    plt.clf()
    pickle.dump(impermanent_gain, open("data/impermanent_loss/{m}/gain/{n}.pkl".format(m=market, n=file_name), "wb"))
    plt.scatter([i for i in range(len(impermanent_loss))], impermanent_loss, s=1)
    plt.savefig('images/impermanent_loss/{m}/loss/{n}.png'.format(m=market, n=file_name))
    plt.clf()
    pickle.dump(impermanent_loss, open("data/impermanent_loss/{m}/loss/{n}.pkl".format(m=market, n=file_name), "wb"))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Market Maker Simulator')
    parser.add_argument('-c', '--config', type=str, required=True,
                        help='Path to configuration file (json)')
    parser.add_argument('-m', '--market', type=str, required=True,
                        help='type of market (random, volatile, etc)')
    parser.add_argument('-n', '--name', type=str, required=True,
                        help='name of saved files')

    args = parser.parse_args()
    market = args.market
    file_name = args.name

    with open(args.config, 'r') as f:
        config = json.load(f)

    simulate(config)
