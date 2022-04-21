from get_results import alg_full_name_dict


def latex_connectedness_plot(results_data, max_points) -> str:
    latex_plot_legend = r"\legend{"
    for alg in results_data.keys():
        latex_plot_legend += f"{alg_full_name_dict[alg]}, "
    latex_plot_legend += "}\n"

    line_accent_index = 0
    colour_iterator = ["black", "blue", "red", "green", "cyan", "purple", "yellow"]
    line_style_iterator = ["dotted", "dashed", "dashdotted", "solid", "densely dotted", "densely dashed", "loosely dashed"]

    latex_plot_data = ""
    for alg in results_data.keys():
        cactus_data = sorted(results_data[alg], key=lambda topology: topology.connectedness)

        skip_number = len(cactus_data) / max_points
        if skip_number < 1:
            skip_number = 1

        latex_plot_data += r"\addplot[mark=none" + \
                           ", color=" + colour_iterator[line_accent_index] + \
                           ", " + line_style_iterator[line_accent_index] + \
                           ", thick] coordinates{" + "\n"
        line_accent_index += 1

        counter = 0
        for i in range(0, len(cactus_data), int(skip_number)):
            if counter > max_points:
                break
            latex_plot_data += f"({counter}, {cactus_data[i].connectedness})\n"
            counter += 1
        latex_plot_data += r"};" + "\n"

    return latex_plot_legend + latex_plot_data
