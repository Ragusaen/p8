# MPLS-Kit

MPLS Data plane Toolkit.


Code for the paper "MPLS-Kit: An MPLS Data Plane Toolkit",
a Python 3 library and tool for generation and simulation of MPLS data planes.


## Licence
Copyright (C) 2020-2022.

All rights reserved.

 * This project and its files can not be copied to third parties and/or distributed,
   and may only be used for evaluation purposes.

All rights reserved.

This program is distributed WITHOUT ANY WARRANTY; without even the
implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

## Dependencies:

Required python packages and their versions are listed in the file `requirements.txt`.
If you use `pip` as your Python package manger, you can install the dependencies by executing:

`pip install -r requirements.txt`


# Usage Examples

## Generate and simulate from command line with a random topology

You can test the tool from command line by executing in a linux terminal from the root directory of this code:

`python3 tool_simulate.py --conf example/config.yaml  --failure_chunk_file example/fail.yaml --output_file dp.json --result_folder results`

Files `config.yaml` and `fail.yaml` are found in the `example` directory.

The generated data plane will be placed in `dp.json`

The files with the results for each simulation can be found in the `results` folder

In this case all configuration parameters were taken from the `config` file.


## Generate and simulate from command line loading an existing topology_path

You can also test the tool from command line in the case of reading the topology from an existing file and passing the protocol parameters as command line arguments.
For this, executing in a linux terminal from the root directory of this code:

`python3 tool_simulate.py --topology example/abilene.json --result_folder results/abilene --rsvp --rsvp_num_lsps 20 --rsvp_tunnels_per_pair 1 --php`


### Simulation results file format
The simulation results file is a CSV file with one row per failure scenario and the following columns:
 - success: Number of succesfully delivered packets, or equivalently, number of succesful flows.
 - total: Total number of attempts/flows.
 - loops: Number of packets that ended in a forwarding loop.

## From Jupyter Notebooks

Open and explore the notebooks included together with the code:
 - `mpls_kit_demo.ipynb`: Provides a notebook providing three complete generation and simulation scenarios (random, custom and external topologies). Displays results and generated tables and provides control for the parameters. This allows the user to interact with the library in a natural way and to explore the results in depth.
 - `mpls_fwd_gen-performance.ipynb`: Notebook for measuring and plotting the generator's performance. Warning: it might take several minutes to complete its calculations.


To install Jupyter, you have many available options, for example https://jupyter.org/install ,or also the Anaconda data science suite (https://www.anaconda.com/) also includes it.  
