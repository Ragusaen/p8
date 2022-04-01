import argparse
import os


parser = argparse.ArgumentParser()
parser.add_argument("--results_folder", type=str, required=True)
parser.add_argument("--output_file", type=str, required=True)

dir = os.path.dirname(__file__)

args = parser.parse_args()
folder =  os.path.join(dir, args.results_folder)
def compute_probability(f, e, pf=0.001):
    return (pf ** f) * (1 - pf) ** (e - f)

probability_dist = [compute_probability(x, 0) for x in range(0, 5)]
with open(args.output_file, "w") as r:
    all_results = []
    for topology in os.listdir(folder):
        for conf in os.listdir(f"{folder}/{topology}"):
            for res_file in os.listdir(f"{folder}/{topology}/{conf}"):
                connectivity = 0
                with open(f"{folder}/{topology}/{conf}/{res_file}") as t:
                    l = t.readline()
                    while l:
                        s = l.split(" ")
                        connectivity += probability_dist[int(s[0])] * float(s[1])
                        l = t.readline()
                    all_results.append(connectivity)

    all_results.sort()
    i = 0
    for res in all_results:
        r.write(f"({i}, {res})")
        i += 1





