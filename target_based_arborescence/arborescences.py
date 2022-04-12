from mpls_classes import Network
import networkx as nx
from typing import Dict, List, Tuple, Set

def create_arborescence(edges: List[Tuple[str, str]], vertices: Set[str], egress: str, edge_to_count):
    arborescence = []

    nodes_used_distance = {egress: 0}

    for _ in range(len(vertices) - 1):
        # Best edge by the heuristic: Sort by longest subtree then by least used edge
        edges_by_heuristic = sorted(filter(lambda e: e[0] not in nodes_used_distance and e[1] in nodes_used_distance, edges),
                                    key=lambda e: (-nodes_used_distance[e[1]], edge_to_count[e]))

        for src, tgt in edges_by_heuristic:
            arborescence.append((src,tgt))
            edge_to_count[(src, tgt)] += 1
            nodes_used_distance[src] = nodes_used_distance[tgt] + 1
            break
    return arborescence

def find_arborescences(network: Network, egress: str) -> List[List[Tuple[str, str]]]:
    edges: list[tuple[str, str]] = [(n1, n2) for (n1, n2) in network.topology.edges if n1 != n2] \
                                   + [(n2, n1) for (n1, n2) in network.topology.edges if n1 != n2]
    vertices = { v for v, _ in edges }

    # Find median of linked edges on routers - Placeholder to find amount of arborescences
    router_link_amount = [len([(n1,n2) for (n1,n2) in edges if n1 == router]) for router in network.routers]
    router_link_amount.sort()
    arborescences_to_find = router_link_amount[-1]#[len(router_link_amount) // 2]

    edge_to_count = {e: 0 for e in edges}

    return [create_arborescence(edges, vertices, egress, edge_to_count) for _ in range(arborescences_to_find)]
