import os
from tqdm import tqdm
from ast import literal_eval


class FailureScenarioData:
    def __init__(self, failed_links, looping_links, successful_flows, connected_flows):
        self.failed_links = failed_links
        self.looping_links = looping_links
        self.successful_flows = successful_flows
        self.connected_flows = connected_flows


class CommonResultData:
    def __init__(self, total_links, num_flows, fwd_gen_time, max_memory):
        self.total_links = total_links
        self.num_flows = num_flows
        self.fwd_gen_time = fwd_gen_time
        self.max_memory = max_memory


class TopologyResult:
    def __init__(self, topology_name, total_links, num_flows, failure_scenarios, connectedness, fwd_gen_time, max_memory):
        self.topology_name = topology_name
        self.total_links = total_links
        self.num_flows = num_flows
        self.failure_scenarios = failure_scenarios
        self.connectedness = connectedness
        self.fwd_gen_time = fwd_gen_time
        self.max_memory = max_memory


def __compute_probability(f, e, pf=0.001):
    return (pf ** f) * (1 - pf) ** (e - f)


def __parse_line_in_common(line: str):
    parts = line.split(' ')
    for part in parts:
        prop_name, value = part.split(':')

        if (prop_name == 'len(E)'):
            total_links = int(value)
            continue
        if (prop_name == 'num_flows'):
            num_flows = int(value)
            continue
        if (prop_name == 'fwd_gen_time'):
            fwd_gen_time = int(value)
            continue
        if (prop_name == 'memory'):
            max_memory = int(max(literal_eval(value)))
            continue

    return CommonResultData(total_links, num_flows, fwd_gen_time, max_memory)

def __parse_single_line_in_failure_scenario(line: str):
    # remove spaces in memory list
    # line = line.replace(", ", ",")

    parts = line.split(' ')
    for part in parts:
        prop_name, value = part.split(':')

        if (prop_name == 'len(F)'): #No match/case in this version :(
            failed_links = int(value)
            continue
        if (prop_name == 'looping_links'):
            looping_links = int(value)
            continue
        if (prop_name == 'successful_flows'):
            successful_flows = int(value)
            continue
        if (prop_name == 'connected_flows'):
            connected_flows = int(value)
            continue

    return FailureScenarioData(failed_links, looping_links, successful_flows, connected_flows)


def parse_result_data(result_folder) -> dict[str, TopologyResult]:
    result_dict: dict[str:TopologyResult] = {}
    conf_progress = 1
    for conf_name in os.listdir(result_folder):
        print(f"\nParsing results from algorithm {conf_name} - {conf_progress}/{len(os.listdir(result_folder))}")
        conf_progress += 1
        result_dict[conf_name] = []
        for topology in tqdm(os.listdir(f"{result_folder}/{conf_name}")):
            failure_scenarios = []
            total_links, num_flows, fwd_gen_time, max_memory = 0, 0, 0, 0
            res_dir = f"{result_folder}/{conf_name}/{topology}"
            for failure_chunk_file in os.listdir(res_dir):
                with open(f"{res_dir}/{failure_chunk_file}", "r") as t:
                    lines = t.readlines()

                    if str(failure_chunk_file) == "common":
                        common_data = __parse_line_in_common(lines[0])
                        total_links = common_data.total_links
                        num_flows = common_data.num_flows
                        fwd_gen_time = common_data.fwd_gen_time
                        max_memory = common_data.max_memory
                    else:
                        for line in lines:
                            failure_data = __parse_single_line_in_failure_scenario(line)
                            failure_scenarios.append(failure_data)

            result_dict[conf_name].append(TopologyResult(topology, total_links, num_flows, failure_scenarios, -1, fwd_gen_time, max_memory))

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
                p = __compute_probability(failure_scenario.failed_links, topology.total_links)
                normalisation_sum += p

                if failure_scenario.connected_flows != 0:
                    connectedness += p * (failure_scenario.successful_flows / failure_scenario.connected_flows)
                else:
                    connectedness += p

            # Normalise
            if normalisation_sum > 0:
                connectedness = connectedness / normalisation_sum
            if len(topology.failure_scenarios) == 0:
                connectedness = 1.2
                # this should never happen
                # raise Exception("Topology had connectivity of 0.. very likely bug")

            topology.connectedness = connectedness

if __name__ == '__main__':
    data = parse_result_data('results')

    print("hello")