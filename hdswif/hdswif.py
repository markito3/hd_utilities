#!/usr/bin/env python

###############################################################
#
# 2015/07/22 Kei Moriya
# 
# Control swif workflow and set up all configuration
# parameters.
#
# The functions create, delete, run are just wrappers
# for swif.
#
# The function add will add jobs with configurable
# run parameters.
#
# Much of this code has been borrowed from Sean's monitoring
# scripts.
#
###############################################################

from optparse import OptionParser
import os.path
import sys
import re
import subprocess

import parse_swif

VERBOSE = False

def create(workflow):
    os.system("swif create " + workflow)

def cancel(workflow):
    os.system("swif cancel " + workflow)

def delete(workflow):
    os.system("swif cancel " + workflow + " -delete")

def list():
    os.system("swif list")

def run(workflow):
    os.system("swif run " + workflow + " -errorlimit none")

def runnjobs(workflow, n):
    os.system("swif run " + workflow + " -joblimit " + n + " -errorlimit none")

def status(workflow):
    os.system("swif status " + workflow)

def fullstatus(workflow, format):
    os.system("swif status " + workflow + " -runs -summary -display " + format)

def resubmit(workflow, ram):
    os.system("swif modify-jobs " + workflow + " -ram add " + str(ram) + "gb -problems AUGER-OVER_RLIMIT")
    os.system("swif run " + workflow + " -errorlimit none")

def is_number(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def find_files(RUNPERIOD, FORMATTED_RUN, FORMATTED_FILE):
    # NOTE:
    # Since we search for files with names
    # Run-[run]/hd_rawdata_[run]_[file].evio
    # we do automatically take out any files that
    # were placed in the wrong directory.
    #
    # If option "all" is used for either run or file,
    # find will be run with *.
    topdir = "/mss/halld/RunPeriod-" + RUNPERIOD + "/rawdata/Run*" + FORMATTED_RUN + "*"
    os.system("find " + topdir + " -name 'hd_rawdata_*" + FORMATTED_RUN + "*_*" + FORMATTED_FILE + "*.evio' > ___files.txt")
    file_handler = open("___files.txt",'r')
    count = 0
    _file_list = [] # create empty list

    # Fill list with files found
    for line in file_handler:
        line = line.rstrip() # remove newline
        _file_list.insert(len(_file_list),line)
        if(VERBOSE == True):
            print str(len(_file_list)) + " "  + line
        count += 1
    os.system("rm -f ___files.txt")
    return _file_list

def add_job(WORKFLOW, config_dict, mssfile):

    # This is so VERBOSE is consistent throughout the program
    global VERBOSE

    # Get back FORMATTED_RUN, FORMATTED_FILE from mssfile (full path to evio file)
    # set name for regexp run_file
    match = ""
    thisrun = 0
    thisfile = 0
    try:
        match = re.search(r"(\d\d\d\d\d\d)_(\d\d\d)",mssfile) # _\d\d\d
        thisrun  = match.group(1)
        thisfile = match.group(2)
    except AttributeError:
        "could not find regexp for " + mssfile

    if(thisrun == 0 or thisfile == 0):
        print "couldn't find run and file number in " + mssfile

    else:
        if(VERBOSE == True):
            print "thisrun = " + thisrun + "  thisfile = " + thisfile

        # Get input file basename
        basename = os.path.basename(mssfile)
        if(VERBOSE == True):
            print "basename = " + basename

        # Create SCRIPT_ARGS
        SCRIPT_ARGS = str(config_dict['ENVFILE'] + " " + basename + " " + thisrun + " " + thisfile + " " +
                          config_dict['OUTPUT_TOPDIR'] + " " + str(config_dict['NCORES']))
        if(VERBOSE == True):
            print "SCRIPT_ARGS = " + SCRIPT_ARGS

        add_command = str("swif add-job -workflow " + WORKFLOW + " -project " + config_dict['PROJECT'] + " \\\n") \
            + str(" -track " + config_dict['TRACK'] + " -cores " + str(config_dict['NCORES']) + " -disk " + str(config_dict['DISK']) + "g \\\n") \
            + str(" -ram " + str(config_dict['RAM']) + "g -time " + str(config_dict['TIMELIMIT']) + "h -os " + config_dict['OS'] + " \\\n") \
            + str(" -input " + basename + " " + mssfile + " \\\n") \
            + str(" -tag user_run " + thisrun + " -tag user_file " + thisfile + " \\\n") \
            + str(" -name offmon" + "_" + thisrun + "_" + thisfile + " \\\n") \
            + str(" -stdout " + config_dict['OUTPUT_TOPDIR'] + "/log/" + thisrun + "/stdout_" + thisrun + "_" + thisfile + ".out \\\n") \
            + str(" -stderr " + config_dict['OUTPUT_TOPDIR'] + "/log/" + thisrun + "/stderr_" + thisrun + "_" + thisfile + ".err \\\n") \
            + str(config_dict['SCRIPTFILE'] + " " + SCRIPT_ARGS)
        
        if(VERBOSE == True):
            print "job add command is \n" + str(add_command)
            
        # Execute swif add for this job
        os.system(add_command)
    
def main(argv):
    global VERBOSE

    # Default to run over all runs, files
    RUN            = "all"
    FILE           = "all"
    FORMATTED_RUN  = ""
    FORMATTED_FILE = ""
    USERCONFIGFILE = ""

    # Read in command line args
    parser = OptionParser(usage = str("\n"
                                      + "hdswif.py [option] [workflow]\n"
                                      + "[option] = {create, list, run (n), status, add, resubmit, summary, cancel, delete}\n"
                                      + "Options for add:\n"
                                      + "-r (run) -f (file)\n"
                                      + "-c [config]\n"
                                      + "options in [ ] are required, options in ( ) are optional for running\n"
                                      + ""
                                      + "(use -V 1 for verbose mode)"))
    parser.add_option("-r","--run    ", dest="run",
                      help="run")
    parser.add_option("-f","--file   ", dest="file",
                      help="file")

    parser.add_option("-c","--config ", dest="config",
                      help="config")
    parser.add_option("-V","--verbose    ",dest="verbose",
                      help="verbose")
    
    (options, args) = parser.parse_args(argv)

    if(options.run):
        RUN = options.run
    if(options.file):
        FILE = options.file

    if(options.config):
        USERCONFIGFILE = options.config
    if(options.verbose):
        VERBOSE = True

    # If we want to list workflows, list and exit
    if(len(args)==1 and args[0] == "list"):
        list()
        return

    # For all other cases, make sure we have at least two arguments,
    # swif command and workflow
    if(len(args) < 2):
        parser.print_help()
        return

    WORKFLOW = args[1]

    # If we want to create workflow, create it and exit
    if(args[0] == "create"):
        create(WORKFLOW)
        return

    # If we want to cancel workflow, cancel and exit
    elif(args[0] == "cancel"):
        cancel(WORKFLOW)
        return

    # If we want to delete workflow, delete it and exit
    elif(args[0] == "delete"):
        delete(WORKFLOW)
        return

    # If we want to run workflow, run it and exit
    elif(args[0] == "run"):
        if(len(args) == 2):
            run(WORKFLOW)
        if(len(args) == 3):
            runnjobs(WORKFLOW, args[2])
        return

    # If we want to check status of workflow, check it and exit
    elif(args[0] == "status"):
        if(len(args) == 2):
            status(WORKFLOW)
        if(len(args) == 3):
            if(not(args[2] == "xml" or args[2] == "json" or args[2] == "simple")):
                print "hdswif.py status [workflow] [display format]"
                print "display format = {xml, json, simple}"
                return
            fullstatus(WORKFLOW, str(args[2]))
        else:
            print "hdswif.py status [workflow] [display format]"
            print "display format = {xml, json, simple}"
            return
        return

    # If we want to create a summary of the workflow, call summary
    elif(args[0] == "summary"):
        # Check if xml output file exists
        filename = str('swif_output_' + WORKFLOW + '.xml')
        if os.path.isfile(filename):
            print 'File ', filename, ' already exists'
            answer = raw_input('Overwrite? (y/n)   ')
            while(not(answer == 'y' or answer == 'n')):
                answer = raw_input('Overwrite? (y/n)   ')
            if answer == 'n':
                print 'abort creating summary file for [', WORKFLOW, ']'
            else:
                # Create the xml file to parse
                print 'Creating XML output file........'
                os.system("swif status " + WORKFLOW + " -runs -summary -display xml > " + filename)
                print 'Created summary file ', filename, '..............'

        # Call parse_swif
        parse_swif.main([filename])
        return

    # If we want to check status of workflow, check it and exit
    elif(args[0] == "resubmit"):
        if(len(args) == 2):
            # Default is to add 2GB of RAM
            resubmit(WORKFLOW,2)
            return
        if(len(args) == 3):
            if(is_number(args[2]) == True):
                resubmit(WORKFLOW, int(args[2]))
                return
            else:
                print "hdswif.py resubmit [workflow] [RAM to add]"
                print "[RAM to add] is in units of GB"
                return
        else:
            print "hdswif.py resubmit [workflow] [RAM to add]"
            print "[RAM to add] is in units of GB"
            return

    # We should only have add left at this stage
    else:
        if(args[0] != "add"):
            print "hdswif.py options:"
            print "create   delete   run  status   add"
            return

    #------------------------------------------+
    #       We are in add mode now             |
    #------------------------------------------+

    # Below is default configuration, is updated
    # if -c config_file is specified
    config_dict = {
        'PROJECT'        : 'gluex',
        'TRACK'          : 'reconstruction',
        'OS'             : 'centos65',
        'RUNPERIOD'      : '2015-03',
        'VERSION'        : '99',                  # Used to specify output top directory
        'OUTPUT_TOPDIR'  : '/volatile/halld/home/gxproj5/hdswif_test/RunPeriod-[RUNPERIOD]/ver[VERSION]', # # Needs to be full path
        'NCORES'         : 6,
        'DISK'           : 40,
        'RAM'            : 5,
        'TIMELIMIT'      : 8,
        'SCRIPTFILE'     : '/home/gxproj5/halld/hdswif/user_script.sh',           # Needs to be full path
        'ENVFILE'        : '/home/gxproj5/halld/hdswif/setup_jlab-2015-03.csh',   # Needs to be full path
        }

    # Read in config file if specified
    if USERCONFIGFILE != '':
        user_dict = {}
        # Check if config file exists
        if (not os.path.isfile(USERCONFIGFILE)) or (not os.path.exists(USERCONFIGFILE)):
            print 'Config file ', USERCONFIGFILE, ' is not a readable file'
            print 'Exiting...'
            exit()

        # Read in user config file
        infile_config = open(USERCONFIGFILE,'r')

        for line in infile_config:

            # Ignore empty lines
            # print 'line = ', line, ' split: ', line.split()
            if len(line.split()) == 0:
                continue

            # Do not update if line begins with #
            if line.split()[0][0] == '#':
                continue

            # Add new key/value pair into user_dict
            user_dict[str(line.split()[0])] = line.split()[1]
        
        #  Update all of the values in config_dict
        # with those specified by the user
        config_dict.update(user_dict)

        if VERBOSE == True:
            print 'Updated config_dict with user config file'
            print 'config_dict is: ', config_dict.items()

    # At this stage we have all the key/value combinations
    # that the user specified. Some of these may depend on
    # other configuration parameters, so update the values
    # containing [key] within the values corresponding to
    # those keys.
    #
    # Example:
    # OUTPUT_TOPDIR /volatile/halld/test/RunPeriod-[RUNPERIOD]/ver[VERSION]
    # depends on other config parameters RUNPERIOD and VERSION
    # 
    # NOTE: The method assumes there are no circular dependencies
    # which would not make sense,
        
    # Iterate over key/value pairs in dictionary
    # If we find a replacement, we need to start over.
    # The parameter found keeps track of whether we found
    # a replacement or not.
    found = 1
    while(found):
        for key, value in config_dict.items():
            found = 0
            
            # print '================================================================'
            # print 'key = ', key, ' value = ', value
            # For each one see if any values contain [P] where
            # P is a different value
            for other_key, other_value in config_dict.items():
                # print 'other_key = ', other_key, ' other_value = ', other_value
                # print 'searching for ', str('[' + other_key + ']')
                if str(value).find(str('[' + other_key + ']')) != -1:
                    # Found replacement
                    found = 1
                    new_value = value.replace(str('[' + other_key + ']'),other_value)
                    # print 'key = ', key, ' new value = ', new_value
                    # Replace new key/value pair into config_dict
                    new_pair = {key : new_value}
                    config_dict.update(new_pair)
                    del new_pair
                    # print '--------------------'
                    
                    # Break out of loop over other_key, other_value
                    break
            # Break out of loop over key, value
            if found == 1:
                break
            
            # If we do not find a replacement we will finish the loop

    if VERBOSE == True:
        print 'config_dict is: ', config_dict.items()

    # config_dict has now been updated if config file was specified
    print "+++   adding jobs to workflow:   " + WORKFLOW + "   +++"
    print "---   Job configuration parameters:   ---"
    print "PROJECT           = " + config_dict['PROJECT']
    print "TRACK             = " + config_dict['TRACK']
    print "OS                = " + config_dict['OS']
    print "NCORES            = " + str(config_dict['NCORES'])
    print "DISK              = " + str(config_dict['DISK'])
    print "RAM               = " + str(config_dict['RAM'])
    print "TIMELIMIT         = " + str(config_dict['TIMELIMIT'])
    print "JOBNAMEBASE       = " + str(config_dict['JOBNAMEBASE'])
    print "RUNPERIOD         = " + config_dict['RUNPERIOD']
    print "VERSION           = " + config_dict['VERSION']
    print "OUTPUT_TOPDIR     = " + config_dict['OUTPUT_TOPDIR']
    print "SCRIPTFILE        = " + config_dict['SCRIPTFILE']
    print "ENVFILE           = " + config_dict['ENVFILE']
    print ""
    print "-----------------------------------------"

    # Format run and file numbers
    if(is_number(RUN) == True):
        FORMATTED_RUN = "{:0>6d}".format(int(RUN))
    elif(RUN == "all"):
        FORMATTED_RUN = "*"
    else:
        FORMATTED_RUN = RUN

    if(is_number(FILE) == True):
        FORMATTED_FILE = "{:0>3d}".format(int(FILE))
    elif(FILE == "all"):
        FORMATTED_FILE = "*"
    else:
        FORMATTED_FILE = FILE

    if(VERBOSE == True):
        print "FORMATTED_RUN = " + FORMATTED_RUN + " FORMATTED_FILE = " + FORMATTED_FILE

    #------------------------------------------+
    #    Find raw evio files to submit         |
    #------------------------------------------+
    file_list = []
    file_list = find_files(config_dict['RUNPERIOD'], FORMATTED_RUN, FORMATTED_FILE)
    if(VERBOSE == True):
        for file in file_list:
            print file
        print "size of file_list is " + str(len(file_list))

    #------------------------------------------+
    #         Add job to workflow              |
    #------------------------------------------+

    # Loop over files found for given run and file
    for mssfile in file_list:
        add_job(WORKFLOW, config_dict, mssfile)

if __name__ == "__main__":
   main(sys.argv[1:])
