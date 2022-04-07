#!/bin/bash
#SBATCH --mail-type=NONE # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=amad18@student.aau.dk
###SBATCH --output=/dev/null
#SBATCH --partition=dhabi
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1

PD=$(pwd)

source ~/p8/venv/bin/activate

python3 -m pip install -r requirements.txt

CONFIG_FILE_YML="${1}.yml"
CONFIG_FILE="${1}"
FAILCHUNK="$2"

python3 --version

python3 ${PD}/tool_simulate.py --conf confs/${CONFIG_FILE_YML} --failure_chunk_file ${FAILCHUNK} --result_folder "results/${CONFIG_FILE}"