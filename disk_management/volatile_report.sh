#!/bin/bash
report_file=/tmp/volatile_oldest.html
rm -f $report_file
/group/halld/Software/hd_utilities/disk_management/volatile_html.py > $report_file
mv $report_file /group/halld/www/halldweb/html/disk_management/
