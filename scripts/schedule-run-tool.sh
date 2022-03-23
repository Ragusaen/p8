#!/bin/bash
#SBATCH --mail-type=FAIL # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=amad18@student.aau.dk
#SBATCH --output=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.out
#SBATCH --error=/nfs/home/student.aau.dk/amad18/slurm-output/gen-net-%j.err
#SBATCH --partition=naples,dhabi,rome
#SBATCH --mem=16G

PD=$(pwd)
CONFIG_FILE="${1}.yml"

for TOPO in $(ls topologies) ; do
    TOPONAME=${TOPO/.json/}
    for CONF in $(ls confs/${TOPONAME}/${CONFIG_FILE}) ; do
        sbatch scripts/run-tool.sh ${CONF}
	done
done

