import queue

import networkx as nx
from networkx import Graph
import matplotlib.pyplot as plt

from mpls_classes import MPLS_Client, Network, oFEC, Router
from target_based_arborescence.arborescences import find_arborescences


def find_distance_edges(network: Network, ingress: str, egress: str) -> list[list[tuple[str, str]]]:
    edges: set[tuple[str, str]] = set([(n1, n2) for (n1, n2) in network.topology.edges if n1 != n2] \
                                      + [(n2, n1) for (n1, n2) in network.topology.edges if n1 != n2])

    layers: list[list] = list(list())  # result

    frontiers: set = set()  # set containing next layer switches
    frontiers.add(egress)  # initialise frontiers to egress, then we traverse the network backwards from there

    i = 0  # number indicating the current layer
    while len(frontiers) != 0:
        layers.append(list())
        next_frontiers: set = set()

        for v in frontiers:
            incoming_edges = set(filter(lambda e: e[1] == v, edges))
            if len(incoming_edges) == 0:
                continue

            # add sources of incoming edges to as next frontiers
            next_frontiers = next_frontiers.union(set(map(lambda e: e[0], incoming_edges)))
            edges = edges - incoming_edges  # we remove already analyzed edges so they are not reconsidered
            layers[i].extend(list(incoming_edges))

        frontiers = next_frontiers.copy()
        i += 1

    # remove last layer if there is no edges in it
    if len(layers[:0]) == 0:
        layers.remove(layers[:0])

    # Ensure switches only have 1 outgoing rule in the same layer
    # We sort layers by source and remove edges if src is same as last element
    new_layers = list(list())
    for layer in layers:
        layer.sort(key=lambda e: e[0])
        fixed_layer = layer.copy()

        last: int = layer[0][0]
        for src2, tgt2 in layer[1:]:
            if last == src2:
                fixed_layer.remove((src2, tgt2))
            else:
                last = src2

        new_layers.append(fixed_layer)
    layers = new_layers.copy()

    # remove edges that have egress switch as src
    new_layers = list(list())
    for layer in layers:
        new_layer = list(filter(lambda e: e[0] != egress, layer))
        new_layers.append(new_layer)
    layers = new_layers.copy()


    # Remove loops
    E: list[tuple[str, str, int]] = []
    for i, layer in enumerate(layers):
        for src, tgt in layer:
            E.append((src, tgt, i))
    V = set([s for s,t in edges] + [t for s,t in edges])

    while True:
        cycles = find_cycles(V, E)
        if len(cycles) == 0:
            break

        demote_or_remove_loops(V, ingress, E, cycles)

    max_layer = max(E, key=lambda x: x[2])[2]
    layers = [[(s,t) for (s,t,lp) in E if lp == l] for l in range(max_layer + 1)]

    return layers


def find_cycles(vertices: set[str], E: list[tuple[str, str, int]]) -> list[list[str]]:
    cycles: list[list[str]] = []

    def DFS_cycle(path: list[str], layer: int):
        for src, tgt, l in E:
            if src == path[-1] and l >= layer - 1:
                if tgt in path:
                    idx = path.index(tgt)
                    cycles.append(path[idx:])
                else:
                    DFS_cycle(path + [tgt], l)

    for v in vertices:
        DFS_cycle([v], 0)

    return cycles

def demote_or_remove_loops(vertices: set[str], ingress: str, E: list[tuple[str, str, int]], cycles: list[list[str]]):
    # Minimum number of failures required to reach this vertex
    min_failure_reach: dict[str, int] = {ingress: 0}

    unfinised = set(vertices)
    while len(unfinised) > 0:
        for v, f_v in min_failure_reach:
            outgoing_edges = [(s,t,l) for s,t,l in E if s == v]
            outgoing_edges.sort(key=lambda x: x[2])

            for f_e, (_, t, _) in enumerate(outgoing_edges):
                if t not in min_failure_reach or f_e + f_v < min_failure_reach[t]:
                    min_failure_reach[t] = f_e + f_v
                    unfinised.add(t)

            unfinised.discard(v)

    # Minimum number of failures required to use this edge
    min_failure_edge: dict[tuple[str, str], int] = {}

    for v in vertices:
        outgoing_edges = [(s, t, l) for s, t, l in E if s == v]
        outgoing_edges.sort(key=lambda x: x[2])

        for f, (s,t,l) in outgoing_edges:
            min_failure_edge[(s,t)] = min_failure_reach[v] + f

    for cycle in cycles:
        # Check that we did not fix this cycle already
        p = cycle[-1]
        cl = 0
        for n in cycle:
            l = [l for s, t, l in E if s == p and t == n][0]
            if not (l >= cl - 1):
                continue
            p = n

        max_fail_edge: tuple[str, str] = (cycle[-1], cycle[0])

        p = cycle[0]
        for n in cycle[1:]:
            if min_failure_edge[(p,n)] > min_failure_edge[max_fail_edge]:
                max_fail_edge = (p,n)
            p = n

        # Remove the edge
        s, t, l = [(s,t,l) for s,t,l in E if s == max_fail_edge[0] and t == max_fail_edge[1]][0]
        E.remove((s,t,l))

        ## Check if we can promote the edge, find the current layer
        # Find the edge after this one in the cycle
        next_target = cycle[(cycle.index(t) + 1) % len(cycle)]
        sn, tn, ln = [(s,t,l) for s,t,l in E if s == t and t == next_target][0]

        # We need to go at least 2 layers above the layer of the next edge in the cycle to break the loop
        pos_layers = [lp + 1 for (sp, tp, lp) in E if sp == t and lp > ln]
        if len(pos_layers) > 0:
            E.append((s,t, pos_layers[0]))


class HopDistance_Client(MPLS_Client):
    protocol = "hop_distance"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # [(headend, [fecs_for_layer_i])]
        self.headend_layers: list[tuple[str, list[oFEC]]] = []

        # The next_hop and next_fec for this router in some FEC (not only those FECs that are tailend here)
        self.fec_to_layer_next_hop: dict[oFEC, str] = {}

    # Abstract functions to be implemented by each client subclass.
    def LFIB_compute_entry(self, fec: oFEC, single=False):
        # TODO: Handle the case when there are multiple next-hops in the same  layer

        for next_hop_fec, next_hop in self.fec_to_layer_next_hop.items():
            if next_hop_fec.value[2] >= fec.value[2] - 1:
                local_label = self.get_local_label(fec)
                remote_label = self.get_remote_label(next_hop, next_hop_fec)
                if next_hop == fec.value[1]:
                    yield (local_label, {"out": next_hop, "ops": [{"pop": ""}], "weight": next_hop_fec.value[2]})
                else:
                    yield (
                    local_label, {"out": next_hop, "ops": [{"swap": remote_label}], "weight": next_hop_fec.value[2]})

    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for _, (ingress, egress) in self.demands.items():
            # Find the distance layers
            distance_edges = find_distance_edges(self.router.network, ingress, egress)

            # Create graph for debugging
            g = nx.DiGraph()
            edge_labels: dict[tuple[str,str], str] = {}

            for i, layer in enumerate(distance_edges):
                g.add_edges_from(layer)
                edge_labels.update({e: str(i) for e in layer})

            pos = nx.planar_layout(g)
            nx.draw_networkx(g, pos)
            nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels)

            plt.title(f"hd_{ingress}_to_{egress}")
            plt.show()

            for i, layer in enumerate(distance_edges):
                # For each layer, create a fec that represents that layer
                layer_fec = oFEC("hop_distance", f"{ingress}_{egress}_d{i}", (ingress, egress, i))

                # Add the next_hop information to the routers involved
                for (src, tgt) in layer:
                    src_router: Router = self.router.network.routers[src]
                    src_client: HopDistance_Client = src_router.clients["hop_distance"]

                    src_client.fec_to_layer_next_hop[layer_fec] = tgt

    def compute_bypasses(self):
        pass

    def LFIB_refine(self, label):
        pass

    def known_resources(self):
        for fec, _ in self.fec_to_layer_next_hop:
            yield fec

    def self_sourced(self, fec: oFEC):
        return fec.fec_type == 'hop_distance' and fec.value[1] == self.router.name
