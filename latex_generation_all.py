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

max_points = 1000000
if args.max_points is not None:
    max_points = args.max_points

latex_plot(results_data, max_points)
latex_loop_table(results_data)

