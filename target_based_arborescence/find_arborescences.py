from mpls_fwd_gen import Network
import networkx as nx

def find_arborescences(network: Network, ingress: list[str], egress: str) -> list[list[tuple[str, str]]]:
    arborescences = list()

    #Find median of linked edges on routers - Placeholder to find amount of arborescences
    router_link_amount = [len(network.topology.edges(router)) for router in network.routers]
    router_link_amount.sort()
    arborescence_to_find = router_link_amount[len(router_link_amount) // 2]

    edge_to_num_arborescence_appearance = {e:0 for e in network.topology.edges}
    node_to_neighbors = {n: network.topology.neighbors(n) for n in network.topology.nodes}

    for arbor in range(arborescence_to_find):
        arborescence = []
        nodes_used_in_arborescence = []

        for i in range(len(network.routers) - 1):
            #Only considered != egress and nodes not already in current arborescence
            restricted_node_to_neighbors = {node:n for node, n in node_to_neighbors.items() if node not in nodes_used_in_arborescence and node != egress}
            node_with_fewest_neighbors = min(restricted_node_to_neighbors, key=len)
    
            #Find least used outgoing edge
            used_edge_out = {(n1,n2):n for (n1,n2), n in edge_to_num_arborescence_appearance.items() if n1 == node_with_fewest_neighbors}
            least_used_edge_out = min(used_edge_out, key=used_edge_out.get)

            arborescence.append(least_used_edge_out)

        arborescences.append(arborescence)

    return arborescences