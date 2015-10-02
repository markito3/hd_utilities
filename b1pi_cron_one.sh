#!/bin/bash
date_token=`cat /u/scratch/$USER/b1pi_date.txt`
export TODAYS_DATE=$date_token
export BMS_OSNAME=`/group/halld/Software/build_scripts/osrelease.pl`
export BUILD_DIR=/u/scratch/gluex/nightly/$TODAYS_DATE/$BMS_OSNAME
export B1PI_TEST_DIR=/group/halld/Software/scripts/b1pi_test
export RUN_DIR=/u/scratch/$USER/b1pi/$TODAYS_DATE/$BMS_OSNAME

# Setup environment based on sim-recon build we're using 
source ${BUILD_DIR}/sim-recon/$BMS_OSNAME/setenv.sh
export JANA_CALIB_CONTEXT="variation=mc"

# do the test
rm -rfv $RUN_DIR
mkdir -pv $RUN_DIR
cd $RUN_DIR
$B1PI_TEST_DIR/b1pi_test.sh -n 150000
export PLOTDIR=/group/halld/www/halldweb/html/b1pi/$TODAYS_DATE/$BMS_OSNAME
mkdir -pv $PLOTDIR
cp -v *.pdf *.gif *.html $PLOTDIR
exit
