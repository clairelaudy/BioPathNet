#!/usr/bin/env bash

set -e
set -o pipefail

if [[ $# -lt 3 || "$1" == "-h" || "$1" == "--help" ]] ; then
    echo "Usage: $(basename $0) <BioPathNet_dir> <input_conf> <job_name> <job_dep> [command [container_arguments]]" >&2
    echo "This will use the current working directory for outputs." >&2
    echo "'command' may be: 'run' (the default), 'visualize', 'predict', 'eval_and_predict', 'visualize_graph', 'eval_and_predict_inductive', or 'visualize_inductive'. " >&2
    echo "Set job_dep to 0 for no SLURM dependency." >&2
    exit 2
fi

module load apptainer cuda

bpn_dir="$1"
shift
echo "bpn_dir: $bpn_dir" >&2

input_conf="$1"
shift
echo "input_conf: $input_conf" >&2

bpn_cmd="$1"
shift
echo "bpn_cmd: $bpn_cmd" >&2

job_name="$1"
shift
echo "job_name: $job_name" >&2

job_dep="$1"
shift
echo "job_dep: $job_dep" >&2

dep_arg=""
if [[ $job_dep -ne 0 ]] ; then
    dep_arg="--dependency=after:${job_dep}"
fi

if cat $input_conf | grep DATA_DIR ; then
    echo "ERROR: the input config file contains placeholders." >&2
    echo "You must run 'prepare_expe.sh' or edit the config file with appropriate directories." >&2
    exit 3
fi

work_dir="$(pwd)"

if [ ! -f $work_dir/biopathnet.sif ] ; then
    echo "ERROR: I cannot find a 'biopathnet.sif' container." >&2
    echo "Call 'bin/prepare_expe.sh' first."
    exit 4
fi

echo "Config:" >&2
cat ${input_conf} >&2

cmd="sbatch \
    --parsable \
    --job-name $job_name \
    $dep_arg \
    -p gpu \
    -q gpu \
    --gres=gmem=80G,gpu:1 \
    --mem=64G \
    apptainer \
        run \
            --nv \
            --writable-tmpfs \
            --cleanenv \
            --bind ${bpn_dir}:/BioPathNet \
            --bind $HOME \
            biopathnet.sif -f ${bpn_cmd}  --gpus [0] -c ${input_conf} --biopathnet /BioPathNet $@"

echo "Submitting:" >&2
echo $cmd >&2
$cmd  # Outputs the SLURMID on stdout for capture
