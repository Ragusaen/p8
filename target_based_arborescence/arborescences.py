from mpls_classes import Network
import networkx as nx


def find_arborescences(network: Network, egress: str) -> list[list[tuple[str, str]]]:
    edges: list[tuple[str, str]] = [(n1, n2) for (n1, n2) in network.topology.edges if n1 != n2] \
                                   + [(n2, n1) for (n1, n2) in network.topology.edges if n1 != n2]

    # Find median of linked edges on routers - Placeholder to find amount of arborescences
    router_link_amount = [len([(n1,n2) for (n1,n2) in edges if n1 == router]) for router in network.routers]
    router_link_amount.sort()
    arborescence_to_find = router_link_amount[len(router_link_amount) // 2]

    edge_to_num_arborescence_appearance = {e: 0 for e in edges}

    arborescence_to_edges = [[] for _ in range(arborescence_to_find)]
    arborescence_to_nodes = [[egress] for _ in range(arborescence_to_find)]
    arborescence_to_edges_to_consider = [[(n1, n2) for (n1, n2) in edges if n2 == egress] for _ in range(arborescence_to_find)]


    for step in range(len(network.topology.nodes) - 1):
        for arborescence in range(arborescence_to_find):
            appearances = {e: edge_to_num_arborescence_appearance[e] for e in arborescence_to_edges_to_consider[arborescence]}
            least_used_edge = min(appearances, key=appearances.get)

            arborescence_to_edges[arborescence].append(least_used_edge)
            arborescence_to_nodes[arborescence].append(least_used_edge[0])
            edge_to_num_arborescence_appearance[least_used_edge] = edge_to_num_arborescence_appearance[least_used_edge] + 1

            new_edges_to_consider = [(n1,n2) for (n1,n2) in edges if n2 == least_used_edge[0] and n1 not in arborescence_to_nodes[arborescence]]
            arborescence_to_edges_to_consider[arborescence].extend(new_edges_to_consider)
            arborescence_to_edges_to_consider[arborescence] = [(n1,n2) for (n1,n2) in arborescence_to_edges_to_consider[arborescence] if n1 not in arborescence_to_nodes[arborescence]]
    return arborescence_to_edges
