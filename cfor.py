from mpls_classes import *
from functools import *
from networkx import shortest_path

from typing import Dict, Tuple, List

class ForwardingTable:
    def __init__(self):
        self.table: dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]] = {}

    def add_rule(self, key: tuple[str, oFEC], value: tuple[int, str, oFEC]):
        if not self.table.keys().__contains__(key):
            self.table[key] = []
        self.table[key].append(value)


def generate_pseudo_forwarding_table(network: Network, ingress: str, egress: str) -> dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]]:
    def label(switch: str, iteration: int):
        return oFEC("cfor", f"v:{switch}, iter:{iteration}", {"ingress": ingress, "egress": egress, "iteration": iteration})

    edges: set[tuple[str, str]] = set([(n1, n2) for (n1, n2) in network.topology.edges if n1 != n2] \
                                      + [(n2, n1) for (n1, n2) in network.topology.edges if n1 != n2])
    network.compute_dijkstra()
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

            # check if path exists
            path = list(shortest_path(subgraph, v, v_next))
            for k in range(1, len(path)):
                if is_last_switch:
                    if k == len(path)-1:
                        forwarding_table.add_rule((path[k-1], label(v, 1)), (2, path[k], label(path[k], 2)))
                    else:
                        forwarding_table.add_rule((path[k-1], label(v, 1)), (2, path[k], label(v, 1)))
                else:
                    if k == len(path)-1:
                        forwarding_table.add_rule((path[k-1], label(v, 1)), (2, path[k], label(path[k], 1)))
                        forwarding_table.add_rule((path[k-1], label(v, 2)), (2, path[k], label(path[k], 2)))
                    else:
                        forwarding_table.add_rule((path[k-1], label(v, 1)), (2, path[k], label(v, 1)))
                        forwarding_table.add_rule((path[k-1], label(v, 2)), (2, path[k], label(v, 2)))

    return forwarding_table.table


class CFor(MPLS_Client):
    protocol = "cfor"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # Partial forwarding table containing only rules for this router
        self.partial_forwarding_table: dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]] = {}


    def LFIB_compute_entry(self, fec: oFEC, single=False):
        for priority, next_hop, swap_fec in self.partial_forwarding_table[(self.router.name, fec)]:
            local_label = self.get_local_label(fec)
            assert(local_label is not None)

            if fec.value["egress"] == next_hop:
                yield (local_label, {'out': next_hop, 'ops': [{'pop': ''}], 'weight': priority})
            else:
                remote_label = self.get_remote_label(next_hop, swap_fec)
                assert(remote_label is not None)

                yield (local_label, {'out': next_hop, 'ops': [{'swap': remote_label}], 'weight': priority})

    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for demand, (ingress, egress) in self.demands.items():
            ft = generate_pseudo_forwarding_table(self.router.network, ingress, egress)

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
        return fec.fec_type == 'cfor' and fec.value["egress"] == self.router.name
