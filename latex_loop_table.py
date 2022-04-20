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

    latex2 = r"\end{tabular}" + "\n" + r"\caption{Ratio of links that has been congested because of loops. " \
                                       r"Looping links divided by sum of all links. }" + "\n" + r"\label{" + r"tab:results_loop_table_all}" + \
             "\n" + r"\end{table}" + "\n "

    return latex1 + latex_table_header + latex_algs + latex_numbers + latex2
