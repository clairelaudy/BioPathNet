#!/bin/sh

set -e
set -o pipefail

if [ $# -lt 2 ] ; then
    echo "Usage: $(basename $0) <input_datadir> <input_confs...>" >&2
    echo "This will use the current working directory for outputs." >&2
    exit 2
fi

module load apptainer cuda

# Need realpath for the underlying BPN run in a container that mounts the CWD.
input_datadir="$(realpath $1)"
shift

first_input_conf="$1"
conf_dir="$(realpath $(dirname $first_input_conf))"

work_dir="$(pwd)"
timestamp="$(date -Iseconds | tr : -)"

bpn_dir="${conf_dir%BioPathNet/*}BioPathNet/"
if [ ! -f ${bpn_dir}/pyproject.toml ] ; then
    echo "ERROR: the directory inferred from the config file path does not contains BioPathNet: '$bpn_dir'"
    exit 3
fi
if [ ! -f $bpn_dir/biopathnet.sif ] ; then
    echo "ERROR: I cannot find a 'biopathnet.sif' container in inferred BioPathNet directory: '${bpn_dir}'" >&2
    echo "Build it with 'bin/build_apptainer.sh' from your BioPathNet directory."
    exit 4
fi
# Link the container.
ln -s -f $bpn_dir/biopathnet.sif

# Instantiate the config file.
for input_conf in "$@" ; do
    name=$(basename "$input_conf")
    stem="${name%.*}"
    ext="${name##*.}"
    cat $input_conf | sed "s,{{DATA_DIR}},${input_datadir},g" | sed "s,{{OUTPUT_DIR}},${work_dir},g" > "${work_dir}/${stem}_${timestamp}.${ext}"
done

echo "Config:" >&2
ls -1 *${timestamp}*

