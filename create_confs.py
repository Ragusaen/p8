#!/usr/bin/env python3
# coding: utf-8

"""
Script to generate configuration files for the generator/simulator. - v0.1

Copyright (C) 2020-2022.

All rights reserved.

 * This file can not be copied and/or distributed.

All rights reserved.

This program is distributed WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""
#Load required libraries
import random
import time
import json, yaml
import math
import argparse
import sys, os
import networkx as nx
from mpls_fwd_gen import *
from itertools import chain, combinations
from functools import reduce


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

def partition(lst, division):
    n = math.ceil(len(lst) / division)
    return [lst[round(division * i):round(division * (i + 1))] for i in range(n)]

def powerset(iterable, m = 0):
    """
    powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    """
    xs = list(iterable)
    # note we return an iterator rather than a list
    return chain.from_iterable(combinations(xs,n) for n in range(m+1))

def generate_failures_random(G, n, division = None, random_seed = 1):
    # create Failure information from sampling.
    F_list = [()]
    random.seed(random_seed)

    # compute numbers proportional to failure scenarios per k
    lis = list(map(lambda x: math.comb(G.number_of_edges(),x) , range(K+1)))
    r = reduce(lambda a,b: a+b, lis)
    p = list(map(lambda x: math.ceil(n*x/r),lis))

    excess = reduce(lambda a,b: a+b, p) - n
    p[-1] -= excess   #adjust.

    for k in range(1,K+1):
        X = combinations(list(G.edges),k)
        F = random.choices(list(X),k=p[k])
        F_list += F

    if division:
        P = partition(F_list, division)
        return P

    return [F_list]

def generate_failures_all(G, division = None, random_seed = 1):
    # create Failure information from sampling.

    all_of_em = list(powerset(G.edges(),m=K))

    if division:
        P = partition(all_of_em, division)
        return P

    return [all_of_em]


def generate_conf(n, conf_type = 0, topofile = None, random_seed = 1):
    if not topofile or conf_type == 0:
        base_config = {
            "random_topology": True,
            "random_mode": "random.log_degree",
            "num_routers": n,
            "random_weight_mode": "random",
            "random_gen_method": 1,
            "php": True,
            "ldp": False,
            "rsvp": True,
            "rsvp_num_lsps": int(math.sqrt(n)), #sqrt f(n)
            "rsvp_tunnels_per_pair": 3,
            "vpn": True,
            "vpn_num_services": int(math.sqrt(n)),
            "vpn_pes_per_services": 4,
            "vpn_ces_per_pe": 2,
            "random_seed_gen": random_seed
        }
    elif topofile:
        base_config = {
        #we need extra configuration here!!!!
            "topology": topofile,
            "random_weight_mode": "equal",
            "random_gen_method": 1,
            "php": False,
            "ldp": False,
            "rsvp": True,
            "rsvp_num_lsps": n, #sqrt f(n)
            "rsvp_tunnels_per_pair": 1,
            "vpn": False,
            "random_seed_gen": random_seed
        }
        if  conf_type == 1:
            base_config["enable_RMPLS"] = False
            base_config["protection"] = None
        elif  conf_type == 2:
            base_config["enable_RMPLS"] = True
            base_config["protection"] = None
        elif  conf_type == 3:
            base_config["enable_RMPLS"] = False
            base_config["protection"] = "facility-node"
        elif  conf_type == 4:
            base_config["enable_RMPLS"] = True
            base_config["protection"] = "facility-node"
        elif  conf_type == 5:
            base_config["enable_RMPLS"] = False
            base_config["rsvp"] = False
            base_config["ldp"] = True
        elif  conf_type == 6:
            base_config["enable_RMPLS"] = True
            base_config["rsvp"] = False
            base_config["ldp"] = True
        elif  conf_type == 7:
            base_config["enable_RMPLS"] = False
            base_config["protection"] = "plinko/1"
        elif  conf_type == 8:
            base_config["enable_RMPLS"] = False
            base_config["protection"] = "plinko/2"
        elif  conf_type == 9:
            base_config["enable_RMPLS"] = False
            base_config["protection"] = "plinko/3"
        elif  conf_type == 10:
            base_config["enable_RMPLS"] = False
            base_config["protection"] = "plinko/4"
        elif  conf_type == 21:
            base_config["tba"] = True

    return base_config


if __name__ == "__main__":
    # #general options
    p = argparse.ArgumentParser(description='Command line utility to generate MPLS simulation specifications.')

    p.add_argument("--topology", type=str, help="File with existing topology to be loaded.")
    p.add_argument("--conf", type=str, help="where to store created configurations. Must not exists.")

    p.add_argument("--K", type=int, default = 4, help="Maximum number of failed links.")

    p.add_argument("--threshold",type=int, default = math.comb(40,4), help="Maximum number of failures to generate")

    p.add_argument("--division",type=int, default = 1000, help="chunk size; number of failure scenarios per worker.")

    p.add_argument("--random_seed",type=int, default = 1, help="Random seed. Leave empty to pick a random one.")

    p.add_argument("--keep_failure_chunks", action="store_true", default=False, help="Do not generate failure chunks if they already exist")

    args = p.parse_args()
    conf = vars(args)

    topofile = conf["topology"]
    configs_dir = conf["conf"]
    K = conf["K"]
#    L = conf["L"]
    random_seed = conf["random_seed"]
    division = conf["division"]
    threshold = conf["threshold"]
    # Ensure the topologies can be found:
    assert os.path.exists(topofile)

    # create main folder for our experiments
    os.makedirs(configs_dir, exist_ok = True)

    # Load
    if topofile.endswith(".graphml"):
        gen = lambda x: nx.Graph(nx.read_graphml(x))
    elif topofile.endswith(".json"):
        gen = topology_from_aalwines_json
    else:
        exit(1)

    print(topofile)
    toponame = topofile.split('/')[-1].split(".")[0]
    folder = os.path.join(configs_dir,toponame)
    os.makedirs(folder, exist_ok = True)

    G = gen(topofile)
    n = G.number_of_nodes() * G.number_of_nodes()    #tentative number of LSPs

    def create(conf_type):
        dict_conf = generate_conf(n, conf_type = conf_type, topofile = topofile, random_seed = random_seed)
        path = os.path.join(folder, "conf_{}.yml".format(conf_type))
        dict_conf["output_file"] = os.path.join(folder, "dp_{}.yml".format(conf_type))
        with open(path, "w") as file:
            documents = yaml.dump(dict_conf, file, Dumper=NoAliasDumper)

    create(3)    # conf file with RSVP(FRR), no RMPLS
    create(21)   # conf file with TBA

    if not (args.keep_failure_chunks and os.path.exists(os.path.join(folder, "failure_chunks"))):
        # Generate failures
        if math.comb(G.number_of_edges(), K) > threshold:
            F_list = generate_failures_random(G, threshold, division = division, random_seed = random_seed)
        else:
            F_list = generate_failures_all(G,  division = division, random_seed = random_seed)

        failure_folder = os.path.join(folder, "failure_chunks")
        os.makedirs(failure_folder, exist_ok = True)
        i = 0
        for F_chunk in F_list:
            pathf = os.path.join(failure_folder, str(i)+".yml")
            i+=1
            with open(pathf, "w") as file:
                documents = yaml.dump(F_chunk, file, default_flow_style=True, Dumper=NoAliasDumper)
