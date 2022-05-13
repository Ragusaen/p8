import datetime
import os
import argparse
from get_results import parse_result_data, TopologyResult, FailureScenarioData, compute_connectedness
import overleaf
import time
from datetime import datetime
import re


class AlgorithmPlotConfiguration:
    def __init__(self, name: str, color: str, line_style: str, mark: str = "none"):
        self.name: str = name
        self.color: str = color
        self.line_style: str = line_style
        self.mark: str = mark


alg_to_plot_config_dict: {str: AlgorithmPlotConfiguration} = {
    # "cfor-disjoint": AlgorithmPlotConfiguration("Continue Forwarding", "black", "dashed"),
    "tba-simple": AlgorithmPlotConfiguration("Circular Arborescence", "black", "dash dotted", "o*"),
    "tba-complex": AlgorithmPlotConfiguration("Circular Arborescence", "blue", "solid", "diamond*"),
    "rsvp-fn": AlgorithmPlotConfiguration("RSVP Facility Node Protection", "green", "dotted", "triangle*"),
    # "hd": AlgorithmPlotConfiguration("Hop Distance", "green", "loosely dotted"),
    "kf": AlgorithmPlotConfiguration("Keep Forwarding", "cyan", "densely dotted"),
    "gft": AlgorithmPlotConfiguration("Grafting DAG", "orange", "loosely dashed", "ocircle*"),
    "inout-disjoint": AlgorithmPlotConfiguration("Ingress Egress Disjoint Paths", "red", "dashed", "square*"),
}

alg_to_bar_config_dict = {
    "tba-simple": "dots",
    "inout-disjoint": "horizontal lines",
    "tba-complex": "north east lines"
}

parser = argparse.ArgumentParser()
parser.add_argument("--max_points", type=int, required=False)
parser.add_argument("--auto_overleaf", action='store_true', required=False)
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


class OutputData:
    def __init__(self, filename: str, content: str, content_type: str):
        self.file_name: str = filename
        self.content: str = content
        self.content_type: str = content_type


def init_connectedness_table_output(result_data):
    filtered_data = dict(filter(lambda x: not x[0].__contains__("max-mem"), result_data.items()))
    return "\\begin{tabular}{c |" + " c" * len(filtered_data.keys()) + "}\n\t" + "$|F|$ & " + " & ".join(
        filtered_data.keys()) + "\\\\ \hline \n"


def add_failure_line_connectedness_table(filtered_data, len_f):
    return f"\t {len_f} & " + " & ".join(
        ["{:.6f}".format(sum(c.connectedness for c in filtered_data[algo]) / len(filtered_data[algo])) for algo in
         filtered_data]) + "\\\\ \n"


def compute_average_connectedness_for_algorithm(data, alg) -> float:
    return sum(c.connectedness for c in data[alg]) / len(data[alg])


def end_connectedness_table_output():
    return "\end{tabular}"


def generate_all_latex():
    start_time = time.time()
    if overleaf_upload:
        overleaf.synchronize()

    latex_dir = os.path.join(os.path.dirname(__file__), f"latex")
    if not os.path.exists(latex_dir) or not os.path.isdir(latex_dir):
        os.mkdir(latex_dir)

    connectedness_table_output = init_connectedness_table_output(results_data)

    # generate latex code for connectedness plot for each failure scenario cardinality
    print("Creating connectedness plot for each failure scenario cardinality")
    for len_f in range(0, 5):
        filtered_data = remove_failure_scenarios_that_are_not_of_correct_failure_cardinality(results_data, len_f)
        filtered_data = dict(filter(lambda x: not x[0].__contains__("max-mem"), filtered_data.items()))
        compute_connectedness(filtered_data)

        connectedness_table_output += add_failure_line_connectedness_table(filtered_data, len_f)

        # output_latex_content(f"connectedness_plot_data_lenf={len_f}.tex",
        #                      latex_connectedness_plot(filtered_data, max_points),
        #                      f"connectedness plot for |F| = {len_f}")

    connectedness_table_output += end_connectedness_table_output()
    output_latex_content("connectedness_table.tex", connectedness_table_output, "connectedness table")
    output_latex_content("connectedness_plot_data.tex", latex_connectedness_plot(results_data, max_points),
                         "connectedness plot")
    output_latex_content("memory_plot_data.tex", latex_memory_plot(results_data, max_points), "memory plot")
    output_latex_content("memory_bar_chart_data.tex", latex_memory_bar_chart(results_data), "memory bar chart")
    output_latex_content("loop_table_data.tex", latex_loop_table(results_data), "loop table")

    if overleaf_upload:
        overleaf.push()
    print(f"Time taken to generate latex: {time.time() - start_time}")


def output_latex_content(file_name: str, content: str, content_type: str):
    content = "% timestamp:" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + "\n" + content
    print(f"Writing {content_type} to file: 'latex/{content_type}'")
    latex_file_table = open(os.path.join(os.path.dirname(__file__), f"latex/{file_name}"), "w")
    latex_file_table.write(content)
    if overleaf_upload:
        try:
            overleaf.set_file_text(content, f"figures/results_auto_generated/{file_name}")
        except:
            print(f"ERROR: Failed uploading {content_type} at 'figures/results_auto_generated/{file_name}'")


def latex_memory_bar_chart(data: dict) -> str:
    latex_plot_legend = r"\legend{"
    skip_algs = set()
    skip_algs.add("Keep Forwarding")
    alg_longname_to_proper_alg_name = {}
    memory_to_alg_dict = {i: [] for i in range(2, 11)}
    algs = set()
    memories = [2, 3, 4, 5, 6, 7, 8, 9, 10]

    for alg in data.keys():
        alg: str
        if "max-mem" in alg:
            (alg_proper_name, memory_group) = re.split("_max-mem=", alg)
            alg_longname_to_proper_alg_name[alg] = alg_proper_name
            memory_to_alg_dict[int(memory_group)].append(alg)
            algs.add(alg_proper_name)
        else:
            max_memory_topology = max(data[alg], key=lambda it: it.max_memory / it.num_flows)
            max_memory = int(max_memory_topology.max_memory / max_memory_topology.num_flows)
            filtered_memories = list(filter(lambda it: it > max_memory, memories))
            for memory in filtered_memories:
                memory_to_alg_dict[memory].append(alg)
            algs.add(alg)

    alg_to_coordinates = {}
    for alg in algs:
        alg_to_coordinates[
            alg] = r"\addplot[" + f"color={alg_to_plot_config_dict[alg].color}, {alg_to_plot_config_dict[alg].line_style}, thick, mark={alg_to_plot_config_dict[alg].mark}" + r", every mark/.append style={solid}] coordinates{"
        latex_plot_legend += f"{alg}, "

    latex_plot_legend += "}\n"

    sorted_dict = sorted(list(memory_to_alg_dict.items()), key=lambda x: int(x[0]))
    for (alg_longname, memory_group) in sorted_dict:
        connectedness = compute_average_connectedness_for_algorithm(filtered_data, alg_longname)

        failedness = 1.0 - connectedness

        alg_to_coordinates[alg_longname_to_proper_alg_name[alg_longname]] += f"({memory_group}, {failedness}) "

    for alg in alg_to_coordinates.keys():
        alg_to_coordinates[alg] += "};\n"

    return latex_plot_legend + ''.join(alg_to_coordinates.values())


def remove_failure_scenarios_that_are_not_of_correct_failure_cardinality(data: {str: TopologyResult}, lenf: int) -> {
    str: TopologyResult}:
    filtered_data = {}
    for (conf, topologies) in data.items():
        conf: str
        filtered_data[conf] = []
        for topology in topologies:
            topology: TopologyResult
            failure_scenarios = list(filter(lambda scenario: scenario.failed_links == lenf, topology.failure_scenarios))
            filtered_data[conf].append(
                TopologyResult(topology.topology_name, topology.total_links, topology.num_flows, failure_scenarios, -1,
                               topology.fwd_gen_time, topology.max_memory, topology.within_memory_limit))

    return filtered_data


def latex_connectedness_plot(data: dict, _max_points) -> str:
    latex_plot_legend = r"\legend{"
    skip_algs = set()
    for alg in data.keys():
        if not alg_to_plot_config_dict.keys().__contains__(alg):
            skip_algs.add(alg)
            continue
        latex_plot_legend += f"{alg_to_plot_config_dict[alg].name}, "
    latex_plot_legend += "}\n"

    latex_plot_data = ""
    for (alg, topologies) in data.items():
        alg: str
        if skip_algs.__contains__(alg):
            continue

        cactus_data = sorted(topologies, key=lambda topology: topology.connectedness)

        skip_number = len(cactus_data) / _max_points
        if skip_number < 1:
            skip_number = 1

        latex_plot_data += r"\addplot[mark=none" + \
                           ", color=" + alg_to_plot_config_dict[alg].color + \
                           ", " + alg_to_plot_config_dict[alg].line_style + \
                           ", thick] coordinates{" + "\n"

        counter = 0
        for i in range(0, len(cactus_data), int(skip_number)):
            if counter > _max_points:
                break
            latex_plot_data += f"({counter}, {cactus_data[i].connectedness}) %{cactus_data[i].topology_name}\n"
            counter += 1
        latex_plot_data += r"};" + "\n"

    return latex_plot_legend + latex_plot_data


def latex_loop_table(data) -> str:
    alg_to_res_dict = {}

    for alg in data.keys():
        num_links = 0
        num_looping_links = 0
        for topology in data[alg]:
            topology: TopologyResult
            num_links += topology.total_links

            for failure_scenario in topology.failure_scenarios:
                failure_scenario: FailureScenarioData
                num_looping_links += failure_scenario.looping_links

        alg_to_res_dict[alg] = num_looping_links

    latex_tabular_header = r"\begin{tabular}{c |"
    latex_algs = r"     "
    latex_numbers = r"    loop ratio "

    for (alg, alg_num) in alg_to_res_dict.items():
        latex_tabular_header += " c"
        latex_algs += f"& {alg} "
        latex_numbers += f"& {alg_num}"

    latex_algs += r"\\\hline" + "\n"
    latex_tabular_header += "}\n"
    latex_numbers += r"\\" + "\n"
    latex_tabular_end = r"\end{tabular}"

    return latex_tabular_header + latex_algs + latex_numbers + latex_tabular_end


def latex_memory_plot(data, _max_points) -> str:
    latex_plot_legend = r"\legend{"
    skip_algs = set()
    for alg in data.keys():
        if not alg_to_plot_config_dict.keys().__contains__(alg):
            skip_algs.add(alg)
            continue
        latex_plot_legend += f"{alg_to_plot_config_dict[alg].name}, "
    latex_plot_legend += "}\n"

    latex_plot_data = ""
    for (alg, topologies) in data.items():
        if skip_algs.__contains__(alg):
            continue
        cactus_data = sorted(topologies, key=lambda topology: topology.max_memory)

        skip_number = len(cactus_data) / _max_points
        if skip_number < 1:
            skip_number = 1

        latex_plot_data += r"\addplot[mark=none" + \
                           ", color=" + alg_to_plot_config_dict[alg].color + \
                           ", " + alg_to_plot_config_dict[alg].line_style + \
                           ", thick] coordinates{" + "\n"

        counter = 0
        for i in range(0, len(cactus_data), int(skip_number)):
            if counter > _max_points:
                break
            latex_plot_data += f"({counter}, {cactus_data[i].max_memory}) %{cactus_data[i].topology_name}\n"
            counter += 1
        latex_plot_data += r"};" + "\n"

    return latex_plot_legend + latex_plot_data


generate_all_latex()
