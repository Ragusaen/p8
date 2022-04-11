#!/bin/bash
#SBATCH --mail-type=NONE # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=amad18@student.aau.dk
#SBATCH --output=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.out
#SBATCH --error=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.err
#SBATCH --partition=naples


PD=$(pwd)
CONFIG_FILE="${1}"

for TOPO in $(ls confs) ; do
    for FAILCHUNK in $(ls confs/${TOPO}/failure_chunks) ; do
        sbatch scripts/run-tool.sh ${TOPO}/${CONFIG_FILE} confs/${TOPO}/failure_chunks/${FAILCHUNK}
        break
    done
    break
done
