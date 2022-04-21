import itertools
import queue
import random
from functools import cmp_to_key
from typing import Union, Set, List, Dict, Tuple

import networkx as nx
from networkx import Graph
import matplotlib.pyplot as plt

from mpls_classes import MPLS_Client, Network, oFEC, Router
from target_based_arborescence.arborescences import find_arborescences


def find_partial_arborescences(graph: Graph, egress: str) -> List[List[Tuple[str, str]]]:
    edges: list[tuple[str, str]] = [(n1, n2) for (n1, n2) in graph.edges if n1 != n2] \
                                   + [(n2, n1) for (n1, n2) in graph.edges if n1 != n2]
    arbs = []

    for n in graph.neighbors(egress):
        arbs.append([(n, egress)])
        edges.remove((n, egress))

    for i in range(len(arbs)):
        while True:
            nodes_in_arbor = get_nodes_in_arbor(arbs[i])
            edges_to_consider = [e for e in edges if e[1] in nodes_in_arbor and e[0] not in nodes_in_arbor]
            if len(edges_to_consider) == 0:
                break
            e = random.choice(edges_to_consider)
            arbs[i].append(e)
            edges.remove(e)

    return arbs

def get_nodes_in_arbor(arbor):
    nodes = set()
    for e in arbor:
        nodes.add(e[0])
        nodes.add(e[1])
    return nodes

def get_nodes_in_arbors(arbors):
    nodes = set()
    for arbor in arbors:
        nodes.union(get_nodes_in_arbor(arbor))
    return nodes

def get_edges_in_arbors(arbors):
    edges = []
    for arbor in arbors:
        for e in arbor:
            edges.append(e)
    return edges

def get_unused_edges_in_arbors(graph, arbors):
    arbor_edges = get_edges_in_arbors(arbors)
    unused_edges = []
    for e in graph.edges:
        if e not in arbor_edges:
            unused_edges.append(e)

    return unused_edges

def dag_extension(graph: Graph, arbors: List[List[Tuple[str, str]]]):
    extended = True
    while extended:
        extended = False
        for arbor in arbors:
            for unused_edge in get_unused_edges_in_arbors(graph, arbors):
                if unused_edge[1] in get_nodes_in_arbor(arbor):
                    arbor.append(unused_edge)
                    dgraph = nx.DiGraph(arbor)
                    if nx.is_directed_acyclic_graph(dgraph):
                        extended = True
                    else:
                        arbor.remove(unused_edge)
    return arbors

class Grafting_Client(MPLS_Client):
    protocol = "gft"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # The arborescences that are rooted in this router
        self.arborescences: list[list[tuple[str, str]]] = []

        # The FECs this router is a non-tailend part of. fec_name -> (fec, next_hop, bounce_fec_name)
        self.arborescence_next_hop: dict[str, tuple[oFEC, str, str]] = {}


    # Abstract functions to be implemented by each client subclass.
    def LFIB_compute_entry(self, fec: oFEC, single=False):
        _, next_hop, bounce_fec_name = self.arborescence_next_hop[fec.name]

        local_label = self.get_local_label(fec)
        assert(local_label is not None)

        # If final hop, pop the label
        if next_hop == fec.value[0]:
            main_entry = {"out": next_hop, "ops": [{"pop" : ""}], "weight" : 0}
        else:
            remote_label = self.get_remote_label(next_hop, fec)
            assert(remote_label is not None)
            main_entry = {"out": next_hop, "ops": [{"swap" : remote_label}], "weight" : 0}
        yield (local_label, main_entry)

        if bounce_fec_name is not None:
            bounce_fec, bounce_next_hop, _ = self.arborescence_next_hop[bounce_fec_name]
            remote_bounce_label = self.get_remote_label(self.router.name, bounce_fec)
            assert(remote_bounce_label is not None)

            bounce_entry = {"out": self.LOCAL_LOOKUP, "ops": [{"swap" : remote_bounce_label}], "weight" : 1}
            yield (local_label, bounce_entry)


    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)


    def commit_config(self):
        if len(self.demands) == 0:
            return

        arbors = find_partial_arborescences(self.router.network.topology, self.router.name)
        self.arborescences = dag_extension(self.router.network.topology, arbors)

        headends = tuple(set(map(lambda x: x[0], self.demands.values())))

        fec_arbors: list[tuple[oFEC, list[tuple[str, str]]]] =\
            [(oFEC("arborescence", f"{self.router.name}_{i}_{ab}", (self.router.name, i, headends, i == 0 and ab == 'a')), a)
                for ab, (i, a) in itertools.product(['a', 'b'], enumerate(self.arborescences))]

        for i, (fec, a) in enumerate(fec_arbors):
            #assert len(fec_arbors) > 1
            bounce_fec_name = None if i + 1 >= len(fec_arbors) else fec_arbors[i + 1][0].name

            # Loop over all edges in arborescence
            for src, tgt in a:
                # Add an arborescence next-hop for this FEC to the routers in the arborescence
                src_router = self.router.network.routers[src].clients["gft"]
                src_router.arborescence_next_hop[fec.name] = (fec, tgt, bounce_fec_name)
        print()

    def compute_bypasses(self):
        pass

    def LFIB_refine(self, label):
        pass

    def known_resources(self):
        for _, v in self.arborescence_next_hop.items():
            yield v[0]

    def self_sourced(self, fec: oFEC):
        return fec.fec_type == 'gft' and fec.value[0] == self.router.name
