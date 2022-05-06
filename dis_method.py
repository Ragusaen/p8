import itertools

import networkx.exception

from mpls_classes import *
from functools import *
from networkx import shortest_path
import networkx as nx

from itertools import islice

from typing import Dict, Tuple, List, Callable


class ForwardingTable:
    def __init__(self):
        self.table: dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]] = {}

    def add_rule(self, key: Tuple[str, oFEC], value: Tuple[int, str, oFEC]):
        if not self.table.keys().__contains__(key):
            self.table[key] = []
        self.table[key].append(value)

    def extend(self, other):
        for lhs, rhs_list in other.table.items():
            for rhs in rhs_list:
                self.add_rule(lhs, rhs)


def generate_pseudo_forwarding_table(network: Network, ingress: [str], egress: str, epochs, num_paths) -> Dict[Tuple[str, oFEC], List[Tuple[int, str, oFEC]]]:
    def label(_ingress, _egress, path_index: int):
        return oFEC("cfor", f"{_ingress}_to_{_egress}_{path_index}", {"ingress": ingress, "egress": [egress], "iteration": 1, "switch": 1})

    forwarding_table = ForwardingTable()

    for ing in ingress:
        weight_graph = network.topology.copy()
        reset_weights(weight_graph, 0)
        paths = []

        for i in range(epochs):
            path = nx.single_source_bellman_ford(weight_graph, ing, egress, "weight")[1]
            if path not in paths:
                paths.append(path)
            if len(path) == num_paths:
                break
            update_weights(weight_graph, path)

        path_labels = []
        for l in range(len(paths)):
            path_labels.append(label(ing, egress, l))
        forwarding_table.extend(encode_paths(weight_graph, paths, path_labels))

    return forwarding_table.table


def reset_weights(G: Graph, value):
    for u, v, d in G.edges(data=True):
        d["weight"] = value


def update_weights(G: Graph, path):
    for v1, v2 in zip(path[:-1], path[1:]):
        weight = G[v1][v2]["weight"]

        if weight == 0:
            G[v1][v2]["weight"] = 100000
        else:
            G[v1][v2]["weight"] = G[v1][v2]["weight"] * 2 + 1


def encode_paths(G: Graph, paths: List, path_labels):
    ft = ForwardingTable()

    for i, path in enumerate(paths):
        # for each edge in path
        for s, t in zip(path[:-1], path[1:]):
            # create forwarding using the path label
            ft.add_rule((s, path_labels[i]), (1, t, path_labels[i]))

            # if not last subpath
            if i < len(path_labels) - 1:
                # if link failed, bounce to next subpath
                ft.add_rule((s, path_labels[i]), (2, s, path_labels[i+1]))

                # create backtracking rules for next subpath
                if t not in paths[i+1]:
                    ft.add_rule((t, path_labels[i+1]), (1, s, path_labels[i+1]))

    return ft


class InOutDisjoint(MPLS_Client):
    protocol = "in-out-disjoint"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router, **kwargs)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # Partial forwarding table containing only rules for this router
        self.partial_forwarding_table: dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]] = {}

        self.num_paths = kwargs['num_paths']
        self.epochs = kwargs['epochs']

    def LFIB_compute_entry(self, fec: oFEC, single=False):
        for priority, next_hop, swap_fec in self.partial_forwarding_table[(self.router.name, fec)]:
            local_label = self.get_local_label(fec)
            assert(local_label is not None)

            if next_hop in fec.value["egress"]:
                yield (local_label, {'out': next_hop, 'ops': [{'pop': ''}], 'weight': priority})
            else:
                remote_label = self.get_remote_label(next_hop, swap_fec)
                assert(remote_label is not None)

                yield (local_label, {'out': next_hop if next_hop != self.router.name else self.LOCAL_LOOKUP, 'ops': [{'swap': remote_label}], 'weight': priority})

    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        headends = list(map(lambda x: x[0], self.demands.values()))
        if len(headends) == 0:
            return
        ft = generate_pseudo_forwarding_table(self.router.network, headends, self.router.name, self.epochs, self.num_paths)

        for (src, fec), entries in ft.items():
            src_client: InOutDisjoint = self.router.network.routers[src].clients["cfor"]

            if (src, fec) not in src_client.partial_forwarding_table:
                src_client.partial_forwarding_table[(src, fec)] = []

            src_client.partial_forwarding_table[(src, fec)].extend(entries)

    def compute_bypasses(self):
        pass

    def LFIB_refine(self, label):
        pass

    def known_resources(self):
        for _, fec in self.partial_forwarding_table.keys():
            yield fec

    def self_sourced(self, fec: oFEC):
        return 'cfor' in fec.fec_type and fec.value["egress"][0] == self.router.name
