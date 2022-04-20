def latex_loop_table(results_data) -> str:
    alg_to_res_dict = {}

    for alg in results_data.keys():
        num_links = 0
        num_looping_links = 0
        for topology in results_data[alg]:
            for chunk_data in results_data[alg][topology].failure_chunks:
                for failure_scenario_data in chunk_data.failure_scenario_data:
                    num_links += failure_scenario_data.total_links
                    num_looping_links += failure_scenario_data.looping_links

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
