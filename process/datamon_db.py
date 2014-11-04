#!/usr/bin/env python
#
# Class for storing data monitoring information
# Currently only MySQL DBs are supported
#
# Author: Sean Dobbs (s-dobbs@northwestern.edu), 2014

import MySQLdb

class datamon_db:
    """Class for interaction with data monitoring DB"""
    def __init__(self, new_dbhost='hallddb.jlab.org'):
        self.verbose = False
        ## store connection information
        self.dbhost = new_dbhost
        self.dbuser = 'datmon'
        self.dbpasswd = ''       ## current we are configured for password-less access
        self.db_name = 'data_monitoring'

        ## initialize connection
        self.db_conn = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpasswd, db=self.db_name)
        self.db = self.db_conn.cursor()

        ## table information
        self.table_names = [ "sc_hits", "cdc_hits", "cdc_hits", "fdc_hits", "bcal_hits", "bcal_energies", "fcal_hits", "tof_hits", "tagm_hits", "tagh_hits", "ps_hits", "cdc_calib", "fdc_calib", "fcal_calib", "bcal_calib", "tof_calib", "sc_calib", "tagh_calib", "tagm_calib", "analysis_data" ]

        ## table definitions
        self.analysis_data = [ ("num_pos_tracks","INTEGER"), ("num_neg_tracks","INTEGER"), ("num_proton_tracks","INTEGER"), 
                               ("num_piplus_tracks","INTEGER"), ("num_piminus_tracks","INTEGER"),  ("num_kplus_tracks","INTEGER"),
                               ("num_good_pos_tracks","INTEGER"),  ("num_good_neg_tracks","INTEGER"), ("num_good_proton_tracks","INTEGER"), 
                               ("num_good_piplus_tracks","INTEGER"),  ("num_good_piminus_tracks","INTEGER"), ("num_good_kplus_tracks","INTEGER"),

                               ("num_neutraL_showers","INTEGER"), ("num_good_neutral_showers","INTEGER"), 

                               ("num_bcal_showers","INTEGER"), ("num_fcal_showers","INTEGER"), ("num_tof_points","INTEGER"), 
                               ("num_sc_hits","INTEGER"), ("num_tagh_hits","INTEGER"), ("num_tagm_hits","INTEGER"), 
                               ("num_bcal_track_matches","INTEGER"), ("num_fcal_track_matches","INTEGER"), ("num_tof_track_matches","INTEGER"), ("num_sc_track_matches","INTEGER") ] 

        self.bcal_geom_info = [ ('quad1_layer1_up', 'INTEGER'), ('quad1_layer1_down', 'INTEGER'), ('quad1_layer2_up', 'INTEGER'), ('quad1_layer2_down', 'INTEGER'), 
                                ('quad1_layer3_up', 'INTEGER'), ('quad1_layer3_down', 'INTEGER'), ('quad1_layer4_up', 'INTEGER'), ('quad1_layer4_down', 'INTEGER'), 
                                ('quad2_layer1_up', 'INTEGER'), ('quad2_layer1_down', 'INTEGER'), ('quad2_layer2_up', 'INTEGER'), ('quad2_layer2_down', 'INTEGER'), 
                                ('quad2_layer3_up', 'INTEGER'), ('quad2_layer3_down', 'INTEGER'), ('quad2_layer4_up', 'INTEGER'), ('quad2_layer4_down', 'INTEGER'), 
                                ('quad3_layer1_up', 'INTEGER'), ('quad3_layer1_down', 'INTEGER'), ('quad3_layer2_up', 'INTEGER'), ('quad3_layer2_down', 'INTEGER'), 
                                ('quad3_layer3_up', 'INTEGER'), ('quad3_layer3_down', 'INTEGER'), ('quad3_layer4_up', 'INTEGER'), ('quad3_layer4_down', 'INTEGER'), 
                                ('quad4_layer1_up', 'INTEGER'), ('quad4_layer1_down', 'INTEGER'), ('quad4_layer2_up', 'INTEGER'), ('quad4_layer2_down', 'INTEGER'), 
                                ('quad4_layer3_up', 'INTEGER'), ('quad4_layer3_down', 'INTEGER'), ('quad4_layer4_up', 'INTEGER'), ('quad4_layer4_down', 'INTEGER') ]

    def CloseDB(self):
        self.db_conn.commit()
        self.db_conn.close()

    def ClearDB(self):
        ## be careful with this!!
        #self.db.execute("DROP TABLE *")  
        for table in self.table_names:
            print "clearing " + table + "..."
            self.db.execute('DELETE FROM ' + table)
        ## reset autoincrement counters
        self.db.execute('ALTER TABLE run_info AUTO_INCREMENT = 1')
        self.db.execute('ALTER TABLE version_info AUTO_INCREMENT = 1')
        self.db_conn.commit()


    def DefineTables(self):
        """Define all the tables that we need"""
        ## meta info
        self.db.execute('CREATE TABLE run_info (runid INTEGER PRIMARY KEY AUTO_INCREMENT, run_num INTEGER, num_events INTEGER, beam_current DOUBLE, luminosity DOUBLE)')
        self.db.execute('CREATE TABLE version_info (version_id INTEGER PRIMARY KEY AUTO_INCREMENT, data_type VARCHAR(64), software_release VARCHAR(64), production_timestamp TIMESTAMP, dataVersionString VARCHAR(255))')

        ## raw data
        self.db.execute('CREATE TABLE sc_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["pad"+str(x)+"_hits INTEGER," for x in range(1,30)]) + ' pad30_hits INTEGER)')
        self.db.execute('CREATE TABLE cdc_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["superlayer"+str(x)+"_hits INTEGER," for x in range(1,7)]) + ' superlayer7_hits INTEGER)')
        self.db.execute('CREATE TABLE fdc_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["plane"+str(x)+"_hits INTEGER," for x in range(1,72)]) + ' plane72_hits INTEGER)')
        self.db.execute('CREATE TABLE bcal_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["sector"+str(x)+"_hits," for x in range(1,48)]) + ' sector48_hits)')

        bcal_hits_tbl = ""
        bcal_energies_tbl = ""
        n = 1
        for (name,typename) in bcal_geom_info:
            bcal_hits_tbl += "bcalhits_" + name + "  "  + typename
            bcal_energies_tbl += "bcalenergies_" + name + "  "  + typename
            if n != len(bcal_geom_info):
                bcal_hits_tbl += ", "
                bcal_energies_tbl += ", "
                n += 1
        self.db.execute('CREATE TABLE bcal_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + bcal_hits_tbl + ')')
        self.db.execute('CREATE TABLE bcal_energies (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + bcal_energies_tbl + ')')
        self.db.execute('CREATE TABLE fcal_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["channel"+str(x)+"_hits INTEGER," for x in range(1,15)]) + ' channel15_hits INTEGER)')
        self.db.execute('CREATE TABLE tof_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["group"+str(x)+"_hits INTEGER," for x in range(1,16)]) + ' group16_hits INTEGER)')

        self.db.execute('CREATE TABLE tagm_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["column"+str(x)+"_hits INTEGER," for x in range(1,12)]) + ' column12_hits INTEGER)')
        self.db.execute('CREATE TABLE tagh_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["sector"+str(x)+"_hits INTEGER," for x in range(1,5)]) + ' sector5_hits INTEGER)')
        self.db.execute('CREATE TABLE ps_hits (runid INTEGER, file_num INTEGER, version_id INTEGER, num_det_events INTEGER, ' + " ".join(["sector"+str(x)+"_hits INTEGER," for x in range(1,10)]) + ' sector10_hits INTEGER)')
        
        ## Calibration
        self.db.execute('CREATE TABLE cdc_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, CDC_resid_mean DOUBLE, CDC_resid_sigma DOUBLE )')
        self.db.execute('CREATE TABLE fdc_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, FDC_resid_mean DOUBLE, FDC_resid_sigma DOUBLE )')
        self.db.execute('CREATE TABLE fcal_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, FCAL_tresol_mean DOUBLE, FCAL_tresol_sigma DOUBLE )')
        self.db.execute('CREATE TABLE bcal_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, BCAL_tresol_mean DOUBLE, BCAL_tresol_sigma DOUBLE )')
        self.db.execute('CREATE TABLE tof_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, TOF_tresol_mean DOUBLE, TOF_tresol_sigma DOUBLE )')
        self.db.execute('CREATE TABLE sc_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, SC_tresol_mean DOUBLE, SC_tresol_sigma DOUBLE )')
        self.db.execute('CREATE TABLE tagh_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, TAGH_tresol_mean DOUBLE, TAGH_tresol_sigma DOUBLE )')
        self.db.execute('CREATE TABLE tagm_calib (runid INTEGER, file_num INTEGER, version_id INTEGER, TAGM_tresol_mean DOUBLE, TAGM_tresol_sigma DOUBLE )')

        ## analysis data
        #db_cmd = 'CREATE TABLE analysis_data (runid INTEGER, file_num INTEGER, version_id INTEGER,'
        db_cmd = 'CREATE TABLE analysis_data (runid INTEGER, file_num INTEGER, '
        for (name,type) in self.analysis_data:
            db_cmd += name + ' ' + type + ', '
        db_cmd += ' version_id INTEGER )'
        self.db.execute(db_cmd)
        

        ## views
        self.db.execute('CREATE VIEW sc_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(pad"+str(x)+"_hits)," for x in range(1,30)])  + ' sum(pad30_hits) FROM sc_hits JOIN run_info ON sc_hits.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW cdc_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(superlayer"+str(x)+"_hits)," for x in range(1,7)])  + ' sum(superlayer7_hits) FROM cdc_hits JOIN run_info ON cdc_hits.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW fdc_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(plane"+str(x)+"_hits)," for x in range(1,72)])  + ' sum(plane72_hits) FROM fdc_hits JOIN run_info ON fdc_hits.runid=run_info.runid  GROUP BY run_num, version_id')

        bcal_hits_sum_tbl = ""
        bcal_energies_sum_tbl = ""
        n = 1
        for (name,typename) in bcal_geom_info:
            bcal_hits_sum_tbl += "sum(bcalhits_" + name + ")  " 
            bcal_energies_sum_tbl += "sum(bcalenergies_" + name + ")  " 
            if n != len(bcal_geom_info):
                bcal_hits_sum_tbl += ", "
                bcal_energies_sum_tbl += ", "
                n += 1

        self.db.execute('CREATE VIEW bcal_hits_run AS SELECT run_num, version_id, ' + bcal_hits_sum_tbl  + ' FROM bcal_hits JOIN run_info ON bcal_hits.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW bcal_energies_run AS SELECT run_num, version_id, ' + bcal_energies_sum_tbl  + ' FROM bcal_energies JOIN run_info ON bcal_energies.runid=run_info.runid  GROUP BY run_num, version_id')
        ##self.db.execute('CREATE VIEW bcal_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(sector"+str(x)+"_hits)," for x in range(1,48)])  + ' sum(sector48_hits) FROM bcal_hits JOIN run_info ON bcal_hits.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW fcal_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(channel"+str(x)+"_hits)," for x in range(1,15)])  + ' sum(channel15_hits) FROM fcal_hits JOIN run_info ON fcal_hits.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW tof_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(group"+str(x)+"_hits)," for x in range(1,16)])  + ' sum(group16_hits) FROM tof_hits JOIN run_info ON tof_hits.runid=run_info.runid  GROUP BY run_num, version_id')

        self.db.execute('CREATE VIEW tagm_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(column"+str(x)+"_hits)," for x in range(1,12)])  + ' sum(column12_hits) FROM tagm_hits JOIN run_info ON tagm_hits.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW tagh_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(sector"+str(x)+"_hits)," for x in range(1,5)])  + ' sum(sector5_hits) FROM tagh_hits JOIN run_info ON tagh_hits.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW ps_hits_run AS SELECT run_num, version_id, ' + " ".join(["sum(sector"+str(x)+"_hits)," for x in range(1,10)])  + ' sum(sector10_hits) FROM ps_hits JOIN run_info ON ps_hits.runid=run_info.runid  GROUP BY run_num, version_id')

        self.db.execute('CREATE VIEW cdc_calib_run AS SELECT run_num, version_id, sum(CDC_resid_mean), sum(CDC_resid_sigma) FROM cdc_calib JOIN run_info ON cdc_calib.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW fdc_calib_run AS SELECT run_num, version_id, sum(FDC_resid_mean), sum(FDC_resid_sigma) FROM fdc_calib JOIN run_info ON fdc_calib.runid=run_info.runid  GROUP BY run_num, version_id')

        self.db.execute('CREATE VIEW bcal_calib_run AS SELECT run_num, version_id, sum(BCAL_tresol_mean), sum(BCAL_tresol_sigma) FROM bcal_calib JOIN run_info ON bcal_calib.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW fcal_calib_run AS SELECT run_num, version_id, sum(FCAL_tresol_mean), sum(FCAL_tresol_sigma) FROM fcal_calib JOIN run_info ON fcal_calib.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW tof_calib_run AS SELECT run_num, version_id, sum(TOF_tresol_mean), sum(TOF_tresol_sigma) FROM tof_calib JOIN run_info ON tof_calib.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW sc_calib_run AS SELECT run_num, version_id, sum(SC_tresol_mean), sum(SC_tresol_sigma) FROM sc_calib JOIN run_info ON sc_calib.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW tagh_calib_run AS SELECT run_num, version_id, sum(TAGH_tresol_mean), sum(TAGH_tresol_sigma) FROM tagh_calib JOIN run_info ON tagh_calib.runid=run_info.runid  GROUP BY run_num, version_id')
        self.db.execute('CREATE VIEW tagm_calib_run AS SELECT run_num, version_id, sum(TAGM_tresol_mean), sum(TAGM_tresol_sigma) FROM tagm_calib JOIN run_info ON tagm_calib.runid=run_info.runid  GROUP BY run_num, version_id')

        db_cmd = 'CREATE VIEW analysis_data_run AS SELECT run_num, '
        for (name,type) in self.analysis_data:
            db_cmd += 'sum(' + name + '), '
        db_cmd += 'version_id FROM analysis_data JOIN run_info ON analysis_data.runid=run_info.runid  GROUP BY run_num, version_id'
        self.db.execute(db_cmd)
        
        self.db_conn.commit()

    def InsertData(self, table_name, values):
        if(len(values) == 0):
            print 'Trying to add data to DB without any data'
        db_cmd = 'INSERT INTO ' + table_name + ' VALUES (' + " ".join(['%s,' for i in xrange(len(values)-1)]) +  ' %s)'
        if(self.verbose):
            print db_cmd + '  <--  ' + str(values)
        #print "Insert cmd = " + str(db_cmd)
        self.db.execute(db_cmd, values)
        self.db_conn.commit()

    ### Functions to deal with meta data
    def CreateRun(self, run_num):
        db_cmd = "INSERT INTO run_info (run_num) VALUES (%s)"
        self.db.execute(db_cmd, [run_num])
        self.db_conn.commit()

    def AddRunInfo(self, run_num, num_events, beam_current, luminosity):
        ## do some type checking
        #self.InsertData('run_info', [runid, run_num, num_events, beam_current, luminosity])  
        db_cmd = "UPDATE run_info SET num_events=%s,beam_current=%,luminosity=%s WHERE runid=%s"
        self.db.execute(db_cmd, [num_events, beam_current, luminosity, runid])
        self.db_conn.commit()
        
        # get the id of the run we just added
        return self.GetRunID(run_num)

#    def AddVersionInfo(self, version_id, data_type, software_release, production_timestamp, data_version_string)
#        ## do some type checking
#        self.InsertData('version_info', [version_id, data_type, software_release, production_timestamp, data_version_string])
        
    def GetRunID(self, run_num):
        self.db.execute('SELECT runid FROM run_info WHERE run_num=%s', (int(run_num),))
        run_info = self.db.fetchone()
        #print 'Got RUNID = ' + str(run_info)
        if run_info == None:
            return -1
        else:
            return int(run_info[0])
 
    ### Functions to add data
    def AddCDCHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('cdc_hits', [runid, file_num, version_id, num_events] + values)
    def AddFDCHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('fdc_hits', [runid, file_num, version_id, num_events] + values)
    def AddFCALHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('fcal_hits', [runid, file_num, version_id, num_events] + values)
    def AddBCALHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('bcal_hits', [runid, file_num, version_id, num_events] + values)
    def AddBCALEnergies(self, runid, file_num, version_id, num_events, values):
        self.InsertData('bcal_energies', [runid, file_num, version_id, num_events] + values)
    def AddTOFHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('tof_hits', [runid, file_num, version_id, num_events] + values)
    def AddSCHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('sc_hits', [runid, file_num, version_id, num_events] + values)
    def AddTAGHHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('tagh_hits', [runid, file_num, version_id, num_events] + values)
    def AddTAGMHits(self, runid, file_num, version_id, num_events, values):
        self.InsertData('tagm_hits', [runid, file_num, version_id, num_events] + values)

    def AddCDCCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('cdc_calib', [runid, file_num, version_id, num_events] + values)
    def AddFDCCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('fdc_calib', [runid, file_num, version_id, num_events] + values)
    def AddFCALCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('fcal_calib', [runid, file_num, version_id, num_events] + values)
    def AddBCALCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('bcal_calib', [runid, file_num, version_id, num_events] + values)
    def AddTOFCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('tof_calib', [runid, file_num, version_id, num_events] + values)
    def AddSCCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('st_calib', [runid, file_num, version_id, num_events] + values)
    def AddTAGHCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('tagh_calib', [runid, file_num, version_id, num_events] + values)
    def AddTAGMCalib(self, runid, file_num, version_id, num_events, values):
        self.InsertData('tagm_calib', [runid, file_num, version_id, num_events] + values)

    def AddAnalysisInfo(self, runid, file_num, version_id, num_events, values):
        self.InsertData('analysis_data', [runid, file_num, version_id, num_events] + values)

