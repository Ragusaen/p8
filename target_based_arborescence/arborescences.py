import heapq

from networkx import Graph, DiGraph

from mpls_classes import Network
import networkx as nx
from typing import Dict, List, Tuple, Set


def has_cycle(current: str, sg: List[Tuple[str, str]], found: Set[str]):
    found.add(current)
    next = [t for s, t, _ in sg if s == current]

    for n in next:
        if n in found or has_cycle(n, sg, found.copy()):
            return True
    return False


def create_arborescence(edges: List[Tuple[str, str]], vertices: Set[str], egress: str,
                        edge_to_count: Dict[Tuple[str, str], int]):
    arborescence = []

    nodes_used_distance = {egress: 0}

    for _ in range(len(vertices) - 1):
        # Best edge by the heuristic: Sort by longest subtree then by least used edge
        edges_by_heuristic = sorted(
            filter(lambda e: e[0] not in nodes_used_distance and e[1] in nodes_used_distance, edges),
            key=lambda e: (edge_to_count[e], -nodes_used_distance[e[1]]))
        for src, tgt in edges_by_heuristic:
            arborescence.append((src, tgt, 2))
            edge_to_count[(src, tgt)] += 1
            nodes_used_distance[src] = nodes_used_distance[tgt] + 1
            break

    # Add single hop short-cuts
    for s, t in edges:
        ea = arborescence + [(s, t, 1)]
        if (s, t, 2) not in arborescence and any(tp == t for _, tp, _ in arborescence) and not any(
                has_cycle(v, ea, set()) for v in vertices):
            arborescence = ea
            # edge_to_count[(s,t)] += 1

    return arborescence


def create_sub_arborescences(edges: List[Tuple[str, str]], vertices: Set[str], egress: str,
                             edge_to_count: Dict[Tuple[str, str], int]):
    arborescence = []

    unused_edges = list(filter(lambda e: edge_to_count[e] == 0 and e[0] != egress, edges))

    for s, t in unused_edges:
        ea = arborescence + [(s, t, 2)]
        if not any(has_cycle(v, ea, set()) for v in vertices):
            arborescence = ea
            edge_to_count[(s, t)] += 1

    assert (len(arborescence) > 0)
    return arborescence


def find_arborescences(graph: Graph, egress: str) -> List[List[Tuple[str, str, int]]]:
    edges: list[tuple[str, str]] = [(n1, n2) for (n1, n2) in graph.edges if n1 != n2] \
                                   + [(n2, n1) for (n1, n2) in graph.edges if n1 != n2]
    vertices = {v for v, _ in edges}

    # Find median of linked edges on routers - Placeholder to find amount of arborescences
    router_link_amount = [len([(n1, n2) for (n1, n2) in edges if n1 == router]) for router in graph.nodes]
    router_link_amount.sort()
    arborescences_to_find = router_link_amount[-1]  # graph.degree(egress)#[len(router_link_amount) // 2]

    edge_to_count = {e: 0 for e in edges}

    arborescences = [create_arborescence(edges, vertices, egress, edge_to_count) for _ in range(arborescences_to_find)]

    edge_to_count = {e: 0 for e in edges}
    for s, t, _ in [e for l in arborescences for e in l]:
        edge_to_count[(s, t)] += 1

    while any(c == 0 for (s, t), c in edge_to_count.items() if s != egress):
        arborescences.append(create_sub_arborescences(edges, vertices, egress, edge_to_count))

    return arborescences


def create_least_used_arborescence(graph: Graph, egress: str, edge_to_count: Dict[Tuple[str, str], int]) -> List[
    Tuple[str, str, int]]:
    arborescence = nx.DiGraph()
    arborescence.add_nodes_from(graph.nodes)

    nodes_in_arborescence = {egress}

    inf = 1_000_000_000

    arb_node_distance = {v: inf for v in graph.nodes}
    arb_node_distance[egress] = 0

    # Possible traversal subgraph, a graph that contains those edges that could possibly be traversed with arborescence
    # i.e., those that are already in arborescence or it is not outgoing from a node in the arborescence
    subgraph: DiGraph = graph.to_directed()

    def h(e):
        return (-arb_node_distance[e[1]], edge_to_count[e], edge_to_count[(e[1], e[0])])

    unused_edges = list(map(lambda ec: (h(ec[0]), ec[0]), filter(lambda x: x[1] == 0, edge_to_count.items())))
    heapq.heapify(unused_edges)

    def try_add_edge(s: str, t: str):
        nonlocal subgraph
        nonlocal unused_edges
        # Try to add this edge
        new_subgraph = subgraph.copy()
        new_subgraph.remove_edges_from(list(filter(lambda e: e[1] != t, new_subgraph.out_edges(s))))

        try:
            has_path = nx.has_path(new_subgraph, s, egress)
        except:
            has_path = False

        # If there is a path then add this edge
        if has_path:
            subgraph = new_subgraph
            arborescence.add_edge(s, t, weight=2)
            nodes_in_arborescence.add(s)

            try:
                arb_node_distance[s] = nx.shortest_path_length(arborescence, s, egress, weight=1)
            except:
                arb_node_distance[s] = inf

            edge_to_count[(s, t)] += 1
            return True
        return False

    # Try to add as many unused edges as possible, prioritise those that go to a node already in arborescence
    while len(unused_edges) > 0:
        _, (s, t) = heapq.heappop(unused_edges)

        # Check that this node is not already in arborescence
        if s not in nodes_in_arborescence:
            # Try to add this edge
            if try_add_edge(s, t):
                # update heap
                unused_edges = [(h(e), e) for _, e in unused_edges]
                heapq.heapify(unused_edges)

    # If we could not add any proper edges, just give up
    if len(arborescence.edges) == 0:
        return []

    # Stitch rest of arborescence together
    nodes_not_in_arborescence = set(graph.nodes()) - nodes_in_arborescence

    for v in nodes_not_in_arborescence:
        edges_by_heuristic = sorted(subgraph.edges(v), key=h)
        for s, t in edges_by_heuristic:
            if try_add_edge(s, t):
                break

    # Add short-cuts, i.e. single hop paths (edges) between two points in the arborescence
    for e in graph.edges:
        if e[0] != egress and e not in arborescence.edges and nx.has_path(arborescence, e[0], e[1]):
            arborescence.add_edge(e[0], e[1], weight=1)

            if not nx.is_directed_acyclic_graph(arborescence):
                arborescence.remove_edge(e[0], e[1])
            else:
                edge_to_count[e] += 1

    return [(s, t, arborescence[s][t]['weight']) for s, t in arborescence.edges]


def complex_find_arborescence(graph: Graph, egress: str) -> List[List[Tuple[str, str, int]]]:
    arborescences = []
    edge_to_count = {e: 0 for e in graph.to_directed().edges}

    while True:
        a = create_least_used_arborescence(graph, egress, edge_to_count)
        if len(a) == 0:
            break
        arborescences.append(a)

    return arborescences
