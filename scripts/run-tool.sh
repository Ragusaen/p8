#!/bin/bash
#SBATCH --mail-type=FAIL # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=amad18@student.aau.dk
#SBATCH --output=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.out 
#SBATCH --error=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.err
#SBATCH --partition=naples,dhabi,rome
#SBATCH --mem=16G
#SBATCH --time=00:30:00

let "m=1024*1024"
ulimit -v $m

PD=$(pwd)

source ${PD}/venv/bin/activate

# # In case you write to auxiliary files, you can work in a temporary folder in /scratch (which is node-local).
# U=$(whoami)
# SCRATCH_DIRECTORY=/scratch/${U}/${SLURM_JOBID}
# mkdir -p ${SCRATCH_DIRECTORY}
# cd ${SCRATCH_DIRECTORY}


CONFIG_FILE="${PD}/$1"

${PD}/tool_simulate.py --conf ${CONFIG_FILE}

# # Clean up in scratch, if used.
# cd /scratch/${U}
# [ -d "${SLURM_JOBID}" ] && rm -r ${SLURM_JOBID}
