import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--results_folder", type=str, required=True)
parser.add_argument("--latex_path", type=str, required=False)
args = parser.parse_args()

dir = os.path.dirname(__file__)
results_folder = os.path.join(dir, args.results_folder)

output_latex_code: str = ""

conf_to_alg_dict = {"conf_3": "FP", "conf_21": "ARB", "conf_22": "HD", "conf_23": "CF"}
alg_to_res_dict = {}
for value in conf_to_alg_dict.values():
    alg_to_res_dict[value] = -1.0


def compute_ratio_of_looping_links(num_links: int, num_looping_links: int) -> float:
    return float(num_looping_links) / num_links

for network_folder in os.listdir(results_folder):
    if os.path.isdir(f"{results_folder}/{network_folder}"):
        for alg_folder in os.listdir(f"{results_folder}/{network_folder}"):
            if alg_folder not in conf_to_alg_dict.keys():
                raise Exception(f"'{alg_folder}' folder name in results is not a recognized algorithm config.")

            if os.path.isdir(f"{results_folder}/{network_folder}/{alg_folder}"):
                num_links = 0
                num_looping_links = 0
                for results_file in os.listdir(f"{results_folder}/{network_folder}/{alg_folder}"):
                    with open(f"{results_folder}/{network_folder}/{alg_folder}/{results_file}", "r") as f:
                        for line in f:
                            data = None
                            num_links += data
                            num_looping_links += data

                ratio = compute_ratio_of_looping_links(num_links, num_looping_links)
                alg_to_res_dict[alg_folder] = ratio

    else:
        continue

latex1 = r"""
\begin{table}[]
    \centering
    \begin{tabular}{c | c c c c}"""
latex_mid = ""
latex2 = r"""
    \end{tabular}
    \caption{Ratio of links that has been congested because of loops. Sum of all links on all networks divided by looping links. }
    \label{tab:loop_table_all}
\end{table}
"""

output_latex_code = latex1 + latex_mid + latex2
latex_file = open(args.latex_path, "w")
latex_file.write(output_latex_code)
