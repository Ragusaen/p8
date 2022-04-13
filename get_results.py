import argparse
import os
import re
from tqdm import tqdm

alg_full_name_dict = {
    "cfor": "Continue Forwarding",
    "tba": "Circular Arborescence",
    "rsvp-fn": "RSVP Facility Node Protection",
    "hd": "Hop Distance",
    "keepf": "Keep Forwarding",
}

class FailureScenarioData:
    def __init__(self, failed_links, total_links, connectivity, looping_links, num_flows, successful_flows, connected_flows):
        self.failed_links = failed_links
        self.total_links = total_links
        self.connectivity = connectivity
        self.looping_links = looping_links
        self.num_flows = num_flows
        self.successful_flows = successful_flows
        self.connected_flows = connected_flows


class FailureChunkResultData:
    def __init__(self, chunk_name, failure_scenerio_data):
        self.failure_chunk_name = chunk_name
        self.failure_scenario_data = failure_scenerio_data #List of FailureScenarioData


class TopologyResult:
    def __init__(self, topology_name, failure_chunks, connectedness):
        self.topology_name = topology_name
        self.failure_chunks = failure_chunks
        self.connectedness = connectedness

def __compute_probability(f, e, pf=0.5):
    return (pf ** f) * (1 - pf) ** (e - f)

def __parse_single_line_in_failure_scenario(line):
    parts = line.split(' ')
    for part in parts:
        split = part.split(':')
        prop_name = split[0]
        value = split[1]

        if (prop_name == 'len(F)'): #No match/case in this version :(
            failed_links = int(value)
            continue
        if (prop_name == 'len(E)'):
            total_links = int(value)
            continue
        if (prop_name == 'ratio'):
            connectivity = float(value)
            continue
        if (prop_name == 'looping_links'):
            looping_links = int(value)
            continue
        if (prop_name == 'num_flows'):
            num_flows = int(value)
            continue
        if (prop_name == 'successful_flows'):
            successful_flows = int(value)
            continue
        if (prop_name == 'connected_flows'):
            connected_flows = int(value)
            continue
    return FailureScenarioData(failed_links, total_links, connectivity, looping_links, num_flows,
                                       successful_flows, connected_flows)

def parse_result_data(result_folder):
    result_dict = {}
    conf_progress = 1
    for conf_name in os.listdir(result_folder):
        print(f"\nParsing results from algorithm {alg_full_name_dict[conf_name]} - {conf_progress}/{len(os.listdir(result_folder))}")
        conf_progress += 1
        result_dict[conf_name] = {}
        for topology in tqdm(os.listdir(f"{result_folder}/{conf_name}")):
            failure_chunks = []
            normalisation_sum = 0
            connectedness = 0
            res_dir = f"{result_folder}/{conf_name}/{topology}"
            for res_file in os.listdir(res_dir):
                failure_scenarios = list()
                with open(f"{res_dir}/{res_file}", "r") as t:
                    lines = t.readlines()
                    for line in lines:
                        failure_data = __parse_single_line_in_failure_scenario(line)

                        p = __compute_probability(failure_data.failed_links, failure_data.total_links)
                        normalisation_sum += p

                        if failure_data.connected_flows != 0:
                            connectedness += p * (failure_data.successful_flows / failure_data.connected_flows)
                        else:
                            connectedness += p

                        failure_scenarios.append(failure_data)

                failure_chunks.append(FailureChunkResultData(res_file, failure_scenarios))

            # Normalise
            if normalisation_sum > 0:
                connectedness = connectedness / normalisation_sum

            result_dict[conf_name][topology] = TopologyResult(topology, failure_chunks, connectedness)

    return result_dict
