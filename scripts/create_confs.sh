#!/bin/bash
#SBATCH --partition=naples,dhabi,rome


PD=$(pwd)

source ${PD}/venv/bin/activate

rm confs/*/conf*

for TOPO in $(ls topologies) ; do
  scripts/run-createconfs.sh ${TOPO}
done

