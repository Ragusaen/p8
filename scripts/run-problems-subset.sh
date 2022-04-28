#!/bin/bash

PD=$(pwd)
CONFIG="${1}"
AMOUNT_TO_TEST="${2}"
count=1

source ~/p8/venv/bin/activate

for TOPO in $(ls confs) ; do
    if [ $count -le $AMOUNT_TO_TEST ]
    then
        for FAILCHUNK in $(ls confs/${TOPO}/failure_chunks) ; do
            python3 ${PD}/tool_simulate.py --conf "confs/${TOPO}/conf_${CONFIG}.yml" --failure_chunk_file "confs/${TOPO}/failure_chunks/${FAILCHUNK}" --result_folder "results/${CONFIG}/${TOPO}"
        done
    fi
    (( count++ ))
done