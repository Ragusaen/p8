import itertools

import networkx.exception

from mpls_classes import *
from functools import *
from networkx import shortest_path
from cfor import ForwardingTable

from typing import Dict, Tuple, List, Callable


def build_kf_traversal(network: Network) -> Dict[str, str]:
    G: nx.DiGraph = network.topology.copy().to_directed()
    used_nodes = set()

    def cycle(start: str, current: str, depth: int):
        used_nodes.add(current)
        if start == current and depth > 0:
            return []

        next = sorted(list(G.neighbors(current)), key=lambda x: 1 if x in used_nodes else 0)[0]
        return [(current, next)] + cycle(start, next, depth + 1)

    s = list(G.nodes())[0]
    traversal = [s]
    while len(used_nodes) != G.number_of_nodes():
        c = cycle(s, s, 0)

        subtraversal = [t for _,t in c]
        i = traversal.index(s)
        traversal = traversal[:i+1] + subtraversal + traversal[i+1:]

        G.remove_edges_from(c)

        # Find next node s.t. it has a remaining edge
        for n in used_nodes:
            if len(list(G.neighbors(n))) != 0:
                s = n
                break
        else:
            assert(len(used_nodes) == G.number_of_nodes())

    trav_dict = {s: t for s,t in zip(traversal[:-1], traversal[1:])}
    return trav_dict


def generate_pseudo_forwarding_table(network: Network, ingress: str, egress: str) -> Dict[Tuple[str, oFEC], List[Tuple[int, str, oFEC]]]:
    router_to_label = {r: oFEC('kf', f'{ingress}_to_{egress}_last_at_{r}', {'egress': egress, 'ingress': ingress}) for r in network.routers.keys()}

    edges: set[tuple[str, str]] = set([(n1, n2) for (n1, n2) in network.topology.edges if n1 != n2] \
                                      + [(n2, n1) for (n1, n2) in network.topology.edges if n1 != n2])
    network.compute_dijkstra(weight=1)
    D: dict[str, int] = {r: network.routers[r].dist[egress] for r in network.routers.keys()}

    kf_traversal = build_kf_traversal(network)

    def true_sink(e: tuple[str, str]):
        v, u = e
        u_degree = network.topology.degree[u]
        if u_degree > 2:
            return u
        elif u_degree == 2:
            u_edges = list(network.topology.edges(u))
            return true_sink([(s,t) for s,t in u_edges if t != v][0])
        else:
            return v

    ft = ForwardingTable()

    for src, tgt in edges:
        if tgt == egress or src == egress:
            continue

        priority = 0
        def add_ordered_rules(edges: List[Tuple[str, str]]):
            nonlocal priority
            edges.sort(key=lambda x: network.topology.degree[x[1]], reverse=True)

            for _, t in edges:
                ft.add_rule((tgt, router_to_label[src]), (priority, t, router_to_label[tgt]))
                priority = priority + 1

        out_edges = [(s,t) for s,t in edges if s == tgt]
        if D[src] > D[tgt]:
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] < D[s]])
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] == D[s] and tgt != t])
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] > D[s] and true_sink((s,t)) != true_sink((src, tgt))])
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] > D[s] and network.topology.degree[t] > 2])
        elif D[src] < D[tgt]:
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] < D[s] and true_sink((s,t)) != true_sink((src, tgt))])
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] == D[s] and tgt != t])
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] > D[s]])
        else:
            add_ordered_rules([(s,t) for s,t in out_edges if D[t] < D[s]])

            ft.add_rule((tgt, router_to_label[src]), (priority, kf_traversal[tgt], router_to_label[tgt]))

            add_ordered_rules([(s,t) for s,t in out_edges if D[t] > D[s]])

        ft.add_rule((tgt, router_to_label[src]), (priority, src, router_to_label[tgt]))

    return ft.table


class KeepForwarding(MPLS_Client):
    protocol = "kf"

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

                yield (local_label, {'out': next_hop if next_hop != self.router.name else self.LOCAL_LOOKUP, 'ops': [{'swap': remote_label}], 'weight': priority})

    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for demand, (ingress, egress) in self.demands.items():
            ft = generate_pseudo_forwarding_table(self.router.network, ingress, egress)

            for (src, fec), entries in ft.items():
                src_client: KeepForwarding = self.router.network.routers[src].clients["kf"]

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
        return 'kf' in fec.fec_type and fec.value["egress"] == self.router.name
