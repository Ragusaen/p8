from mpls_classes import MPLS_Client, Network, oFEC, Router
from target_based_arborescence.arborescences import find_arborescences


class TargetBasedArborescence(MPLS_Client):

    protocol = "tba"

    def __init__(self, router: Router, **kwargs):
        super().__init__(router)

        # The demands where this router is the tailend
        self.demands: dict[str, tuple[str, str]] = {}

        # The arborescences that are rooted in this router
        self.rooted_arborescences: list[list[tuple[str, str]]] = []

        # The FECs this router is a non-tailend part of. fec_name -> (fec, next_hop, bounce_fec_name)
        self.arborescence_next_hop: dict[str, tuple[oFEC, str, str]] = {}


    # Abstract functions to be implemented by each client subclass.
    def LFIB_compute_entry(self, fec: oFEC, single=False):
        _, next_hop, bounce_fec_name = self.arborescence_next_hop[fec.name]

        local_label = self.get_local_label(fec)
        remote_label = self.get_remote_label(next_hop, fec)
        main_entry = {"out": next_hop, "ops": [{"swap" : remote_label}], "weight" : 0}
        yield (local_label, main_entry)

        bounce_fec, bounce_next_hop, _ = self.arborescence_next_hop[bounce_fec_name]
        local_bounce_label = self.get_local_label(bounce_fec)
        remote_bounce_label = self.get_remote_label(bounce_next_hop, bounce_fec)
        bounce_entry = {"out": self.LOCAL_LOOKUP, "ops": [{"swap" : remote_bounce_label}], "weight" : 1}
        yield (local_bounce_label, bounce_entry)


    # Defines a demand for a headend to this one
    def define_demand(self, headend: str):
        self.demands[f"{len(self.demands.items())}_{headend}_to_{self.router.name}"] = (headend, self.router.name)

    def commit_config(self):
        self.rooted_arborescences = find_arborescences(self.router.network, self.demands.keys(), self.router.name)

        fec_arbors: list[tuple[oFEC, list[tuple[str, str]]]] =\
            [(oFEC("arborescence", f"{self.router.name}_{i}", (self.router.name, i)), a) for i, a in enumerate(self.rooted_arborescences)]

        for i, (fec, a) in enumerate(fec_arbors):
            assert len(fec_arbors) > 1
            bounce_fec, _ = fec_arbors[(i + 1) % len(fec_arbors)]

            # Loop over all edges in arborescence
            for src, tgt in a:
                # Add an arborescence next-hop for this FEC to the routers in the arborescence
                src_router: TargetBasedArborescence = self.router.network.routers[src].clients["tba"]
                src_router.arborescence_next_hop[fec.name] = (fec, tgt, bounce_fec.name)

    def compute_bypasses(self):
        pass

    def LFIB_refine(self, label):
        pass

    def known_resources(self):
        for _, v in self.arborescence_next_hop.items():
            yield v[0]

    def self_sourced(self, fec: oFEC):
        return fec.fec_type == "arborescence" and fec.value[0] == self.router.name

