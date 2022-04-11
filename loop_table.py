import argparse
import os
import overleaf
from get_results import parse_result_data

parser = argparse.ArgumentParser()
parser.add_argument("--results_folder", type=str, required=True)
parser.add_argument("--latex_path_table", type=str, required=False)
args = parser.parse_args()

dir = os.path.dirname(__file__)
results_folder = os.path.join(dir, args.results_folder)

output_latex_code: str = ""

alg_to_res_dict = {}

results_data = parse_result_data(results_folder)

for alg in results_data.keys():
    num_links = 0
    num_looping_links = 0
    for topology in results_data[alg]:
        for chunk_data in results_data[alg][topology].failure_chunks:
            for failure_scenario_data in chunk_data.failure_scenario_data:
                num_links += failure_scenario_data.total_links
                num_looping_links += failure_scenario_data.failed_links_with_loops

    ratio = float(num_looping_links) / float(num_links)
    alg_to_res_dict[alg] = ratio

latex1 = r"\begin{table}[]" + "\n" + r"    \centering" + "\n"
latex_table_header = r"    \begin{tabular}{c |"
latex_algs = r"         "
latex_numbers = r"        loop ratio "

for (alg, alg_num) in alg_to_res_dict.items():
    latex_table_header += " c"
    latex_algs += f"& {alg} "
    latex_numbers += f"& " + "{:.6f}".format(alg_num)

latex_algs += r"\\\hline" + "\n"
latex_table_header += "}\n"
latex_numbers += r"\\" + "\n"

latex2 = r"\end{tabular}" + "\n" + r"\caption{Ratio of links that has been congested because of loops. Sum of all " \
         r"links on all networks divided by looping links. }" + "\n" + r"\label{" + r"tab:loop_table_all}" + \
         "\n" + r"\end{table}" + "\n "

output_latex_code = latex1 + latex_table_header + latex_algs + latex_numbers + latex2

latex_folder = os.path.join(dir, "latex")
if not (os.path.exists(latex_folder) and os.path.isdir(latex_folder)):
    os.mkdir(latex_folder)

latex_file = open(os.path.join(dir, "latex/" + args.latex_path_table), "w")
latex_file.write(output_latex_code)


#overleaf.set_file_text(output_latex_code, "figures/loop_table_all2.tex")
#print("Created and uploaded loop table to overleaf")