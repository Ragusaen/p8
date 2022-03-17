import queue

from networkx import Graph

from mpls_classes import MPLS_Client, Network, oFEC, Router
from target_based_arborescence.arborescences import find_arborescences


def find_distance_edges(network: Network, ingress: str, egress: str) -> list[list[tuple[str, str]]]:
    edges: list[tuple[int, int]] = [(n1, n2) for (n1, n2) in network.topology.edges if n1 != n2] \
                                   + [(n2, n1) for (n1, n2) in network.topology.edges if n1 != n2]
    target_switch = network.topology.nodes.get(egress)

    layers: list[list] = list(list)  # result

    frontiers: set = {target_switch}
    i = 0
    while len(frontiers) != 0:
        next_frontiers: set = set()
        for v in frontiers:
            frontiers.remove(v)
            outgoing_edges = list(filter(lambda src, tgt: tgt == v, edges))
            if len(outgoing_edges) == 0:
                continue

            next_frontiers.add(map(lambda x: x.src, outgoing_edges))
            edges -= outgoing_edges
            layers[i].append(outgoing_edges)

        assert len(frontiers) == 0
        frontiers.add(next_frontiers)

    # Ensure switches only have 1 outgoing rule with same layer
    new_layers = list(list)
    for layer in layers:
        layers.sort(key=lambda src, tgt: src)
        fixed_layer = layer.copy()

        last: int = layer[0]
        for src2, tgt2 in layer[1:]:
            if last == src2:
                fixed_layer.remove((src2, tgt2))
            else:
                last = src2
    layers = new_layers

    return layers


class HopDistance_Client(MPLS_Client):

    protocol = "hopdistance"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}


    # Abstract functions to be implemented by each client subclass.
    def LFIB_compute_entry(self, fec: oFEC, single=False):
        pass


    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for _, (ingress, egress) in self.demands:
            find_distance_edges(self.router.network, ingress, egress)
        pass

    def compute_bypasses(self):
        pass

    def LFIB_refine(self, label):
        pass

    def known_resources(self):
        pass

    def self_sourced(self, fec: oFEC):
        pass

