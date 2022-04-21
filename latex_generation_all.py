import os
import argparse
from get_results import parse_result_data, TopologyResult, FailureScenarioData, compute_connectedness
from latex_loop_table import latex_loop_table
from latex_connectedness_plot import latex_connectedness_plot
import overleaf
import time

parser = argparse.ArgumentParser()
parser.add_argument("--max_points", type=int, required=False)
parser.add_argument("--auto_overleaf", type=bool, required=False)
args = parser.parse_args()

results_folder = os.path.join(os.path.dirname(__file__), "results")
print("Parsing results from results folder")
results_data = parse_result_data(results_folder)

max_points = 1000000
if args.max_points is not None:
    max_points = args.max_points

overleaf_upload = False
if args.auto_overleaf is not None:
    overleaf_upload = args.auto_overleaf


def generate_all_latex():
    # generate latex code for connectedness plot for each failure scenario cardinality
    print("Creating connectedness plot for each failure scenario cardinality")
    start_time = time.time()
    for len_f in range(1, 5):
        print(f"Creating connectedness plot for |F| = {len_f}")
        filtered_data = {}
        for conf in results_data.keys():
            conf: str
            filtered_data[conf] = []
            for topology in results_data[conf]:
                topology: TopologyResult
                failure_scenarios = []
                for failure_scenario in topology.failure_scenarios:
                    failure_scenario: FailureScenarioData
                    if failure_scenario.failed_links == 3:
                        failure_scenarios.append(failure_scenario)
                if len(failure_scenarios) > 0:
                    filtered_data[conf].append(TopologyResult(topology.topology_name, failure_scenarios, topology.connectedness))

        compute_connectedness(filtered_data)
        connectedness_plot = latex_connectedness_plot(filtered_data, max_points)
        write_local(f"results_connectedness_plot_data_lenf={len_f}.tex", connectedness_plot)
        if overleaf_upload:
            upload_to_overleaf(f"figures/results_connectedness_plot_data_lenf={len_f}.tex", connectedness_plot)

    # generate latex code for connectedness plot
    print("Creating connectedness plot from data in results folder")
    connectedness_plot = latex_connectedness_plot(results_data, max_points)
    write_local("results_connectedness_plot_data.tex", connectedness_plot)
    if overleaf_upload:
        upload_to_overleaf("figures/results_connectedness_plot_data.tex", connectedness_plot)

    # generate latex code for loop table
    print("Creating loop table from data in results folder")
    loop_table = latex_loop_table(results_data)
    write_local("results_loop_table_data.tex", loop_table)
    if overleaf_upload:
        upload_to_overleaf("figures/results_loop_table_data.tex", loop_table)

    print(f"Time taken to generate latex: {time.time()-start_time}")


def write_local(file_name: str, content: str):
    print(f"Writing latex to local file: 'latex/{file_name}'")
    latex_file_table = open(os.path.join(os.path.dirname(__file__), f"latex/{file_name}"), "w")
    latex_file_table.write(content)


def upload_to_overleaf(file_path: str, content: str):
    print(f"Uploading latex to Overleaf at: '{file_path}'")
    overleaf.set_file_text(content, f"{file_path}")
    print("Finished uploading to overleaf")


generate_all_latex()
