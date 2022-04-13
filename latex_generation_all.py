import os
import argparse
from get_results import parse_result_data
from latex_loop_table import latex_loop_table
from latex_plot import latex_plot
import overleaf

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

print("Creating performance plot from data in results folder")
plot = latex_plot(results_data, max_points)

print("Creating loop table from data in results folder")
table = latex_loop_table(results_data)

latex_folder = os.path.join(os.path.dirname(__file__), "latex")
if not (os.path.exists(latex_folder) and os.path.isdir(latex_folder)):
    os.mkdir(latex_folder)

print(r"Writing latex plot to file: 'latex/results_plot_all.tex'")
latex_file_plot = open(os.path.join(os.path.dirname(__file__), "latex/results_plot_all.tex"), "w")
latex_file_plot.write(plot)
print(r"Writing latex loop table to file: 'latex/results_loop_table_all.tex'")
latex_file_table = open(os.path.join(os.path.dirname(__file__), "latex/results_loop_table_all.tex.tex"), "w")
latex_file_table.write(table)

if overleaf_upload:
    print(r"Uploading latex plot to Overleaf at: 'figures/results_plot_all.tex'")
    overleaf.set_file_text(plot, "figures/results_plot_all.tex")
    print(r"Uploading latex plot to Overleaf at: 'figures/results_loop_table_all.tex'")
    overleaf.set_file_text(table, "figures/results_loop_table_all.tex")
print("Latex results generation finished")
