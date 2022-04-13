import os
import argparse
from get_results import parse_result_data
from latex_loop_table import latex_loop_table
from latex_plot import latex_plot

parser = argparse.ArgumentParser()
parser.add_argument("--max_points", type=int, required=False)
args = parser.parse_args()

results_folder = os.path.join(os.path.dirname(__file__), "results")
results_data = parse_result_data(results_folder)

from get_results import parse_result_data
max_points = 0
if "max_points" in args:
    max_points = args.max_points

latex_plot(results_data, 50)
latex_loop_table(results_data)

