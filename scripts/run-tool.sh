#!/bin/bash
#SBATCH --mail-type=NONE # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=amad18@student.aau.dk
#SBATCH --output=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.out 
#SBATCH --error=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.err
#SBATCH --partition=naples,dhabi,rome
#SBATCH --time=00:30:00

PD=$(pwd)

source ~/p8/venv/bin/activate

python3 -m pip install -r requirements.txt

# # In case you write to auxiliary files, you can work in a temporary folder in /scratch (which is node-local).
# U=$(whoami)
# SCRATCH_DIRECTORY=/scratch/${U}/${SLURM_JOBID}
# mkdir -p ${SCRATCH_DIRECTORY}
# cd ${SCRATCH_DIRECTORY}


CONFIG_FILE="$1"
FAILCHUNK="$2"

${PD}/tool_simulate.py --conf ${CONFIG_FILE} --failure_chunk_file ${FAILCHUNK}

# # Clean up in scratch, if used.
# cd /scratch/${U}
# [ -d "${SLURM_JOBID}" ] && rm -r ${SLURM_JOBID}
