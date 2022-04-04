import argparse
import os


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
                        s = l.split(" ")
                        if len(s) > 7:
                            p = compute_probability(int(s[0]), int(s[2]))
                            total_packets = int(s[4])
                            connected_packets = int(s[7])
                            connectivity = float(s[1])

                            if connectivity > 0:
                                connectedness += p * connectivity * (total_packets / connected_packets)

                            normalisation_sum += p

                            l = t.readline()
                        else:
                            l = t.readline()
                            continue

            # normalise
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




