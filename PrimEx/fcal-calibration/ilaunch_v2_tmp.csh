#!/bin/tcsh -f
set period=$1
set wfname=primex-fcal-gains-matching
set i=$2
set imax=$3

while ( $i < $imax )
    set wf=$wfname-$period-$i
    ./igo_auto_tmp.csh $i $period $wfname
    echo $wf $period $i
    python icontrol.py $wf $period $i
    @ i ++
    echo $i
end
