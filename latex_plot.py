import os
from get_results import alg_full_name_dict


def latex_plot(results_data, max_points):
    latex1 = r"\begin{tikzpicture}" + "\n" + r"\begin{axis}[" + "\n" + r"ylabel={Connectedness}, legend pos= {south east}, " \
             r"legend style = {legend cell align=left}, ymode = {log}, tick label style={font=\scriptsize}, " \
             r"minor y tick style = {draw = none}, y label style = {yshift = -5pt}, legend style = {font=\scriptsize}, " \
             r"width=\linewidth, height=5cm" + "\n]\n"
    latex_plot_legend = r"\legend{"
    for alg in results_data.keys():
        latex_plot_legend += f"{alg_full_name_dict[alg]}, "
    latex_plot_legend += "}\n"

    colour_index = 0
    colour_iterator = ["blue", "red", "green", "cyan", "purple"]
    latex_plot_data = ""
    for alg in results_data.keys():
        cactus_data = sorted(results_data[alg].values(), key=lambda topology: topology.connectedness)

        skip_number = 1
        if max_points > 0:
            skip_number = len(cactus_data) / max_points
            if skip_number < 1:
                skip_number = 1

        latex_plot_data += r"\addplot[mark=none, color=" + colour_iterator[colour_index] + r", thick] coordinates{" + "\n"
        colour_index += 1

        counter = 0
        for i in range(0, len(cactus_data), int(skip_number)):
            if counter > max_points:
                break
            latex_plot_data += f"({counter}, {cactus_data[i].connectedness})\n"
            counter += 1
        latex_plot_data += r"};" + "\n"

    latex_end = r"\end{axis}" + "\n" r"\end{tikzpicture}" + "\n"

    output_latex_code = latex1 + latex_plot_legend + latex_plot_data + latex_end

    latex_folder = os.path.join(os.path.dirname(__file__), "latex")
    if not (os.path.exists(latex_folder) and os.path.isdir(latex_folder)):
        os.mkdir(latex_folder)

    latex_file = open(os.path.join(os.path.dirname(__file__), "latex/plot.tex"), "w")
    latex_file.write(output_latex_code)


    # overleaf.set_file_text(output_latex_code, "figures/loop_table_all2.tex")
    # print("Created and uploaded loop table to overleaf")