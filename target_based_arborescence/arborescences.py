from mpls_classes import Network
import networkx as nx


def find_arborescences(network: Network, ingress: list[str], egress: str) -> list[list[tuple[str, str]]]:
    arborescences = list()

    # Find median of linked edges on routers - Placeholder to find amount of arborescences
    router_link_amount = [len(network.topology.edges(router)) for router in network.routers]
    router_link_amount.sort()
    arborescence_to_find = router_link_amount[len(router_link_amount) // 2]

    edges = []
    for (n1,n2) in network.topology.edges:
        edges.append((n1,n2))
        edges.append((n2,n1))

    edge_to_num_arborescence_appearance = {e: 0 for e in edges}
    node_to_neighbors = {n: network.topology.neighbors(n) for n in network.topology.nodes}

    arborescence_to_edges = [[] for _ in range(arborescence_to_find)]
    arborescence_to_nodes = [[] for _ in range(arborescence_to_find)]
    arborescence_to_edges_to_consider = [[(n1, n2) for (n1, n2) in edges if n2 == egress] for _ in range(arborescence_to_find)]


    for step in range(len(network.topology.nodes) - 1):
        for arborescence in range(arborescence_to_find):
            appearances = {e: edge_to_num_arborescence_appearance[e] for e in arborescence_to_edges_to_consider[arborescence]}
            least_used_edge = min(appearances, key=appearances.get)
            arborescence_to_edges[arborescence].append(least_used_edge)
            arborescence_to_nodes[arborescence].append(least_used_edge[1])
            edge_to_num_arborescence_appearance[least_used_edge] = edge_to_num_arborescence_appearance[least_used_edge] + 1
            new_edges_to_consider = [(n1,n2) for (n1,n2) in edges if n2 == least_used_edge[0] and n1 not in arborescence_to_nodes[arborescence]]
            arborescence_to_edges_to_consider[arborescence].extend(new_edges_to_consider)

    return arborescence_to_edges
