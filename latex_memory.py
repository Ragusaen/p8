from get_results import alg_full_name_dict


def latex_memory_plot(results_data, max_points) -> str:
    latex_plot_legend = r"\legend{"
    for alg in results_data.keys():
        latex_plot_legend += f"{alg_full_name_dict[alg]}, "
    latex_plot_legend += "}\n"

    colour_index = 0
    colour_iterator = ["blue", "red", "green", "cyan", "purple", "yellow"]
    latex_plot_data = ""
    for alg in results_data.keys():
        cactus_data = sorted(results_data[alg].values(), key=lambda topology: topology.max_memory)

        skip_number = len(cactus_data) / max_points
        if skip_number < 1:
            skip_number = 1

        latex_plot_data += r"\addplot[mark=none, color=" + colour_iterator[colour_index] + r", thick] coordinates{" + "\n"
        colour_index += 1

        counter = 0
        for i in range(0, len(cactus_data), int(skip_number)):
            if counter > max_points:
                break
            latex_plot_data += f"({counter}, {cactus_data[i].max_memory})\n"
            counter += 1
        latex_plot_data += r"};" + "\n"

    return latex_plot_legend + latex_plot_data
