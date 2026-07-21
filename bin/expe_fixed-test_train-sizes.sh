#!/usr/bin/env bash

set -e
set -o pipefail

if [[ $# -ne 8 ]] ; then
    echo "ERROR usage" >&2
    echo "Run from your experiment directory:" >&2
    echo "$(basename $0) <oncodashkb_dir> <DECIDER_data_dir> <tested_triples_file> <validation_split_perc> <min_subsampling_perc> <incr_subsampling_perc> <max_subsampling_perc> <nb_runs>" >&2
    exit 2
fi

odkb="$(realpath $1)"
decider="$(realpath $2)"
tested="$(realpath $3)"
split="$4"
min="$5"
incr="$6"
max="$7"
nb_runs="$8"

expe="oncodashkb_builds__$(basename $decider)__$(basename -s .txt $tested)__validation-split-$split"
echo "Experience in: $expe" >&2
mkdir -p "$expe"

bpn=$(realpath "$(dirname $0)/..")
# bpn=$(basename $(dirname $(realpath $0/..)))

for run in $(seq $nb_runs) ; do
    for size in $(seq $min $incr $max) ; do
        build="$expe/odkb_sample-$size"
        if [[ -d "$build" ]] ; then
            echo "OncodashKB of size $size% already built in: $build" >&2
        else
            echo "Build OncodashKB of size $size..." >&2
            pushd $odkb
            import_file=$(./make.sh "$decider" "./config/biopathnet.yaml" $size)
            bc_build=$(dirname $(realpath "$import_file"))
            popd
            mv "$bc_build" "$build"
            echo "OncodashKB of size $size built in: $build" >&2
        fi

        if [[ -f "$build/$(basename $tested)" ]] ; then
            echo "Cross-validation splits already generated." >&2
        else
            echo "Generate cross-validation splits..."
            pushd "$build/"
            uv run --project $bpn $bpn/script/cross-validation_split.py skg.txt $split 0 "variant biomarker for treatment"
            cp "$tested" .
            rm skg__test.txt
            ln -s $(basename "$tested") skg__test.txt
            popd
            echo "Cross-validation splits generated."
        fi

        echo "Configure BioPathNet..." >&2
        mkdir -p "$build/run_seed-$run"
        pushd "$build/run_seed-$run/"
        configs=$($bpn/bin/prepare_expe.sh $(realpath ..) $bpn/config/non_independent/run.yaml $bpn/config/non_independent/pred.yaml $bpn/config/non_independent/vis.yaml)
        echo "BioPathNet configured." >&2

        echo "Submit run $run on sample ${size}% with config: $conf" >&2
        conf_train="bpn_run.yaml"
        conf_pred="bpn_pred.yaml"
        conf_vis="bpn_vis.yaml"

        # Submit the training run and get its SLURMID
        jobid=$($bpn/bin/sbatch_apptainer.sh "$bpn" "$conf_train" "run" "Ts${size}r${run}" "0" --seed $run)

        # Make them depends on the training.
        $bpn/bin/sbatch_apptainer.sh "$bpn" "$conf_pred" "predict"   "Ps${size}r${run}" "$jobid" --seed $run
        $bpn/bin/sbatch_apptainer.sh "$bpn" "$conf_vis"  "visualize" "Vs${size}r${run}" "$jobid" --seed $run
        popd
    done # size
done # run

echo "Done building and submitting" >&2
