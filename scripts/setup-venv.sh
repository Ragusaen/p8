#!/bin/bash
#SBATCH --mail-type=FAIL # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=<your-email>
#SBATCH --output=/nfs/home/cs.aau.dk/<your-id>/slurm-output/setup-venv-%j.out 
#SBATCH --error=/nfs/home/cs.aau.dk/<your-id>/slurm-output/setup-venv-%j.err
#SBATCH --partition=naples,dhabi,rome
#SBATCH --mem=16G

let "m=1024*1024"
ulimit -v $m

PYTHON_PROJECT_FOLDER="$1"

cd ${PYTHON_PROJECT_FOLDER}

# Setup a venv (virtual environment) called venv. This creates a folder called 'venv' in the current (project) directory.
python3 -m venv venv
# Activate the venv.
source venv/bin/activate

# Install requirements in the now active venv.
python3 -m pip install -r requirements.txt
