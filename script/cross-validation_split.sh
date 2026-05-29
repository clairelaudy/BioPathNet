#!/usr/bin/bash

set -e #x
#set -o pipefail

if [[ $# -lt 3 || $# -gt 4 || "$1" == "-h" || "$1" == "--help" ]] ; then
    echo "Usage: $0 <input_file> <percent_validated> <percent_tested> [type]" >&2
    echo "This script will split the input_file into 3 files suffixe with __validation, __test and _ train." >&2
    echo "Percentages are rounded down, the remaining lines goes to the __train file." >&2
    echo "Files are written in the working directory, wherever is the input_file from." >&2
    echo "If type is given, only lines with edge type matching the type regexp will go into validation and test." >&2
    exit 2
fi

INPUT="$1"
NAME=$(basename "$INPUT")
STEM="${NAME%.*}"
EXT="${NAME##*.}"

echo "$STEM.$EXT" >&2

check_percent() {
    if [[ $1 -gt 100 ]] ; then
        echo "Wrong percentage: $1" >&2
        exit 1
    fi
    if [[ $1 -eq 0 ]] ; then
        echo "Wrong percentage: $1" >&2
        exit 1
    fi
}

P_VALI="$2"
check_percent $P_VALI

P_TEST="$3"
check_percent $P_TEST

TYPE=".*"
if [[ $# -eq 4 ]] ; then
    TYPE="$4"
fi
EDGE="^\w*\t${TYPE}\t\w*$"

if [[ $P_VALI -gt 100 ]] ; then
    echo "<percent_validated> is greater than 100" >&2
    exit 78
fi
if [[ $P_TEST -gt 100 ]] ; then
    echo "<percent_tested> is greater than 100" >&2
    exit 78
fi
if [[ $((P_TEST + P_VALID)) -gt 100 ]] ; then
    echo "<percent_validated>+<percent_tested> is greater than 100" >&2
    exit 78
fi

lc() {
    wc -l "$1" | cut -d " " -f 1
}

##############
echo "SHUFFLE" >&2
##############

SHUFFLED="${STEM}__shuffled.$EXT"

INPUT_NLINES=$(lc "$INPUT")
echo "$INPUT_NLINES lines in input" >&2

shuf "$1" > "$SHUFFLED"

NLINES=$(lc "$SHUFFLED")
echo "$NLINES lines in $SHUFFLED" >&2

if [[ $NLINES -ne $INPUT_NLINES ]] ; then
    echo "Missing lines after shuffling" >&2
    exit 153
fi

##############
echo "VALIDATION" >&2
##############

N_VALI=$((P_VALI * NLINES / 100))
echo "$N_VALI lines for validation"
if [[ $N_VALI -eq 0 ]] ; then
    echo "Zero lines in validation" >&2
    exit 1
fi

# Nth first edges
echo "Make ${STEM}__validation.$EXT ..." >&2
cat "$SHUFFLED" | grep -P "$EDGE" | head -n $N_VALI > "${STEM}__validation.$EXT"

VALI_N=$(lc "${STEM}__validation.$EXT")
if [[ $VALI_N -ne $N_VALI ]] ; then
    echo "validation file has $VALI_N lines but ought to be $N_VALI" >&2
    # exit 153
fi

##############
echo "TEST" >&2
##############

TMP=$(mktemp)

cat "$SHUFFLED" | tail -n $((NLINES - N_VALI)) > $TMP

NTT=$(lc $TMP)
if [[ $NTT -eq 0 ]] ; then
    echo "Zero lines in test+train" >&2
    exit 1
fi

N_TEST=$((P_TEST * NLINES / 100))
echo "$N_TEST lines for test" >&2
if [[ $N_TEST -eq 0 ]] ; then
    echo "Zero lines in test" >&2
    exit 1
fi

# Nth first edges
echo "Make ${STEM}__test.$EXT ..." >&2
cat "$TMP" | grep -P "$EDGE" | head -n $N_TEST > "${STEM}__test.$EXT"

TEST_N=$(lc "${STEM}__test.$EXT")
if [[ $TEST_N -ne $N_TEST ]] ; then
    echo "test file has $TEST_N lines but ought to be $N_TEST" >&2
    # exit 153
fi

##############
echo "TRAIN" >&2
##############

echo "Make ${STEM}__train.$EXT ..." >&2
cat "$TMP" | tail -n $((NTT - N_TEST)) > "${STEM}__train.$EXT"

TRAIN_N=$(lc "${STEM}__train.$EXT")
echo "$TRAIN_N lines in train" >&2
if [[ $TRAIN_N -eq 0 ]] ; then
    echo "Zero lines in train" >&2
    exit 153
fi

echo "Done" >&2

