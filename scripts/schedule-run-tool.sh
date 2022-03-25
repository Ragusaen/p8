#!/bin/bash
#SBATCH --mail-type=NONE # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=amad18@student.aau.dk
#SBATCH --output=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.out
#SBATCH --error=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.err
#SBATCH --partition=naples,dhabi,rome


PD=$(pwd)
CONFIG_FILE="${1}.yml"

for TOPO in $(ls confs) ; do
    sbatch scripts/run-tool.sh confs/${TOPO}/${CONFIG_FILE}
done

