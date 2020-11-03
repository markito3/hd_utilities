#!/bin/sh
#
#$ -S /bin/sh
#$ -V
#$ -j y
#$ -o led.log
#$ -cwd
#$ -pe mpi 5

RUNDIR="data/"
CMD="./fcal_chainify"

MINRUN="0"
MAXRUN="58000"
NUMRUNPERCHAIN="5"

PIDS=""

printf "Starting %s script with %s...\n" "$CMD" "$NSLOTS"

for f in $(find "${RUNDIR}" -name "data_*.root" -type f) ; do
  m="$(printf "$f\n" | sed 's/data_/chain_/')"
  $CMD "$f" "$m" "$NUMRUNPERCHAIN" "$MINRUN" "$MAXRUN" & PIDS="$PIDS $!"
done

for p in $(printf "%s\n" $PIDS) ; do
  wait "$p"
done

printf "%s script over" "$CMD"