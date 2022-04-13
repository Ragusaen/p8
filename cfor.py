import itertools

import networkx.exception

from mpls_classes import *
from functools import *
from networkx import shortest_path

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


def generate_pseudo_forwarding_table(network: Network, ingress: str, egress: str, path_generator: Callable[[Graph, str, str, oFEC, oFEC], ForwardingTable]) -> Dict[Tuple[str, oFEC], List[Tuple[int, str, oFEC]]]:
    def label(switch: str, iteration: int):
        return oFEC("cfor", f"{ingress}_to_{egress}_at_{switch}_it_{iteration}", {"ingress": ingress, "egress": egress, "iteration": iteration, "switch": switch})


    edges: set[tuple[str, str]] = set([(n1, n2) for (n1, n2) in network.topology.edges if n1 != n2] \
                                      + [(n2, n1) for (n1, n2) in network.topology.edges if n1 != n2])
    network.compute_dijkstra(weight=1)
    layers: dict[int, list[str]] = {layer: [] for layer in range(0, network.routers[ingress].dist[egress] + 1)}

    for v in network.routers.values():
        dist = v.dist[egress]
        if v.dist[egress] <= network.routers[ingress].dist[egress]:
            layers[dist].append(v.name)

    forwarding_table = ForwardingTable()

    for layer in layers.values():
        layer.sort()

    for i in range(1, len(layers)):
        for j in range(0, len(layers[i])):
            v = layers[i][j]
            for v_down in filter(lambda edge: edge[0] == v and edge[1] in layers[i - 1], edges):
                forwarding_table.add_rule((v, label(v, 1)), (1, v_down[1], label(v_down[1], 1)))
                forwarding_table.add_rule((v, label(v, 2)), (1, v_down[1], label(v_down[1], 1)))

            subtract_switches = set()
            for k in range(0, i):
                subtract_switches = subtract_switches.union(set(layers[k]))
            subgraph_switches = set(network.topology.nodes).difference(subtract_switches)

            is_last_switch = v == layers[i][-1]
            v_next = layers[i][0]
            if not is_last_switch:
                v_next = layers[i][j+1]

            subgraph = network.topology.subgraph(subgraph_switches)

            if not is_last_switch:
                sub_ft = path_generator(subgraph, v, v_next, label(v, 1), label(v_next, 1))
                sub_ft.extend(path_generator(subgraph, v, v_next, label(v, 2), label(v_next, 2)))
            else:
                sub_ft = path_generator(subgraph, v, v_next, label(v, 1), label(v_next, 2))

            forwarding_table.extend(sub_ft)


    return forwarding_table.table

def shortest_path_generator(G: Graph, src: str, tgt: str, ingoing_label, outgoing_label):
    ft = ForwardingTable()
    if src == tgt:
        return ft

    try:
        path = list(shortest_path(G, src, tgt, weight=1))
    except networkx.exception.NetworkXNoPath:
        return ft

    for src, tgt in zip(path[:-2], path[1:-1]):
        ft.add_rule((src, ingoing_label), (2, tgt, ingoing_label))

    src, tgt = path[-2:]
    ft.add_rule((src, ingoing_label), (2, tgt, outgoing_label))
    return ft

def arborescence_path_generator(G: Graph, src: str, tgt: str, ingoing_label: oFEC, outgoing_label: oFEC):
    from target_based_arborescence.arborescences import find_arborescences

    ft = ForwardingTable()
    arborescences = find_arborescences(G, tgt)

    if src == tgt or len(arborescences) < 1:
        return ft

    fec_arbs = [(oFEC('cfor_arb', ingoing_label.name + f"_to_{tgt}_arb{i}{ab}", {'egress':ingoing_label.value['egress']}), a) for ab, (i, a)  in itertools.product(['a', 'b'], enumerate(arborescences))]

    # Create ingoing local lookup rule
    ft.add_rule((src, ingoing_label), (2, src, fec_arbs[0][0]))

    for i, (fec, a) in enumerate(fec_arbs):
        bounce_fec = None if i >= len(fec_arbs) - 1 else fec_arbs[i + 1][0]

        # Add outgoing local lookup rules
        ft.add_rule((tgt, fec), (0, tgt, outgoing_label))

        for s, t in a:
            ft.add_rule((s, fec), (1, t, fec))
            if bounce_fec is not None:
                ft.add_rule((s, fec), (2, s, bounce_fec))

    return ft


class CFor(MPLS_Client):
    protocol = "cfor"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # Partial forwarding table containing only rules for this router
        self.partial_forwarding_table: dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]] = {}

        self.path_generator = {
            'shortest': shortest_path_generator,
            'arborescence': arborescence_path_generator
        }[kwargs['path_generator']]


    def LFIB_compute_entry(self, fec: oFEC, single=False):
        for priority, next_hop, swap_fec in self.partial_forwarding_table[(self.router.name, fec)]:
            local_label = self.get_local_label(fec)
            assert(local_label is not None)

            if fec.value["egress"] == next_hop:
                yield (local_label, {'out': next_hop, 'ops': [{'pop': ''}], 'weight': priority})
            else:
                remote_label = self.get_remote_label(next_hop, swap_fec)
                assert(remote_label is not None)

                yield (local_label, {'out': next_hop if next_hop != self.router.name else self.LOCAL_LOOKUP, 'ops': [{'swap': remote_label}], 'weight': priority})

    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for demand, (ingress, egress) in self.demands.items():
            ft = generate_pseudo_forwarding_table(self.router.network, ingress, egress, self.path_generator)

            for (src, fec), entries in ft.items():
                src_client: CFor = self.router.network.routers[src].clients["cfor"]

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
        return 'cfor' in fec.fec_type and fec.value["egress"] == self.router.name
