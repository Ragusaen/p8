#!/bin/bash

PD=$(pwd)
CONFIG_FILE="${1}"
AMOUNT_TO_TEST="${2}"
count=0

source ~/p8/venv/bin/activate

for TOPO in $(ls confs) ; do
    if [ AMOUNT_TO_TEST > count ]
    then
        for FAILCHUNK in $(ls confs/${TOPO}/failure_chunks) ; do
            python3 ${PD}/tool_simulate.py --conf "confs/${TOPO}/${CONFIG_FILE}.yml" --failure_chunk_file ${FAILCHUNK} --result_folder "results/${CONFIG_FILE}"
        done
    fi
done
