#!/bin/bash
#SBATCH --partition=naples,dhabi,rome


PD=$(pwd)

source ${PD}/venv/bin/activate

TOPO="${1}"

python3 create_confs.py --topology topologies/${TOPO} --conf confs --keep_failure_chunks --result_folder results/${TOPO%.json}


