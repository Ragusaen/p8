import argparse
import os
import re
from tqdm import tqdm
from ast import literal_eval

class FailureScenarioData:
    def __init__(self, failed_links, total_links, looping_links, num_flows, successful_flows, connected_flows, max_memory):
        self.failed_links = failed_links
        self.total_links = total_links
        self.looping_links = looping_links
        self.num_flows = num_flows
        self.successful_flows = successful_flows
        self.connected_flows = connected_flows
        self.max_memory = max_memory


class TopologyResult:
    def __init__(self, topology_name, failure_scenarios, connectedness):
        self.topology_name = topology_name
        self.failure_scenarios = failure_scenarios
        self.connectedness = connectedness


def __compute_probability(f, e, pf=0.001):
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
        if (prop_name == 'memory'):
            memory = max(literal_eval(value))
            continue
    return FailureScenarioData(failed_links, total_links, looping_links, num_flows,
                                       successful_flows, connected_flows, 0)#, memory)


def parse_result_data(result_folder):
    result_dict: dict[str:TopologyResult] = {}
    conf_progress = 1
    for conf_name in os.listdir(result_folder):
        print(f"\nParsing results from algorithm {conf_name} - {conf_progress}/{len(os.listdir(result_folder))}")
        conf_progress += 1
        result_dict[conf_name] = []
        for topology in tqdm(os.listdir(f"{result_folder}/{conf_name}")):
            failure_scenarios = []
            res_dir = f"{result_folder}/{conf_name}/{topology}"
            for failure_chunk_file in os.listdir(res_dir):
                with open(f"{res_dir}/{failure_chunk_file}", "r") as t:
                    lines = t.readlines()
                    for line in lines:
                        failure_data = __parse_single_line_in_failure_scenario(line)
                        failure_scenarios.append(failure_data)

            result_dict[conf_name].append(TopologyResult(topology, failure_scenarios, -1))

    compute_connectedness(result_dict)
    return result_dict


def compute_connectedness(result_data: dict) -> {}:
    for conf_name in result_data.keys():
        conf_name: str
        for topology in result_data[conf_name]:
            topology: TopologyResult
            normalisation_sum = 0
            connectedness = 0
            for failure_scenario in topology.failure_scenarios:
                failure_scenario: FailureScenarioData
                p = __compute_probability(failure_scenario.failed_links, failure_scenario.total_links)
                normalisation_sum += p

                if failure_scenario.connected_flows != 0:
                    connectedness += p * (failure_scenario.successful_flows / failure_scenario.connected_flows)
                else:
                    connectedness += p

            # Normalise
            if normalisation_sum > 0:
                connectedness = connectedness / normalisation_sum

            topology.connectedness = connectedness
