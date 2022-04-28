#!/bin/bash
#SBATCH --partition=rome
#SBATCH --time=06:00:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1

PD=$(pwd)

source ${PD}/venv/bin/activate

TOPO="${1}"

python3 create_confs.py --topology ${TOPO} --conf confs --result_folder results
