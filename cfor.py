from mpls_classes import *
from typing import Dict, Tuple, List

#import nimporter
#import nim_test

ForwardingTable = Dict[Tuple[str, oFEC], List[Tuple[int, str, oFEC]]]

def generate_pseudo_forwarding_table(network: Network, ingress: str, egress: str) -> ForwardingTable:
    pass



class CFor(MPLS_Client):
    protocol = "cfor"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # Partial forwarding table containing only rules for this router
        self.partial_forwarding_table: ForwardingTable = {}


    def LFIB_compute_entry(self, fec: oFEC, single=False):
        for priority, next_hop, swap_fec in self.partial_forwarding_table[(self.router.name, fec)]:
            local_label = self.get_local_label(fec)
            remote_label = self.get_remote_label(next_hop, swap_fec)
            assert(local_label is not None)
            assert(remote_label is not None)

            yield (local_label, {'out': next_hop, 'ops': [{'swap': remote_label}], 'weight': priority})



    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        for demand, (ingress, egress) in self.demands.items():
            ft = generate_pseudo_forwarding_table(self.router.network, ingress, egress)

            for (src, fec), entries in ft.items():
                src_client: CFor = self.router.network.routers[src].clients["cfor"]

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
        return fec.fec_type == 'cfor' and fec.value[0] == self.router.name
