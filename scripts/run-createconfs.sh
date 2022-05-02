#!/bin/bash
#SBATCH --output=/nfs/home/student.aau.dk/amad18/slurm-output/createconfs-%j.out
#SBATCH --error=/nfs/home/student.aau.dk/amad18/slurm-output/createconfs-%j.err
#SBATCH --partition=naples
#SBATCH --time=06:00:00
#SBATCH --mem=12G
#SBATCH --cpus-per-task=1

PD=$(pwd)

source ${PD}/venv/bin/activate

TOPO="${1}"

python3 create_confs.py --topology topologies/${TOPO} --conf confs --keep_failure_chunks --result_folder results