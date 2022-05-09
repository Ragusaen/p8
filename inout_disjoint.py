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


def generate_pseudo_forwarding_table(network: Network, ingress: [str], egress: str, epochs, flow_max_memory) -> Dict[Tuple[str, oFEC], List[Tuple[int, str, oFEC]]]:
    def label(_ingress, _egress, path_index: int):
        return oFEC("cfor", f"{_ingress}_to_{_egress}_path{path_index}", {"ingress": ingress, "egress": [egress], "iteration": 1, "switch": 1})
    def backtracking_label(_ingress, _egress, path_index: int):
        return oFEC("cfor", f"{_ingress}_to_{_egress}_path{path_index}_backtracking", {"ingress": ingress, "egress": [egress], "iteration": 1, "switch": 1})

    flow_max_memory *= len(ingress)
    router_memory_usage = {r: 0 for r in network.routers}

    forwarding_table = ForwardingTable()
    weight_graph = network.topology.copy()
    ingress_to_paths_dict = {r: [] for r in ingress}
    ingress_index = 0
    ingress_to_path_labels_dict = {r: [] for r in ingress}
    ingress_to_path_backtracking_labels_dict = {r: [] for r in ingress}

    for i in range(epochs):
        if ingress_index == len(ingress):
            ingress_index = 0
        ingress_router = ingress[ingress_index]
        ingress_index += 1

        max_memory_reached = False
        path = nx.dijkstra_path(weight_graph, ingress_router, egress, "weight")
        for r in path:
            if router_memory_usage[r] < flow_max_memory:
                router_memory_usage[r] += 3
            else:
                max_memory_reached = True
                break
        if max_memory_reached:
            break

        if path not in ingress_to_paths_dict[ingress_router]:
            ingress_to_paths_dict[ingress_router].append(path)
        ingress_to_path_labels_dict[ingress_router].append(label(ingress_router, egress, len(ingress_to_paths_dict[ingress_router])))
        ingress_to_path_backtracking_labels_dict[ingress_router].append(backtracking_label(ingress_router, egress, len(ingress_to_paths_dict[ingress_router])))

        update_weights(weight_graph, path)

    for ing in ingress:
        # remove duplictes
        ingress_to_path_labels_dict[ing] = list(dict.fromkeys(ingress_to_path_labels_dict[ing]))
        ingress_to_path_backtracking_labels_dict[ing] = list(dict.fromkeys(ingress_to_path_backtracking_labels_dict[ing]))

        forwarding_table.extend(encode_paths(network.topology, ingress_to_paths_dict[ing], ingress_to_path_labels_dict[ing], ingress_to_path_backtracking_labels_dict[ing]))

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
            G[v1][v2]["weight"] = G[v1][v2]["weight"] * 2 + random.randint(1,10)


def encode_paths(G: Graph, paths: List, path_labels: List, backtracking_path_labels: List):
    ft = ForwardingTable()

    for i, path in enumerate(paths):
        if i > 0:
            ft.add_rule((path[0], backtracking_path_labels[i-1]), (1, path[0], path_labels[i]))

        # for each edge in path
        for s, t in zip(path[:-1], path[1:]):
            # create forwarding using the path label
            ft.add_rule((s, path_labels[i]), (1, t, path_labels[i]))

            # create backtracking
            if i < len(path_labels) - 1:
                # if link failed, bounce to backtracking
                ft.add_rule((s, path_labels[i]), (2, s, backtracking_path_labels[i]))

                if t != path[len(path)-1]:
                    ft.add_rule((t, backtracking_path_labels[i]), (1, s, backtracking_path_labels[i]))

    return ft


class InOutDisjoint(MPLS_Client):
    protocol = "inout-disjoint"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router, **kwargs)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # Partial forwarding table containing only rules for this router
        self.partial_forwarding_table: dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]] = {}

        self.epochs = kwargs['epochs']
        self.max_memory = kwargs['max_memory']

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

        if self.max_memory == 0:
            ft = generate_pseudo_forwarding_table(self.router.network, headends, self.router.name, self.epochs, 100)
        else:
            ft = generate_pseudo_forwarding_table(self.router.network, headends, self.router.name, self.epochs, self.max_memory)

        for (src, fec), entries in ft.items():
            src_client: InOutDisjoint = self.router.network.routers[src].clients["inout-disjoint"]

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
        return 'inout-disjoint' in fec.fec_type and fec.value["egress"][0] == self.router.name
