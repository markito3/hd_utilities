#!/bin/bash

iter=$1
period=$2

path=/work/halld/home/gxproj2/calibration/fcal

h=${period/period_/}
#61321->61329  61335
#61340->61344  61355-61355
#61378->61391  61356-61411
#61434->61439  61412-61454
#61470->61479  61455-61484
#61490->61499  61485-61504
#61510->61519  61505-61569
#61621->61629  61570-
#61700->61709
#61750->61759
#61810->61818
#61874->61879
#61930->61939
#61950->61956
min_run=(61321 61340 61378 61434 61470 61590 61510 61621 61700 61750 61810 61874 61930 61950)
max_run=(61339 61377 61433 61469 61489 61509 61620 61699 61749 61809 61873 61929 61949 61956)

dname=$path/$period/g$iter
echo $dname $h
cd $dname
ccdb add FCAL/gains -r ${min_run[$h]}-${max_run[$h]} new_gains.txt

