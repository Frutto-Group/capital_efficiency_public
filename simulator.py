import argparse
import json
import pickle
import os

import marketmakers
import metrics
from initializer import Initializer
from pricegen import PriceGenerator
from trafficgen import TrafficGenerator

import matplotlib.pyplot as plt
import json

def simulate(config):
    initializer = Initializer(**config["initializer"]["init_kwargs"])
    initializer.configure_tokens(**config["initializer"]["token_configs"])
    pairwise_pools, pairwise_infos, single_pools, single_infos, \
        traffic_info, price_gen_info, crash_types = initializer.get_stats()

    traffic_generator = TrafficGenerator(**config['traffic']['init_kwargs'])
    traffic_generator.configure_tokens(single_pools, traffic_info)

    price_generator = PriceGenerator(**config['price_gen']['init_kwargs'])
    price_generator.configure_tokens(price_gen_info)

    MMClass = getattr(marketmakers, config['market_maker']['type'])
    mm = MMClass(
        pairwise_pools = pairwise_pools,
        pairwise_infos = pairwise_infos,
        single_pools = single_pools,
        single_infos = single_infos
    )
    mm.configure_simulation(**config['market_maker']['simulate_kwargs'])
    mm.configure_crash_types(crash_types)

    # generate prices, traffic and store in files
    price_dir = os.path.join(base_dir, market + "_price.obj")
    if not os.path.exists(price_dir):
        ext_prices = price_generator.simulate_ext_prices()
        f = open(price_dir, "wb")
        pickle.dump(ext_prices, f)
        f.close()
    else:
        f = open(price_dir, "rb")
        ext_prices = pickle.load(f)
        f.close()
    
    traffic_dir = os.path.join(base_dir, market + "_traffic.obj")
    if not os.path.exists(traffic_dir):
        traffics = traffic_generator.generate_traffic(ext_prices)
        f = open(traffic_dir, "wb")
        pickle.dump(traffics, f)
        f.close()
    else:
        f = open(traffic_dir, "rb")
        traffics = pickle.load(f)
        f.close()

    outputs, statuses, status0, crash_types = mm.simulate_traffic(traffics, ext_prices)

    # compute metrics
    disply_name = market + " " + mm_name
    capital_efficiency, cap_eff_dict = metrics.capital_efficiency(outputs, crash_types, disply_name)
    impermanent_gain, impermanent_loss, gain_dict, loss_dict =\
         metrics.impermanent_loss(status0, statuses, crash_types, disply_name)
    price_impact, price_imp_dict = metrics.price_impact(outputs, crash_types, disply_name)

    # price_impact
    plt.scatter([x[0] for x in price_impact], [x[1] for x in price_impact], s=1)
    plt.savefig('{d}/images/price_impact/{m}/{n}.png'.format(d=base_dir, m=market, n=mm_name))
    plt.clf()
    pickle.dump(price_impact, \
        open("{d}/raw_data/price_impact/{m}/{n}.pkl".format(d=base_dir, m=market, n=mm_name), "wb"))
    with open("{d}/stats/price_impact/{m}/{n}.json".format(d=base_dir, m=market, n=mm_name), "w") as f:
        f.write(json.dumps(price_imp_dict))
    
    # capital efficiency
    plt.scatter([x[0] for x in capital_efficiency], [x[1] for x in capital_efficiency], s=1)
    plt.savefig('{d}/images/capital_efficiency/{m}/{n}.png'.format(d=base_dir, m=market, n=mm_name))
    plt.clf()
    pickle.dump(capital_efficiency, \
        open("{d}/raw_data/capital_efficiency/{m}/{n}.pkl".format(d=base_dir, m=market, n=mm_name), "wb"))
    with open("{d}/stats/capital_efficiency/{m}/{n}.json".format(d=base_dir, m=market, n=mm_name), "w") as f:
        f.write(json.dumps(cap_eff_dict))
    
    # impermanent loss
    plt.scatter([x[0] for x in impermanent_gain], [x[1] for x in impermanent_gain], s=1)
    plt.savefig('{d}/images/impermanent_gain/{m}/{n}.png'.format(d=base_dir, m=market, n=mm_name))
    plt.clf()
    pickle.dump(impermanent_gain, \
        open("{d}/raw_data/impermanent_gain/{m}/{n}.pkl".format(d=base_dir, m=market, n=mm_name), "wb"))
    with open("{d}/stats/impermanent_gain/{m}/{n}.json".format(d=base_dir, m=market, n=mm_name), "w") as f:
        f.write(json.dumps(gain_dict))
    plt.scatter([x[0] for x in impermanent_loss], [x[1] for x in impermanent_loss], s=1)
    plt.savefig('{d}/images/impermanent_loss/{m}/{n}.png'.format(d=base_dir, m=market, n=mm_name))
    plt.clf()
    pickle.dump(impermanent_loss, \
        open("{d}/raw_data/impermanent_loss/{m}/{n}.pkl".format(d=base_dir, m=market, n=mm_name), "wb"))
    with open("{d}/stats/impermanent_loss/{m}/{n}.json".format(d=base_dir, m=market, n=mm_name), "w") as f:
        f.write(json.dumps(loss_dict))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Market Maker Simulator')
    parser.add_argument('-d', '--results_dir', type=str, required=True,
                        help='Path to results directory')

    base_dir = parser.parse_args().results_dir
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)

    data_dirs = []
    for dir in ["images", "stats", "raw_data"]:
        combined_dir = os.path.join(base_dir, dir)
        data_dirs.append(combined_dir)
        if not os.path.exists(combined_dir):
            os.mkdir(combined_dir)
    
    for market in os.listdir("config"): 
        category_dirs = \
            ["price_impact", "capital_efficiency", "impermanent_gain", "impermanent_loss"]
        for dir in data_dirs:
            for sub_dir in category_dirs:
                combined_dir = os.path.join(dir, sub_dir)
                if not os.path.exists(combined_dir):
                    os.mkdir(combined_dir)
                
                market_dir = os.path.join(combined_dir, market)
                if not os.path.exists(market_dir):
                    os.mkdir(market_dir)
        
        market_path = os.path.join("config", market)
        for env in os.listdir(market_path):
            mm_name = env[:-5]
            with open(os.path.join(market_path, env), 'r') as f:
                config = json.load(f)

            simulate(config)
