#!/bin/bash

PD=$(pwd)
CONFIG_FILE="${1}.yml"
VERBOSE=$2

source ${PD}/venv/bin/activate

for TOPO in $(ls topologies) ; do
    TOPONAME=${TOPO/.json/}
    for CONF in $(ls confs/${TOPONAME}/${CONFIG_FILE}) ; do
        scripts/run-tool.sh ${CONF} ${VERBOSE}
	done
done

