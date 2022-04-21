import os
import argparse
from get_results import parse_result_data
from latex_loop_table import latex_loop_table
from latex_connectedness_plot import latex_connectedness_plot
from latex_memory import latex_memory_plot
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
plot = latex_connectedness_plot(results_data, max_points)

print("Creating loop table from data in results folder")
table = latex_loop_table(results_data)

print("Creating memory plot from data in results folder")
memory = latex_memory_plot(results_data, max_points)

latex_folder = os.path.join(os.path.dirname(__file__), "latex")
if not (os.path.exists(latex_folder) and os.path.isdir(latex_folder)):
    os.mkdir(latex_folder)

plot_file_name = r"results_connectedness_plot_data.tex"
table_file_name = r"results_loop_table_data.tex"
memory_plot_file_name = r"results_memory_plot_data.tex"
print(f"Writing latex plot to file: 'latex/{plot_file_name}'")
latex_file_plot = open(os.path.join(os.path.dirname(__file__), f"latex/{plot_file_name}"), "w")
latex_file_plot.write(plot)
print(f"Writing latex loop table to file: 'latex/{table_file_name}'")
latex_file_table = open(os.path.join(os.path.dirname(__file__), f"latex/{table_file_name}"), "w")
latex_file_table.write(table)
print(f"Writing latex memory table to file: 'latex/{memory_plot_file_name}'")
latex_file_memory = open(os.path.join(os.path.dirname(__file__), f"latex/{memory_plot_file_name}"), "w")
latex_file_memory.write(memory)

if overleaf_upload:
    print(f"Uploading latex plot to Overleaf at: 'figures/{plot_file_name}'")
    overleaf.set_file_text(plot, f"figures/{plot_file_name}")
    print(f"Uploading latex plot to Overleaf at: 'figures/{table_file_name}'")
    overleaf.set_file_text(table, f"figures/{table_file_name}")
print("Latex results generation finished")
