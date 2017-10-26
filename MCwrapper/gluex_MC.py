#!/usr/bin/env python
##########################################################################################################################
#
# 2017/03 Thomas Britton
#
#   Options:
#      MC variation can be changed by supplying "variation=xxxxx" option otherwise default: mc
#      the number of events to be generated per file (except for any remainder) can be set by "per_file=xxxx" default: 1000
#
#      If the user does not want genr8, geant, smearing, reconstruction to be performed the sequence will be terminated at the first instance of genr8=0,geant=0,mcsmear=0,recon=0 default: all on
#      Similarly, if the user wishes to retain the files created by any step you can supply the cleangenr8=0, cleangeant=0, cleanmcsmear=0, or cleanrecon=0 options.  By default all but the reconstruction files #      are cleaned. 
#
#      The reconstruction step is multi-threaded, for this step, if enabled, the script will use 4 threads.  This threading can be changed with the "numthreads=xxx" option 
#
#      By default the job will run interactively in the local directory.  If the user wishes to submit the jobs to swif the option "swif=1" must be supplied.
#
# SWIF DOCUMENTATION:
# https://scicomp.jlab.org/docs/swif
# https://scicomp.jlab.org/docs/swif-cli
# https://scicomp.jlab.org/help/swif/add-job.txt #consider phase!
#
##########################################################################################################################
from os import environ
from optparse import OptionParser
import os.path
import rcdb
import ccdb
from ccdb.cmd.console_context import ConsoleContext
import ccdb.path_utils
import mysql.connector
import time
import os
import sys
import re
import subprocess
from subprocess import call
import glob

def swif_add_job(WORKFLOW, RUNNO, FILENO,SCRIPT,COMMAND, VERBOSE,PROJECT,TRACK,NCORES,DISK,RAM,TIMELIMIT,OS,DATA_OUTPUT_BASE_DIR):

        
	# PREPARE NAMES
	STUBNAME = str(RUNNO) + "_" + str(FILENO)
	JOBNAME = WORKFLOW + "_" + STUBNAME

	# CREATE ADD-JOB COMMAND
	# job
        #try removing the name specification
	add_command = "swif add-job -workflow " + WORKFLOW #+ " -name " + JOBNAME
	# project/track
	add_command += " -project " + PROJECT + " -track " + TRACK
	# resources
	add_command += " -cores " + NCORES + " -disk " + DISK + " -ram " + RAM + " -time " + TIMELIMIT + " -os " + OS
	# stdout
	add_command += " -stdout " + DATA_OUTPUT_BASE_DIR + "/log/" + str(RUNNO) + "_stdout." + STUBNAME + ".out"
	# stderr
	add_command += " -stderr " + DATA_OUTPUT_BASE_DIR + "/log/" + str(RUNNO) + "_stderr." + STUBNAME + ".err"
	# tags
	add_command += " -tag run_number " + str(RUNNO)
	# tags
	add_command += " -tag file_number " + str(FILENO)
	# script with options command
	add_command += " "+SCRIPT  +" "+ COMMAND

	if(VERBOSE == True):
		print "job add command is \n" + str(add_command)

        if(int(NCORES)==1 and int(RAM[:-2]) >= 10 and RAM[-2:]=="GB" ):
                print "SciComp has a limit on RAM requested per thread, as RAM is the limiting factor."
                print "This will likely cause an AUGER-SUBMIT error."
                print "Please either increase NCORES or decrease RAM requested and try again."
                exit(1)
	# ADD JOB
        if add_command.find(';')!=-1 or add_command.find('&')!=-1 :#THIS CHECK HELPS PROTECT AGAINST A POTENTIAL HACK VIA CONFIG FILES
                print "Nice try.....you cannot use ; or &"
                exit(1)
	status = subprocess.call(add_command.split(" "))

def  qsub_add_job(VERBOSE, WORKFLOW, RUNNUM, FILENUM, indir, COMMAND, NCORES, DATA_OUTPUT_BASE_DIR, TIMELIMIT, RUNNING_DIR, MEMLIMIT, QUEUENAME, LOG_DIR ):
        #name
        STUBNAME = str(RUNNUM) + "_" + str(FILENUM)
	JOBNAME = WORKFLOW + "_" + STUBNAME
       
        sub_command="qsub MCqsub.submit"
       
        qsub_ml_command=""
        bits=NCORES.split(":")
        if (len(bits)==3):
                qsub_ml_command ="nodes="+bits[0]+":"+bits[1]+":ppn="+bits[2]
        elif (len(bits)==2):
                qsub_ml_command ="nodes="+bits[0]+":ppn="+bits[1]

        shell_to_use="/bin/bash "
        if (indir[len(indir)-3]=='c'):
                shell_to_use="/bin/csh "

        f=open('MCqsub.submit','w')
        f.write("#!/bin/sh -f"+"\n" )
        f.write("#PBS"+" -N "+JOBNAME+"\n" )
        f.write("#PBS"+" -l "+qsub_ml_command+"\n" )
        f.write("#PBS"+" -o "+LOG_DIR+"/log/"+JOBNAME+".out"+"\n" )
        f.write("#PBS"+" -e "+LOG_DIR+"/log/"+JOBNAME+".err"+"\n" )
        f.write("#PBS"+" -l walltime="+TIMELIMIT+"\n" )
        if (QUEUENAME != "DEF"):
                f.write("#PBS"+" -q "+QUEUENAME+"\n" )
        f.write("#PBS"+" -l mem="+MEMLIMIT+"\n" ) 
        f.write("#PBS"+" -m a"+"\n" )  
        f.write("#PBS"+" -p 0"+"\n" )
        f.write("#PBS -c c=2 \n")
        f.write("NCPU=\\ \n")
        f.write("NNODES=\\ \n")    
       
       # f.write("trap \'\' 2 9 15 \n" )
        f.write(shell_to_use+indir+" "+COMMAND+"\n" )
        f.write("exit 0\n")
        f.close()

        time.sleep(0.25)

        if ( DATA_OUTPUT_BASE_DIR != LOG_DIR ) :
                status = subprocess.call("mkdir -p "+LOG_DIR+"/log/", shell=True)


        mkdircom="mkdir -p "+DATA_OUTPUT_BASE_DIR+"/log/"

        status = subprocess.call(mkdircom, shell=True)
        status = subprocess.call(sub_command, shell=True)
        if ( VERBOSE == False ) :
                status = subprocess.call("rm MCqsub.submit", shell=True)
        

def  condor_add_job(VERBOSE, WORKFLOW, RUNNUM, FILENUM, indir, COMMAND, NCORES, DATA_OUTPUT_BASE_DIR, TIMELIMIT, RUNNING_DIR ):
        STUBNAME = str(RUNNUM) + "_" + str(FILENUM)
	JOBNAME = WORKFLOW + "_" + STUBNAME

        mkdircom="mkdir -p "+DATA_OUTPUT_BASE_DIR+"/log/"

        f=open('MCcondor.submit','w')
        f.write("Executable = "+indir+"\n") 
        f.write("Arguments  = "+COMMAND+"\n")
        f.write("Error      = "+DATA_OUTPUT_BASE_DIR+"/log/"+"error_"+JOBNAME+".log\n")
        f.write("Log      = "+DATA_OUTPUT_BASE_DIR+"/log/"+"out_"+JOBNAME+".log\n")
        f.write("RequestCpus = "+NCORES+"\n")
        f.write("Queue 1\n")
        f.close()
        
        add_command="condor_submit -name "+JOBNAME+" MCcondor.submit"
        if add_command.find(';')!=-1 or add_command.find('&')!=-1 or mkdircom.find(';')!=-1 or mkdircom.find('&')!=-1:#THIS CHECK HELPS PROTEXT AGAINST A POTENTIAL HACK VIA CONFIG FILES
                print "Nice try.....you cannot use ; or &"
                exit(1)

        status = subprocess.call(mkdircom, shell=True)
        status = subprocess.call(add_command, shell=True)
        status = subprocess.call("rm MCcondor.submit", shell=True)


def showhelp():
        helpstring= "variation=%s where %s is a valid jana_calib_context variation string (default is \"mc\")\n"
        helpstring+= " per_file=%i where %i is the number of events you want per file/job (default is 10000)\n"
        helpstring+= " numthreads=%i sets the number of threads to use to %i.  Note that this will overwrite the NCORES set in MC.config\n"
        helpstring+= " generate=[0/1] where 0 means that the generation step and any subsequent step will not run (default is 1)\n"
        helpstring+= " geant=[0/1] where 0 means that the geant step and any subsequent step will not run (default is 1)\n"
        helpstring+= " mcsmear=[0/1] where 0 means that the mcsmear step and any subsequent step will not run (default is 1)\n"
        helpstring+= " recon=[0/1] where 0 means that the reconstruction step will not run (default is 1)\n"
        helpstring+= " cleangenerate=[0/1] where 0 means that the generation step will not be cleaned up after use (default is 1)\n"
        helpstring+= " cleangeant=[0/1] where 0 means that the geant step will not be cleaned up after use (default is 1)\n"
        helpstring+= " cleanmcsmear=[0/1] where 0 means that the mcsmear step will not be cleaned up after use (default is 1)\n"
        helpstring+= " cleanrecon=[0/1] where 0 means that the reconstruction step will not run (default is 1)\n"
        helpstring+= " batch=[0/1/2] where 1 means that jobs will be submitted, 2 will do the same as 1 but also run the workflow in the case of swif (default is 0 [interactive])\n"
        helpstring+= " logdir=[path] will direct the .out and .err files to the specified path for qsub\n"
        return helpstring

########################################################## MAIN ##########################################################
	
def main(argv):
	parser_usage = "gluex_MC.py config_file Run_Number/Range num_events [all other options]\n\n where [all other options] are:\n\n "
        parser_usage += showhelp()
	parser = OptionParser(usage = parser_usage)
	(options, args) = parser.parse_args(argv)

	#check if there are enough arguments
	if(len(argv)<3):
		parser.print_help()
		return

	#check if the needed arguments are valid
	if len(args[1].split("="))>1 or len(args[2].split("="))>1:
		parser.print_help()
		return

        #!!!!!!!!!!!!!!!!!!REQUIRED COMMAND LINE ARGUMENTS!!!!!!!!!!!!!!!!!!!!!!!!
        CONFIG_FILE = args[0]
        RUNNUM = args[1]
	EVTS = int(args[2])
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        print "*********************************"
        print "Welcome to v1.9 of the MCwrapper"
        print "Thomas Britton 10/24/17"
        print "*********************************"

	#load all argument passed in and set default options
        VERBOSE    = False

        TAGSTR="I_dont_have_one"

        DATA_OUTPUT_BASE_DIR    = "UNKNOWN_LOCATION"#your desired output location
        
       
        ENVFILE = "my-environment-file"#change this to your own environment file
        
        GENERATOR = "genr8"
        GENCONFIG = "NA"

        eBEAM_ENERGY="rcdb"
        COHERENT_PEAK="rcdb"
        MIN_GEN_ENERGY="4"
        MAX_GEN_ENERGY="12"
        RUNNING_DIR="./"
	SQLITEPATH="no_sqlite"

        GEANTVER = 4        
        BGFOLD="DEFAULT"

        CUSTOM_MAKEMC="DEFAULT"
        CUSTOM_GCONTROL="0"
        CUSTOM_PLUGINS="None"

        BATCHSYS="NULL"
        QUEUENAME="DEF"
        #-------SWIF ONLY-------------
        # PROJECT INFO
        PROJECT    = "gluex"          # http://scicomp.jlab.org/scicomp/#/projects
        TRACK      = "simulation"     # https://scicomp.jlab.org/docs/batch_job_tracks
        
        # RESOURCES for swif jobs
        NCORES     = "8"               # Number of CPU cores
        DISK       = "10GB"            # Max Disk usage
        RAM        = "20GB"            # Max RAM usage
        TIMELIMIT  = "300minutes"      # Max walltime
        OS         = "centos7"        # Specify CentOS65 machines

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        VERSION  = "mc"
        CALIBTIME="notime"
        BASEFILENUM=0
	PERFILE=10000
	GENR=1
	GEANT=1
	SMEAR=1
	RECON=1
	CLEANGENR=1
	CLEANGEANT=1
	CLEANSMEAR=1
	CLEANRECON=0
        BATCHRUN=0
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #loop over config file and set the "parameters"
        f = open(CONFIG_FILE,"r")

        for line in f:
                if len(line)==0:
                       continue
                if line[0]=="#":
                       continue

                parts=line.split("=")

                if len(parts)==1:
                        #print "Warning! No Sets given"
                        continue
                
                if len(parts)>2 and str(parts[0]).upper() != "VARIATION":
                        print "warning! I am going to have a really difficult time with:"
                        print line
                        print "I'm going to just ignore it and hope it isn't a problem...."
                        continue
                        
                        
                rm_comments=[]
                if len(parts)>1:
                        rm_comments=parts[len(parts)-1].split("#")
                        
                j=-1
                for i in parts:
                        j=j+1
                        i=i.strip()
                        parts[j]=i
                
                if str(parts[0]).upper()=="VERBOSE" :
                        if rm_comments[0].strip().upper()=="TRUE" or rm_comments[0].strip() == "1":
                                VERBOSE=True
                elif str(parts[0]).upper()=="PROJECT" :
                        PROJECT=rm_comments[0].strip()
                elif str(parts[0]).upper()=="TRACK" :
                        TRACK=rm_comments[0].strip()
                elif str(parts[0]).upper()=="NCORES" :
                        NCORES=rm_comments[0].strip()
                elif str(parts[0]).upper()=="DISK" :
                        DISK=rm_comments[0].strip()
                elif str(parts[0]).upper()=="RAM" :
                        RAM=rm_comments[0].strip()
                elif str(parts[0]).upper()=="TIMELIMIT" :
                        TIMELIMIT=rm_comments[0].strip()
                elif str(parts[0]).upper()=="OS" :
                        OS=rm_comments[0].strip()
                elif str(parts[0]).upper()=="DATA_OUTPUT_BASE_DIR" :
                        DATA_OUTPUT_BASE_DIR=rm_comments[0].strip()
                elif str(parts[0]).upper()=="ENVIRONMENT_FILE" :
                        ENVFILE=rm_comments[0].strip()
                elif str(parts[0]).upper()=="GENERATOR" :
                        GENERATOR=rm_comments[0].strip()
                elif str(parts[0]).upper()=="GEANT_VERSION" :
                        GEANTVER=rm_comments[0].strip()
                elif str(parts[0]).upper()=="WORKFLOW_NAME" :
                        WORKFLOW=rm_comments[0].strip()
                        if WORKFLOW.find(';')!=-1 or WORKFLOW.find('&')!=-1 :#THIS CHECK HELPS PROTEXT AGAINST A POTENTIAL HACK IN WORKFLOW NAMES
                                print "Nice try.....you cannot use ; or & in the name"
                                exit(1)
                elif str(parts[0]).upper()=="GENERATOR_CONFIG" :
                        GENCONFIG=rm_comments[0].strip()
                elif str(parts[0]).upper()=="CUSTOM_MAKEMC" :
                        CUSTOM_MAKEMC=rm_comments[0].strip()
                elif str(parts[0]).upper()=="CUSTOM_GCONTROL" :
                        CUSTOM_GCONTROL=rm_comments[0].strip()
                elif str(parts[0]).upper()=="BKG" :
                        BGFOLD=rm_comments[0].strip()
                elif str(parts[0]).upper()=="EBEAM_ENERGY" :
                        eBEAM_ENERGY=rm_comments[0].strip()
                elif str(parts[0]).upper()=="COHERENT_PEAK" :
                        COHERENT_PEAK=rm_comments[0].strip()
                elif str(parts[0]).upper()=="GEN_MIN_ENERGY" :
                        MIN_GEN_ENERGY=rm_comments[0].strip()
                elif str(parts[0]).upper()=="GEN_MAX_ENERGY" :
                        MAX_GEN_ENERGY=rm_comments[0].strip()
                elif str(parts[0]).upper()=="TAG" :
                        TAGSTR=rm_comments[0].strip()
                elif str(parts[0]).upper()=="CUSTOM_PLUGINS" :
                        CUSTOM_PLUGINS=rm_comments[0].strip()
                elif str(parts[0]).upper()=="BATCH_SYSTEM" :
                        batch_sys_parts=rm_comments[0].strip().split(":")
                        BATCHSYS=batch_sys_parts[0]
                        if len(batch_sys_parts) > 1 :
                                QUEUENAME=batch_sys_parts[1]
                elif str(parts[0]).upper()=="RUNNING_DIRECTORY" :
                        RUNNING_DIR=rm_comments[0].strip()
                elif str(parts[0]).upper()=="VARIATION" :
                        if ( len(parts)>2 ) :
                                VERSION=str(parts[1]).split("calibtime")[0].split("#")[0].strip()
                                CALIBTIME=str(parts[2]).split("#")[0].strip()
                        else:
                                VERSION=rm_comments[0].strip()
		elif str(parts[0]).upper()=="SQLITEPATH" :
			SQLITEPATH=rm_comments[0].strip()
                else:
                        print "unknown config parameter!! "+str(parts[0])
	#loop over command line arguments 
	
        LOG_DIR = DATA_OUTPUT_BASE_DIR  #set LOG_DIR=DATA_OUTPUT_BASE_DIR

        for argu in args:
		argfound=0
		flag=argu.split("=")
		#redundat check to jump over the first 4 arguments
		if(len(flag)<2):
			continue
		else:#toggle the flags as user defines
			if flag[0]=="variation":
				argfound=1

				VERSION=flag[1]
                                CALIBTIME="notime"
 #                               for part in range(2,len(flag)):
  #                                      VERSION+="="+flag[part]
                        if flag[0]=="calibtime":
				argfound=1
                               	CALIBTIME=flag[1]
			if flag[0]=="per_file":
				argfound=1
				PERFILE=int(flag[1])
                        if flag[0]=="base_file_number":
				argfound=1
				BASEFILENUM=int(flag[1])
			if flag[0]=="genr8":
				argfound=1
				GENR=int(flag[1])
			if flag[0]=="geant":
				argfound=1
				GEANT=int(flag[1])
			if flag[0]=="mcsmear":
				argfound=1
				SMEAR=int(flag[1])
			if flag[0]=="recon":
				argfound=1
				RECON=int(flag[1])
			if flag[0]=="cleangenerate":
				argfound=1
				CLEANGENR=int(flag[1])
			if flag[0]=="cleangeant":
				argfound=1
				CLEANGEANT=int(flag[1])
			if flag[0]=="cleanmcsmear":
				argfound=1
				CLEANSMEAR=int(flag[1])
			if flag[0]=="cleanrecon":
				argfound=1
				CLEANRECON=int(flag[1])
			if flag[0]=="batch":
				argfound=1
				BATCHRUN=int(flag[1])
			if flag[0]=="numthreads":
				argfound=1
				NCORES=str(flag[1])
                        if flag[0]=="logdir":
				argfound=1
				LOG_DIR=str(flag[1])
			if argfound==0:
				print "WARNING OPTION: "+argu+" NOT FOUND!"
	
      #  if str(GEANTVER)=="3":
      #          print "!!!  Warning: Geant 3 detected! NumThreads has been set to 1"
      #          print "!!!  This is done to ensure efficient use of resources while running and should provide faster job starts."
      #          NCORES="2"
      #          print ""
                
        if DATA_OUTPUT_BASE_DIR == "UNKNOWN_LOCATION":
                print "I doubt that the system will find "+DATA_OUTPUT_BASE_DIR+" so I am saving you the embarassment and stopping this"
                return

        name_breakdown=GENCONFIG.split("/")
        CHANNEL = name_breakdown[len(name_breakdown)-1].split(".")[0]

	#print a line indicating SWIF or Local run
	if BATCHRUN == 0 or BATCHSYS=="NULL":
		print "Locally simulating "+args[2]+" "+CHANNEL+" Events"
	else:
		print "Creating "+WORKFLOW+" to simulate "+args[2]+" "+CHANNEL+" Events"
	# CREATE WORKFLOW
       
        if (BATCHSYS.upper() =="SWIF" and int(BATCHRUN) != 0):
		status = subprocess.call(["swif", "create", "-workflow", WORKFLOW])

	#calculate files needed to gen
	FILES_TO_GEN=EVTS/PERFILE
	REMAINING_GEN=EVTS%PERFILE

	indir=os.environ.get('MCWRAPPER_CENTRAL')
        
        script_to_use = "/MakeMC.csh"
        if environ['SHELL']=="/bin/bash" :
                script_to_use = "/MakeMC.sh"
        
        indir+=script_to_use

        if len(CUSTOM_MAKEMC)!= 0 and CUSTOM_MAKEMC != "DEFAULT":
                indir=CUSTOM_MAKEMC

        if str(indir) == "None":
                print "MCWRAPPER_CENTRAL not set"
                return

	outdir=DATA_OUTPUT_BASE_DIR
	
        #if local run set out directory to cwd
	if outdir[len(outdir)-1] != "/" :
                outdir+= "/"

	#for every needed file call the script with the right options

        #need two loops 1) for when RUNNUM is a number and 2) when it contains a "-" as in 11366-11555 or RunPeriod2017-02
        # for 2) use rcdb to get a list of the runs of a runperiod and amount of data.  Normalize number of events. Loop through list calling with the runnumbers from rcdb and their normalized num_events*requested events
        RunType=str(RUNNUM).split("-")
        

        if len(RunType) != 1 :
                event_sum=0.
                #Make python rcdb calls to form the vector
                db = rcdb.RCDBProvider("mysql://rcdb@hallddb/rcdb")

                dbhost = "hallddb.jlab.org"
                dbuser = 'datmon'
                dbpass = ''
                dbname = 'data_monitoring'

                runlow=0
                runhigh=0

                if RunType[0] != "RunPeriod":
                        runlow=RunType[0]
                        runhigh=RunType[1]
                else:
                        cnx = mysql.connector.connect(user='ccdb_user', database='ccdb', host='hallddb.jlab.org')
                        cursor = cnx.cursor()
                        #ccddb = ccdb.CCDBProvider("mysql://ccdb_user@hallddb/ccdb")
                
                        #runhigh=ccdbcon.session.query("select runMax from runRanges where name = test2")
                        #runlow=runRange[0]
                        #runhigh=runRange[1]
                        runrange_name=""
                        for npart in RunType:
                                if npart=="RunPeriod":
                                        continue
                                else:
                                        runrange_name=runrange_name+npart

                        cursor.execute("select runMin,runMax from runRanges where name = '"+runrange_name+"'")
                        runRange = cursor.fetchall()
                        runlow=runRange[0][0]
                        runhigh=runRange[0][1]
                        print runRange
                        #cursor.close()
                        #cnx.close()
                        print str(runlow)+"-->"+str(runhigh)

                table = db.select_runs("@is_production and @status_approved",runlow,runhigh).get_values(['event_count'],True)
                #print table
                #print len(table)
                for runs in table:
                        if len(table)<=1:
                                break
                        event_sum = event_sum + runs[1]

                #print event_sum
                sum2=0.
                for runs in table: #do for each job
                        #print runs[0]
                        if len(table) <= 1:
                                break
                        num_events_this_run=int(((float(runs[1])/float(event_sum))*EVTS)+.5)
                        sum2=sum2+int(((float(runs[1])/float(event_sum))*EVTS)+.5)
                        #print num_events_this_run
                        
                        if num_events_this_run == 0:
			        continue

                       #do for each file needed
                        FILES_TO_GEN_this_run=num_events_this_run/PERFILE
	                REMAINING_GEN_this_run=num_events_this_run%PERFILE

                        for FILENUM_this_run in range(1, FILES_TO_GEN_this_run + 2):
                                num_this_file=PERFILE

                                if FILENUM_this_run == FILES_TO_GEN_this_run +1:
			                num_this_file=REMAINING_GEN_this_run
                                
                                if num_this_file == 0:
			                continue

		                COMMAND=str(BATCHRUN)+" "+ENVFILE+" "+GENCONFIG+" "+str(outdir)+" "+str(runs[0])+" "+str(BASEFILENUM+FILENUM_this_run+-1)+" "+str(num_this_file)+" "+str(VERSION)+" "+str(CALIBTIME)+" "+str(GENR)+" "+str(GEANT)+" "+str(SMEAR)+" "+str(RECON)+" "+str(CLEANGENR)+" "+str(CLEANGEANT)+" "+str(CLEANSMEAR)+" "+str(CLEANRECON)+" "+str(BATCHSYS)+" "+str(NCORES).split(':')[-1]+" "+str(GENERATOR)+" "+str(GEANTVER)+" "+str(BGFOLD)+" "+str(CUSTOM_GCONTROL)+" "+str(eBEAM_ENERGY)+" "+str(COHERENT_PEAK)+" "+str(MIN_GEN_ENERGY)+" "+str(MAX_GEN_ENERGY)+" "+str(TAGSTR)+" "+str(CUSTOM_PLUGINS)+" "+str(PERFILE)+" "+str(RUNNING_DIR)+" "+str(SQLITEPATH)
                                if BATCHRUN == 0 or BATCHSYS=="NULL":
                                        #print str(runs[0])+" "+str(BASEFILENUM+FILENUM_this_run+-1)+" "+str(num_this_file)
        			        os.system(str(indir)+" "+COMMAND)
	        	        else:
                                        if BATCHSYS.upper()=="SWIF":
                        	                swif_add_job(WORKFLOW, runs[0], BASEFILENUM+FILENUM_this_run+-1,str(indir),COMMAND,VERBOSE,PROJECT,TRACK,NCORES,DISK,RAM,TIMELIMIT,OS,DATA_OUTPUT_BASE_DIR)
                                        elif BATCHSYS.upper()=="QSUB":
                                                qsub_add_job(VERBOSE, WORKFLOW, runs[0], BASEFILENUM+FILENUM_this_run+-1, indir, COMMAND, NCORES, DATA_OUTPUT_BASE_DIR, TIMELIMIT, RUNNING_DIR, RAM, QUEUENAME, LOG_DIR )
                                        elif BATCHSYS.upper()=="CONDOR":
                                                condor_add_job(VERBOSE, WORKFLOW, runs[0], BASEFILENUM+FILENUM_this_run+-1, indir, COMMAND, NCORES, DATA_OUTPUT_BASE_DIR, TIMELIMIT, RUNNING_DIR )
                        #print "----------------"
                
        else:
	        for FILENUM in range(1, FILES_TO_GEN + 2):
		        num=PERFILE
		        #last file gets the remainder
		        if FILENUM == FILES_TO_GEN +1:
			        num=REMAINING_GEN
		        #if ever asked to generate 0 events....just don't
		        if num == 0:
			        continue
                
		        COMMAND=str(BATCHRUN)+" "+ENVFILE+" "+GENCONFIG+" "+str(outdir)+" "+str(RUNNUM)+" "+str(BASEFILENUM+FILENUM+-1)+" "+str(num)+" "+str(VERSION)+" "+str(CALIBTIME)+" "+str(GENR)+" "+str(GEANT)+" "+str(SMEAR)+" "+str(RECON)+" "+str(CLEANGENR)+" "+str(CLEANGEANT)+" "+str(CLEANSMEAR)+" "+str(CLEANRECON)+" "+str(BATCHSYS)+" "+str(NCORES).split(':')[-1]+" "+str(GENERATOR)+" "+str(GEANTVER)+" "+str(BGFOLD)+" "+str(CUSTOM_GCONTROL)+" "+str(eBEAM_ENERGY)+" "+str(COHERENT_PEAK)+" "+str(MIN_GEN_ENERGY)+" "+str(MAX_GEN_ENERGY)+" "+str(TAGSTR)+" "+str(CUSTOM_PLUGINS)+" "+str(PERFILE)+" "+str(RUNNING_DIR)+" "+str(SQLITEPATH)
               
	                #print COMMAND
		        #either call MakeMC.csh or add a job depending on swif flag
                        if BATCHRUN == 0 or BATCHSYS=="NULL":
        			os.system(str(indir)+" "+COMMAND)
	        	else:
                                if BATCHSYS.upper()=="SWIF":
                        	        swif_add_job(WORKFLOW, RUNNUM, BASEFILENUM+FILENUM+-1,str(indir),COMMAND,VERBOSE,PROJECT,TRACK,NCORES,DISK,RAM,TIMELIMIT,OS,DATA_OUTPUT_BASE_DIR)
                                elif BATCHSYS.upper()=="QSUB":
                                        qsub_add_job(VERBOSE, WORKFLOW, RUNNUM, BASEFILENUM+FILENUM+-1, indir, COMMAND, NCORES, DATA_OUTPUT_BASE_DIR, TIMELIMIT, RUNNING_DIR, RAM, QUEUENAME, LOG_DIR )
                                elif BATCHSYS.upper()=="CONDOR":
                                        condor_add_job(VERBOSE, WORKFLOW, RUNNUM, BASEFILENUM+FILENUM+-1, indir, COMMAND, NCORES, DATA_OUTPUT_BASE_DIR, TIMELIMIT, RUNNING_DIR )

                                        
        if BATCHRUN == 1 and BATCHSYS.upper() == "SWIF":
                print "All Jobs created.  Please call \"swif run "+WORKFLOW+"\" to run"
        elif BATCHRUN == 2 and BATCHSYS.upper()=="SWIF":
                swifrun = "swif run "+WORKFLOW
                subprocess.call(swifrun.split(" "))
                
if __name__ == "__main__":
   main(sys.argv[1:])
