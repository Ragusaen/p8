from get_results import TopologyResult, FailureScenarioData


def latex_loop_table(results_data) -> str:
    alg_to_res_dict = {}

    for alg in results_data.keys():
        num_links = 0
        num_looping_links = 0
        for topology in results_data[alg]:
            topology: TopologyResult
            for failure_scenario in topology.failure_scenarios:
                failure_scenario: FailureScenarioData
                num_links += failure_scenario.total_links
                num_looping_links += failure_scenario.looping_links

        ratio = float(num_looping_links) / float(num_links)
        alg_to_res_dict[alg] = ratio

    latex_tabular_header = r"\begin{tabular}{c |"
    latex_algs = r"     "
    latex_numbers = r"    loop ratio "

    for (alg, alg_num) in alg_to_res_dict.items():
        latex_tabular_header += " c"
        latex_algs += f"& {alg} "
        latex_numbers += f"& " + "{:.6f}".format(alg_num)

    latex_algs += r"\\\hline" + "\n"
    latex_tabular_header += "}\n"
    latex_numbers += r"\\" + "\n"
    latex_tabular_end = r"\end{tabular}"

    return latex_tabular_header + latex_algs + latex_numbers + latex_tabular_end
