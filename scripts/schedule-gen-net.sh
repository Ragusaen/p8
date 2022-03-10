#!/bin/bash

for TOPO in $(ls topologies) ; do
    scripts/gen-net.sh scripts/conf-1.yml networks/conf-1/${TOPO} topologies/${TOPO}
    break
done
