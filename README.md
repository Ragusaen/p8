# Code for FBR: Dynamic Memory-Aware Fast Rerouting

This is code for the paper *FBR: Dynamic Memory-Aware Fast Rerouting*. This repository is based on a version of MPLS-Kit, which is available at https://github.com/juartinv/mplskit.


# Reproduce results in paper
To reproduce the results from the paper you can run the script: `./run_experiments.sh "" all`
This will however take a long time to run - See next section
This script will set up a virtual env and install the required packages. It will create the configurations for all topologies in the topologies folder and run the configs on all algorithms used in the paper. Lastly, it will parse the results which can be seen in the latex folder. Here, the files `memory_failure_data.tex` and `latency_full_median.tex` are the ones in the paper. 


# Options to limit amount of topologies and algorithms
The first argument is a filter for which topologies to run. For example, `./run_experiments.sh zoo_A all` would run all the zoo topologies starting with A.
The second argument is which algorithms that should be run. For all algorithms you can simply write `all`. If you only want to run let's say rmpls and FBR with 4 rules limit per router per demand it would be: `./run_experiments.sh "" rmpls input-disjoint_max-mem=4`

The possible algorithms are: 
 [Conf-name]                     |     [Name in paper]
 inout-disjoint_max-mem=X                  FBR
 tba-complex_max-mem=X                     E-CA
 rmpls                                     R-MPLS
 gft                                       GFT-CA
 rsvp-fn                                   RSVP-FN
 tba-simple                                B-CA

where X is a integer limit on the number of rules per router per demand.




TODO: Download topologies or have them in the package?
TODO: Fix incorrect legends in latex files. 
TODO: Output png of plots
