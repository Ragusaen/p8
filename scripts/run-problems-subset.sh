#!/bin/bash

PD=$(pwd)
CONFIG_FILE="${1}"
AMOUNT_TO_TEST="${2}"
count=1

source ~/p8/venv/bin/activate

for TOPO in $(ls confs) ; do
    if [ $count -le $AMOUNT_TO_TEST ]
    then
        for FAILCHUNK in $(ls confs/${TOPO}/failure_chunks) ; do
            python3 ${PD}/tool_simulate.py --conf "confs/${TOPO}/${CONFIG_FILE}.yml" --failure_chunk_file "confs/${TOPO}/failure_chunks/${FAILCHUNK}" --result_folder "results/${TOPO}/${CONFIG_FILE}"
        done
    fi
    (( count++ ))
done

rm count
