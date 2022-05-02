#!/bin/bash
#SBATCH --partition=naples,dhabi,rome


PD=$(pwd)

EXECUTOR="sbatch"
if [ "$1" = "no" ]; then
  EXECUTOR=""
fi

FILTER="$2"

source ${PD}/venv/bin/activate

rm confs/*/conf*
rm confs/*/flows.yml

for TOPO in $(ls topologies/${FILTER}*) ; do
  $EXECUTOR scripts/run-createconfs.sh ${TOPO}
done

