import argparse
import os
import re

class ResultData:
    def __init__(self, failed_links, total_links, connectivity, failed_links_with_loops, num_flows, successful_flows, connected_flows):
        self.failed_links = failed_links
        self.total_links = total_links
        self.connectivity = connectivity
        self.failed_links_with_loops = failed_links_with_loops
        self.num_flows = num_flows
        self.successful_flows = successful_flows
        self.connected_flows = connected_flows



parser = argparse.ArgumentParser()
parser.add_argument("--results_folder", type=str, required=True)
parser.add_argument("--output_file", type=str, required=True)

dir = os.path.dirname(__file__)

args = parser.parse_args()
folder =  os.path.join(dir, args.results_folder)

result_path = os.path.join(dir, args.output_file)

class Output():
    def __init__(self, conf_name, result_path):
        self.conf_name = conf_name
        self.result_path = result_path
        self.connectedness_list = []
        self.file = open(result_path + conf_name, "w")

def compute_probability(f, e, pf=0.001):
    return (pf ** f) * (1 - pf) ** (e - f)

def parse_result_data(line):
    failed_links = int(re.findall(r'len\(F\):(\d+)', l)[0])
    total_links = int(re.findall(r'len\(E\):(\d+)', l)[0])
    connectivity = float(re.findall(r'ratio:(\d+\.\d+)', l)[0])
    failed_links_with_loops = int(re.findall(r'failed_links\(with_loops\):(\d+)', l)[0])
    num_flows = int(re.findall(r'num_flows:(\d+)', l)[0])
    successful_flows = int(re.findall(r'successful_flows:(\d+)', l)[0])
    connected_flows = int(re.findall(r'connected_flows:(\d+)', l)[0])
    result_data = ResultData(failed_links, total_links, connectivity, failed_links_with_loops, num_flows,
                             successful_flows, connected_flows)
    return result_data

conf_names = ["conf_3", "conf_21"]

outputs = []
for conf_name in conf_names:
    outputs.append(Output(conf_name, result_path))

for topology in os.listdir(folder):
    for output in outputs:
        connectivity = 0
        normalisation_sum = 0
        res_dir = f"{folder}/{topology}/{output.conf_name}"
        exists = os.path.exists(res_dir)
        if exists:
            connectedness = 0
            for res_file in os.listdir(res_dir):
                with open(f"{res_dir}/{res_file}", "r") as t:
                    l = t.readline()
                    while l:
                        result_data = parse_result_data(l)

                        p = compute_probability(result_data.failed_links, result_data.total_links)
                        normalisation_sum += p
                        connectedness += p * result_data.connectivity * (result_data.num_flows / result_data.connected_flows) #TODO: This is not right, fix

                        l = t.readline()

            # Normalise
            if normalisation_sum > 0:
                connectedness = connectedness / normalisation_sum
                output.connectedness_list.append(connectedness)
                print(connectedness)
        else:
            continue

for output in outputs:
    output.connectedness_list.sort()
    i = 0
    for res in output.connectedness_list:
        output.file.write(f"({i}, {res})\n")
        i += 1
    output.file.close()

print("")





