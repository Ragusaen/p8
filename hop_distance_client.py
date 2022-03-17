from mpls_classes import MPLS_Client, Network, oFEC, Router
from target_based_arborescence.arborescences import find_arborescences


def find_distance_edges(network: Network, ingress: str, egress: str) -> list[list[tuple[str, str]]]:
    pass



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
        pass



    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for _, (ingress, egress) in self.demands:
            # Find the distance layers
            distance_edges = find_distance_edges(self.router.network, ingress, egress)

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

