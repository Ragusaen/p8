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


def generate_pseudo_forwarding_table(network: Network, flows: List[Tuple[str, str]], epochs: int, total_max_memory: int) -> Dict[
    Tuple[str, oFEC], List[Tuple[int, str, oFEC]]]:
    def label(_ingress, _egress, path_index: int):
        return oFEC("inout-disjoint", f"{_ingress}_to_{_egress}_path{path_index}",
                    {"ingress": _ingress, "egress": [_egress], "path_index": path_index})

    def compute_memory_usage(ing_to_paths_dict) -> Dict:
        memory_usage = {r: 0 for r in network.routers}

        for _, paths in ing_to_paths_dict.items():
            for i, path in enumerate(paths):
                is_last_path = i == (len(paths) - 1)

                # for each edge in path
                for s, t in zip(path[:-1], path[1:]):
                    # create simple forwarding using the path label
                    memory_usage[s] += 1

                    # handle bouncing to next path
                    if not is_last_path:
                        memory_usage[s] += 1

                        # create backtracking rules for next subpath
                        if t not in paths[i + 1]:
                            memory_usage[t] += 1

        return memory_usage

    forwarding_table = ForwardingTable()
    flow_to_paths_dict = {f: [] for f in flows}
    flow_to_path_labels_dict = {f: [] for f in flows}
    flow_to_weight_graph_dict = {f: network.topology.copy().to_directed() for f in flows}

    for _, weighted_graph in flow_to_weight_graph_dict.items():
        reset_weights(weighted_graph, 0)

    for i in range(epochs):
        # select the next ingress router to even out memory usage
        flow = flows[i % len(flows)]
        ingress_router, egress_router = flow

        path = nx.dijkstra_path(flow_to_weight_graph_dict[flow], ingress_router, egress_router, weight="weight")

        try_paths = {}
        for f, paths in flow_to_paths_dict.items():
            try_paths[f] = paths.copy()
            if f == flow:
                if path not in try_paths[f]:
                    try_paths[f].append(path)

        # see if adding this path surpasses the the memory limit
        router_memory_usage = compute_memory_usage(try_paths)
        max_memory_reached = True in [False if router_memory_usage[r] <= total_max_memory else True for r in path]

        # update weights in the network to change the shortest path
        update_weights(flow_to_weight_graph_dict[flow], path)

        # if path violates memory limit, do not add it
        if max_memory_reached:
            continue

        if path not in flow_to_paths_dict[flow]:
            flow_to_paths_dict[flow].append(path)
        flow_to_path_labels_dict[flow].append(
            label(ingress_router, egress_router, len(flow_to_paths_dict[flow])))

    for f in flows:
        # remove duplicate labels
        flow_to_path_labels_dict[f] = list(dict.fromkeys(flow_to_path_labels_dict[f]))
        forwarding_table.extend(
            encode_paths_quick_next_path(flow_to_paths_dict[f], flow_to_path_labels_dict[f]))

    return forwarding_table.table


def reset_weights(G: Graph, value):
    for u, v, d in G.edges(data=True):
        d["weight"] = value


def update_weights(G: Graph, path):
    for v1, v2 in zip(path[:-1], path[1:]):
        weight = G[v1][v2]["weight"]

        if weight <= 0:
            G[v1][v2]["weight"] = 1
        else:
            G[v1][v2]["weight"] = G[v1][v2]["weight"] * 2 + random.randint(1, 10)


def encode_paths_full_backtrack(paths: List, path_labels: List, backtracking_path_labels: List):
    ft = ForwardingTable()

    for i, path in enumerate(paths):
        if i > 0:
            ft.add_rule((path[0], backtracking_path_labels[i - 1]), (1, path[1], path_labels[i]))

        # for each edge in path
        for s, t in zip(path[:-1], path[1:]):
            if s == path[0]:
                # create forwarding using the path label
                ft.add_rule((s, path_labels[i]), (1, t, path_labels[i]))

            # create backtracking
            if i < len(paths) - 1:
                # if link failed, bounce to backtracking
                ft.add_rule((s, path_labels[i]), (2, s, backtracking_path_labels[i]))

                if t != path[len(path) - 1]:
                    ft.add_rule((t, backtracking_path_labels[i]), (1, s, backtracking_path_labels[i]))

    return ft


def encode_paths_quick_next_path(paths: List, path_labels: List):
    ft = ForwardingTable()

    for i, path in enumerate(paths):
        is_last_path = i == (len(paths) - 1)

        # for each edge in path
        for s, t in zip(path[:-1], path[1:]):
            # create simple forwarding using the path label
            ft.add_rule((s, path_labels[i]), (1, t, path_labels[i]))

            # handle bouncing to next path
            if not is_last_path:
                ft.add_rule((s, path_labels[i]), (2, s, path_labels[i + 1]))

                # create backtracking rules for next subpath
                if t not in paths[i + 1]:
                    ft.add_rule((t, path_labels[i + 1]), (1, s, path_labels[i + 1]))

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
        self.per_flow_memory = kwargs['per_flow_memory']

    def LFIB_compute_entry(self, fec: oFEC, single=False):
        for priority, next_hop, swap_fec in self.partial_forwarding_table[(self.router.name, fec)]:
            local_label = self.get_local_label(fec)
            assert (local_label is not None)

            if next_hop in fec.value["egress"]:
                yield (local_label, {'out': next_hop, 'ops': [{'pop': ''}], 'weight': priority})
            else:
                remote_label = self.get_remote_label(next_hop, swap_fec)
                assert (remote_label is not None)

                yield (local_label, {'out': next_hop if next_hop != self.router.name else self.LOCAL_LOOKUP,
                                     'ops': [{'swap': remote_label}], 'weight': priority})

    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        # Only one router should generate dataplane!
        if self.router.name != min(rname for rname in self.router.network.routers):
            return

        network = self.router.network

        flows = [(headend, tailend) for tailend in network.routers for headend in map(lambda x: x[0], network.routers[tailend].clients[self.protocol].demands.values())]

        ft = generate_pseudo_forwarding_table(self.router.network, flows, self.epochs, self.per_flow_memory * len(flows))

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
