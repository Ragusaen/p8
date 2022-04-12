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

def compute_probability(f, e, pf=0.5):
    return (pf ** f) * (1 - pf) ** (e - f)

def parse_result_data(result_folder):
    result_dict = {}
    conf_progress = 1
    hello = 0
    for conf_name in os.listdir(result_folder):
        if hello > 6:
            continue
        hello += 1
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
                    l = t.readline()
                    while l:
                        failed_links = int(re.findall(r'len\(F\):(\d+)', l)[0])
                        total_links = int(re.findall(r'len\(E\):(\d+)', l)[0])
                        connectivity = float(re.findall(r'ratio:(\d+\.\d+)', l)[0])
                        looping_links = int(re.findall(r'looping_links:(\d+)', l)[0])
                        num_flows = int(re.findall(r'num_flows:(\d+)', l)[0])
                        successful_flows = int(re.findall(r'successful_flows:(\d+)', l)[0])
                        connected_flows = int(re.findall(r'connected_flows:(\d+)', l)[0])
                        failure_data = FailureScenarioData(failed_links, total_links, connectivity, looping_links,
                                                 num_flows,
                                                 successful_flows, connected_flows)

                        p = compute_probability(failure_data.failed_links, failure_data.total_links)
                        normalisation_sum += p

                        if failure_data.connected_flows != 0:
                            connectedness += p * (failure_data.successful_flows / failure_data.connected_flows)
                        else:
                            connectedness += p

                        failure_scenarios.append(failure_data)
                        l = t.readline()

                failure_chunks.append(FailureChunkResultData(res_file, failure_scenarios))

            # Normalise
            if normalisation_sum > 0:
                connectedness = connectedness / normalisation_sum

            result_dict[conf_name][topology] = TopologyResult(topology, failure_chunks, connectedness)

    return result_dict
