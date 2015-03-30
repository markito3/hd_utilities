#!/bin/tcsh

# Update tables for jobs
../status.sh

# Create _aux table that contains information about launch from stdout files
time mysql -hhallddb -ufarmer farming < ./create_offline_monAux.sql
# If we need to reset the table, use this
# time mysql -hhallddb -ufarmer farming -e "drop table PROJECT_aux"

# Fill in _aux table
# If running this part again, delete processed_job_info.txt
echo "running get_processed_job_info_from_stdout.sh........."
time ./get_processed_job_info_from_stdout.sh

# Write out results to table aux
# CAUTION: Running this command multiple times will result
# in multiple entries for the same run and file.
echo "running write_inserts_aux.pl........."
time write_inserts_aux.pl < processed_job_info.txt | mysql -hhallddb -ufarmer farming

# Create txt file containing merged info from tables [project]Job and [project]_aux
echo "running create_jobs_data_from_db.csh........."
time ./create_jobs_data_from_db.csh

# Format the txt file
echo "running format_jobs_data.C........."
make
time ./format_jobs_data

# Run analysis to create plots
time root -b -q analyze.C

# Publish on web
mkdir -p /work/halld/data_monitoring/launch_analysis/PROJECT/
set HTMLDIR = "/work/halld/data_monitoring/launch_analysis/PROJECT/"
cp ./mystyle.css ./results.html ./figures/00[1-8]* ./figures/01[1-2]* ./figures/014* $HTMLDIR


