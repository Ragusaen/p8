#!/bin/bash

rm confs/*/conf*

for TOPO in $(ls topologies) ; do
  python3 create_confs.py --topology topologies/${TOPO} --conf confs --keep_failure_chunks --result_folder results/${TOPO}
done

