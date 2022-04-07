from mpls_classes import *


class ForwardingTable:
    table = dict[tuple[str, oFEC], list[tuple[int, str, oFEC]]]

    def add_rule(self, index: tuple[str, oFEC], to: tuple[int, str, oFEC]):
        pass
        # if list doesnt exists create it


def generate_pseudo_forwarding_table(network: Network, ingress: str, egress: str) -> ForwardingTable:
    network.compute_dijkstra()
    layers: dict[int, list[str]] = {layer: [] for layer in range(0, network.routers[ingress].dist[egress] + 1)}

    for v in network.routers.values():
        dist = v.dist[egress]
        if v.dist[egress] <= network.routers[ingress].dist[egress]:
            layers[dist].append(v.name)

    forwarding_table = ForwardingTable()
    first_it_labels: dict[int, oFEC] = dict()
    second_it_labels: dict[int, oFEC] = dict()

    for j in range(1, len(layers)):
        first_it_labels[j] = oFEC("type1", "dist-{j}-iter-1")
        second_it_labels[j] = oFEC("type1", "dist-{j}-iter-2")
        for v in layers[j]:
            for v_down in filter(lambda x: x[0] == v and x[1] in layers[j - 1], network.topology.edges):
                forwarding_table[v, first_it_labels[j]].append((1, v_down, first_it_labels[j - 1]))
                forwarding_table[v, second_it_labels[j]].append((1, v_down, second_it_labels[j - 1]))


class CFor(MPLS_Client):
    protocol = "cfor"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # [(headend, [fecs_for_layer_i])]
        self.headend_layers: list[tuple[str, list[oFEC]]] = []

        # Incoming FECs
        self.incoming_fecs: list[oFEC] = []

        # The next_hop and next_fec for this router in some FEC (not only those FECs that are tailend here)
        self.demand_fec_layer_next_hop: dict[str, dict[oFEC, str]] = {}

    # Abstract functions to be implemented by each client subclass.
    def LFIB_compute_entry(self, fec: oFEC, single=False):
        pass  # TODO

    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for demand, (ingress, egress) in self.demands.items():
            generate_pseudo_forwarding_table(self.router.network, ingress, egress)

    def compute_bypasses(self):
        pass

    def LFIB_refine(self, label):
        pass

    def known_resources(self):
        for _, fec_dict in self.demand_fec_layer_next_hop.items():
            for fec, _ in fec_dict.items():
                yield fec
        for fec in self.incoming_fecs:
            yield fec

    def self_sourced(self, fec: oFEC):
        return fec.fec_type == 'hop_distance' and fec.value[0] == self.router.name
