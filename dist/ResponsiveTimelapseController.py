#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser
import              sys, math, time, datetime, shutil, numpy, threading
from PyQt4          import QtGui, QtCore
from PyQt4.QtGui    import QImage, QPixmap, QLabel
from PIL            import Image, ImageFilter, ImageDraw
from functools      import partial

from ConfocalInterface  import *
from ImageProcessing    import *
from Configuration      import *

smallDelay          = 0.1
bigDelay            = 0.5

class ResponsiveTimelapseController(QtGui.QMainWindow):
    
    def __init__(self):
        super(ResponsiveTimelapseController, self).__init__()
        self.experimentSTOP = True
        self.experimentPAUSE = False
        self.experiment_reloaded = False
        self.oilEscape = False
        self.User_root           = ''
        self.Confocal_output     = ''
        self.Laser1 = '488'
        self.Laser2 = '515'
        self.Laser3 = '594'
        self.Laser_limit = '2'
        self.Setup_job = 'SetupScan'
        self.Overview_job = 'OverviewScan'
        self.Zoom_job = 'ZoomScan'
        self.Laser_assignment_error = False
        load_config(self)
        self.initUI()
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Setup main Window
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
    def initUI(self):
        screen       =  QtGui.QApplication.desktop().screenGeometry().getCoords()
        screenHeight = screen[-1]
        screenWidth  = screen[-2]
        self.setGeometry(screenWidth-680, 30, 600, screenHeight-80)
        self.setWindowTitle('Responsive Timelapse Controller')
        self.setWindowIcon(QtGui.QIcon('RTC.png'))
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtGui.QColor(80,80,80))
        self.setPalette(palette)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Setup Widgets
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
        #start/pause & stop buttons
        self.startpause                     = QtGui.QPushButton('Start')
        self.startpause.setCheckable(True)
        self.startpause.state               = 0
        self.startpause.clicked[bool].connect(partial(self.control_main_loop,action='Start'))
        self.stopbutton                     = QtGui.QPushButton('Stop')
        self.stopbutton.clicked[bool].connect(partial(self.control_main_loop,action='Stop'))
        #timing widgets
        self.TimingLabel1                   = QtGui.QLabel('No. Loops:')
        self.TimingLoops                    = QtGui.QLineEdit('180')
        self.TimingLabel2                   = QtGui.QLabel('Interval (s):')
        self.TimingInterval                 = QtGui.QLineEdit('300')
        self.TimingLabel3                   = QtGui.QLabel('Duration')
        self.TimingDuration                 = QtGui.QLineEdit('15 : 00 : 00')
        self.TimingDuration.setReadOnly(True)
        self.TimingLoops.returnPressed.connect(self.update_duration)
        self.TimingLoops.textChanged.connect(self.update_duration)
        self.TimingInterval.returnPressed.connect(self.update_duration)
        self.TimingInterval.textChanged.connect(self.update_duration)

        #Fileing Widgets
        self.FileRestore                    = QtGui.QPushButton('Load Experiment')
        self.FileRestore.clicked[bool].connect(self.restore_experiment)
        self.FileUserLabel                  = QtGui.QLabel('User:')
        self.FileUserList                   = QtGui.QComboBox()
        #generate user list
        
        userList =  glob.glob(self.User_root + '\\*')                                                  #RELPATH!!!
        for item in userList:
            if os.path.isdir(item):
                userName = item.split('\\')[-1]
                self.FileUserList.addItem(userName)
        self.FileExptNameLabel              = QtGui.QLabel('Experiment Title:')
        self.FileExptName                   = QtGui.QLineEdit('')
        self.FileExptName.returnPressed.connect(self.update_expt_name)
        self.FileExptName.textChanged.connect(self.update_expt_name)
        self.FileUserList.currentIndexChanged['QString'].connect(self.update_expt_name)
#TO DO - Remove this 'FileAddress' from the GUI and instead add it to the 'info' window. Note that the FileAddress.text() is used to get the location to store images, so will need new variable instead.
        self.FileAddress                    = QtGui.QLineEdit('')
        self.FileAddress.setReadOnly(True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Tracking Widgets
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        #info/instruction prompt
        self.TrackingLabel1                 = QtGui.QLabel("Tracking:")
        self.TrackingLaserOff               = QtGui.QRadioButton("OFF")
        self.TrackingLaser1                 = QtGui.QRadioButton(self.Laser1)
        self.TrackingLaser2                 = QtGui.QRadioButton(self.Laser2)
        self.TrackingLaser3                 = QtGui.QRadioButton(self.Laser3)
        self.TrackingLabel2                 = QtGui.QLabel("Channel:")
        self.TrackingAdjustOnOff            = QtGui.QCheckBox('Auto-Adjust?')        
        self.TrackingChannel                = QtGui.QLineEdit('2')
        self.TrackingChannel.setMaxLength(1)
        self.TrackingOV                     = QtGui.QCheckBox('Auto-Focus OV?')
        self.TrackingLaserOff.toggle()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Information Widget
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        #info/instruction prompt
        self.InfoModel                      = QtGui.QStandardItemModel()
        self.InfoModel.setHorizontalHeaderLabels([self.tr("Title"),self.tr("Info")])
        self.InfoModel.setRowCount(5)
        self.InfoModel.setColumnCount(2)
        self.InfoTree                       = QtGui.QTreeView(self)
        self.InfoTree.setFixedHeight(160)
        self.InfoTree.setModel(self.InfoModel)
        self.InfoTree.setHeaderHidden(True)
        self.clear_info()

        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Preview Widgets
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Overview/Setup Image

        self.CurrRed    = True
        self.CurrGreen  = True
        self.CurrBlue   = True
        self.OVRed      = True
        self.OVGreen    = True
        self.OVBlue     = True
        
            #RGB options
        self.PrevOVRed      = QtGui.QCheckBox('R')
        self.PrevOVGreen    = QtGui.QCheckBox('G')
        self.PrevOVBlue     = QtGui.QCheckBox('B')
        self.PrevOVRed.toggle()
        self.PrevOVGreen.toggle()
        self.PrevOVBlue.toggle()
        self.PrevOVRed.stateChanged.connect(lambda: self.change_image_state('OV','Red'))
        self.PrevOVGreen.stateChanged.connect(lambda: self.change_image_state('OV','Green'))
        self.PrevOVBlue.stateChanged.connect(lambda: self.change_image_state('OV','Blue'))
            #OV Image
        self.PrevOVFileName                 = 'Blank.tif'                                              #RELPATH!!!
        self.PrevOVImage                    = QtGui.QImage(self.PrevOVFileName)
        self.PrevOVpixmap                   = QtGui.QPixmap(self.PrevOVImage)
        self.PrevOVlabel                    = QtGui.QLabel()
        self.PrevOVlabel.setPixmap(self.PrevOVpixmap)
        self.PrevOVlabel.mousePressEvent    = self.get_click_position
        self.PrevOVimage_clickable          = False

#transparent layer
        self.PrevOverlaylabel                   = QtGui.QLabel()
        self.PrevOverlaylabel.mousePressEvent   = self.get_click_position
        self.PrevOverlayimage_clickable         = False
        
        #Current Image
            #RGB options
        self.PrevCurrRed      = QtGui.QCheckBox('R')
        self.PrevCurrGreen    = QtGui.QCheckBox('G')
        self.PrevCurrBlue     = QtGui.QCheckBox('B')
        self.PrevCurrRed.toggle()
        self.PrevCurrGreen.toggle()
        self.PrevCurrBlue.toggle()
        self.PrevCurrRed.stateChanged.connect(lambda: self.change_image_state('Curr','Red'))
        self.PrevCurrGreen.stateChanged.connect(lambda: self.change_image_state('Curr','Green'))
        self.PrevCurrBlue.stateChanged.connect(lambda: self.change_image_state('Curr','Blue'))

            #Image
        self.PrevCurrFileName           = 'Blank.tif'                                          #RELPATH!!!
        self.PrevCurrImage              = QtGui.QImage(self.PrevCurrFileName)
        self.PrevCurrpixmap             = QtGui.QPixmap(self.PrevCurrImage)
        self.PrevCurrlabel              = QtGui.QLabel()
        self.PrevCurrlabel.setPixmap(self.PrevCurrpixmap)
        self.PrevCurrimage_clickable    = False

        #Image labels
        self.PrevOVInfoLabel            = QtGui.QLabel('')
        self.PrevCurrInfoLabel          = QtGui.QLabel('')
        
        #setup buttons
        self.Prevsetupscan              = QtGui.QPushButton('Setup Scan')
        self.Prevsetupscan.clicked[bool].connect(self.do_setup_scan)
        self.Prevfinishbutton           = QtGui.QPushButton('Finish')
        self.Prevfinishbutton.clicked[bool].connect(self.finish_clicking)
        self.Prevfinishbutton.setEnabled(False)

        #radio buttons
        self.PrevShowLive               = QtGui.QRadioButton('Live')
        self.PrevUserSelect             = QtGui.QRadioButton('User Select')
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Data Widgets
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #Buttons
        self.clearSelection = QtGui.QPushButton('Clear Selection')
        self.clearSelection.clicked[bool].connect(self.clear_selection)
        self.DataGoTo = QtGui.QPushButton('Go To Selection')
        self.DataGoTo.clicked[bool].connect(lambda: self.go_to())
        
        #Create Model
        self.model      = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels([self.tr("Scan"),self.tr("Job"),self.tr("X"),self.tr("Y"),self.tr("Z"),self.tr("Loops"),self.tr(self.Laser1),self.tr(self.Laser2),self.tr(self.Laser3),self.tr("Pinhole")])

        #Create Tree
        self.tree       = QtGui.QTreeView(self)
        self.selModel   = self.tree.selectionModel()
        
        #add model to tree
        self.tree.setModel(self.model)

        self.tree.selectionModel().selectionChanged.connect(lambda: self.set_preview_image())
        for c in range(10):
            self.tree.resizeColumnToContents(c)
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               #Assemble Widgets
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        #Settings Widgets

        #Timings Pane
        self.TimingGroup = QtGui.QGroupBox('Timing')
        self.TimingGroup.setLayout(QtGui.QGridLayout())
        self.TimingGroup.layout().addWidget(self.TimingLabel1,       0,0)
        self.TimingGroup.layout().addWidget(self.TimingLoops,        0,1)
        self.TimingGroup.layout().addWidget(self.TimingLabel2,       1,0)
        self.TimingGroup.layout().addWidget(self.TimingInterval,     1,1)
        self.TimingGroup.layout().addWidget(self.TimingLabel3,       2,0)
        self.TimingGroup.layout().addWidget(self.TimingDuration,     2,1)

        #Fileing Pane
        self.FileGroup = QtGui.QGroupBox('File Storage')
        self.FileGroup.setLayout(QtGui.QGridLayout())
        self.FileGroup.layout().addWidget(self.FileUserLabel,        0,0)
        self.FileGroup.layout().addWidget(self.FileUserList,         0,1)
        self.FileGroup.layout().addWidget(self.FileRestore,          1,1,1,2)
        self.FileGroup.layout().addWidget(self.FileExptNameLabel,    2,0)
        self.FileGroup.layout().addWidget(self.FileExptName,         2,1)
        self.FileGroup.layout().addWidget(self.FileAddress,          3,0,1,2)

        #Tracking Pane
        
        self.TrackingGroup = QtGui.QGroupBox('Chromosome Tracking')
        self.TrackingGroup.setLayout(QtGui.QGridLayout())
        self.TrackingGroup.layout().addWidget(self.TrackingLabel1,      0,0)
        self.TrackingGroup.layout().addWidget(self.TrackingLaserOff,    0,1)
        self.TrackingGroup.layout().addWidget(self.TrackingLaser1,      0,2)
        self.TrackingGroup.layout().addWidget(self.TrackingLaser2,      0,3)
        self.TrackingGroup.layout().addWidget(self.TrackingLaser3,      0,4)
        self.TrackingGroup.layout().addWidget(self.TrackingLabel2,      1,0,1,2)
        self.TrackingGroup.layout().addWidget(self.TrackingChannel,     1,2,1,1)
        self.TrackingGroup.layout().addWidget(self.TrackingAdjustOnOff, 2,0,1,4)
        self.TrackingGroup.layout().addWidget(self.TrackingOV,          3,0,1,4)
 
        #Overall Settings pane
        self.SettingGroup = QtGui.QGroupBox('Settings')
        self.SettingGroup.setLayout(QtGui.QGridLayout())
        self.SettingGroup.layout().addWidget(self.startpause,       0,0)
        self.SettingGroup.layout().addWidget(self.stopbutton,       0,1)
        self.SettingGroup.layout().addWidget(self.TimingGroup,      1,0)
        self.SettingGroup.layout().addWidget(self.FileGroup,        1,1)
        self.SettingGroup.layout().addWidget(self.TrackingGroup,    1,2)
        
        #Information/instruction Pane
        InfoGroup = QtGui.QGroupBox('Information')
        InfoGroup.setFixedHeight(200)
        InfoGroup.setLayout(QtGui.QGridLayout())
        InfoGroup.layout().addWidget(self.InfoTree,                 0,0)
        
        #Preview Pane
        PreviewGroup = QtGui.QGroupBox('Preview')
        PreviewGroup.setLayout(QtGui.QGridLayout())
        PreviewGroup.layout().addWidget(self.PrevOVRed,             0,0)
        PreviewGroup.layout().addWidget(self.PrevOVGreen,           0,1)
        PreviewGroup.layout().addWidget(self.PrevOVBlue,            0,2)
        PreviewGroup.layout().addWidget(self.PrevCurrRed,           0,6)
        PreviewGroup.layout().addWidget(self.PrevCurrGreen,         0,7)
        PreviewGroup.layout().addWidget(self.PrevCurrBlue,          0,8)
        PreviewGroup.layout().addWidget(self.PrevOVInfoLabel,       1,0,1,3)
        PreviewGroup.layout().addWidget(self.PrevCurrInfoLabel,     1,6,1,3)
        PreviewGroup.layout().addWidget(self.PrevOVlabel,           2,0,2,6)
        PreviewGroup.layout().addWidget(self.PrevOverlaylabel,      2,0,2,6) #layered!
        PreviewGroup.layout().addWidget(self.PrevCurrlabel,         2,6,2,6)
        PreviewGroup.layout().addWidget(self.Prevsetupscan,         4,0,1,2)
        PreviewGroup.layout().addWidget(self.Prevfinishbutton,      4,2,1,2)
##        PreviewGroup.layout().addWidget(self.PrevShowLive,          4,6,1,1)
##        PreviewGroup.layout().addWidget(self.PrevUserSelect,        4,7,1,2)
        
        #Tree Pane
        self.DataGroup = QtGui.QGroupBox('Position/scan Data')
        self.DataGroup.setLayout(QtGui.QGridLayout())
        self.DataGroup.layout().addWidget(self.DataGoTo,            0,4,1,1)
        self.DataGroup.layout().addWidget(self.clearSelection,      0,5,1,1)
        self.DataGroup.layout().addWidget(self.tree,                1,0,1,6)

        #Overall assembly
        OverallLayout = QtGui.QGridLayout()
        OverallLayout.addWidget(self.SettingGroup,                  0,0,1,1)
        OverallLayout.addWidget(InfoGroup,                          1,0,1,1)
        OverallLayout.addWidget(PreviewGroup,                       2,0,1,1)
        OverallLayout.addWidget(self.DataGroup,                     3,0,1,1)
        
        self.MainArea = QtGui.QFrame()
        self.MainArea.setLineWidth(0)
        self.MainArea.setLayout(OverallLayout)
        self.setCentralWidget(self.MainArea)

        #lock for use in threads and GUI
        self.lock   = threading.Lock()
        self.lock2  = threading.Lock()
        
        self.show()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                      Imaging Loop Control                     #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# 
    def control_main_loop(self, action):     
        if action == 'Stop' and self.experimentSTOP == False:
            # -TO DO- check if user really wants to stop experiment
            print 'Stopping experiment'
            self.clear_info()
            self.update_info(4,1,'Experiment Stopped')
            self.startpause.setText('Start')
            self.startpause.setCheckable(False)
            self.startpause.setCheckable(True)
            self.startpause.state = 0
            self.DataGoTo.setEnabled(True)
            self.block_settings_edit(False)
            #stop main loop
            with self.lock2:
                self.experimentSTOP = True
                self.experimentPAUSE = False
            #reset loop count to zero
            self.reset_all_loop_counts()
            self.ImagingLoopThread.join()
            
        elif action == 'Start' and self.startpause.text() == 'Pause':
            print 'Pausing experiment'
            self.update_info(4,1,'Experiment Paused')
            self.startpause.setText('Resume')
            self.DataGoTo.setEnabled(True)
            self.startpause.state = 1
            #resume main loop
            with self.lock2:
                self.experimentPAUSE = True
            #Allow access to some widgets:
            
            
        elif action == 'Start' and self.startpause.text() == 'Resume':
            print 'Resuming experiment'
            self.update_info(4,1,'Resuming Experiment')
            self.sender().setText('Pause')
            self.DataGoTo.setEnabled(False)
            self.startpause.state = 0
            #resume experiment
            with self.lock2:
                self.experimentPAUSE = False

        elif action == 'Start' and self.startpause.text() ==  'Start':
            #_____Checklist
            Ready = True
            #_____Have scans been added?
            if self.model.rowCount()==0:
                self.update_info(3,1,"No scans have been added!\nClick 'Setup Scan' to begin")
                Ready = False
            #_____Tracking channel correct?
            if not self.TrackingLaserOff.isChecked() and not self.isInt(self.TrackingChannel.text()):
                self.update_info(3,1,'Chromosome tracking requires tracking channel to be entered!')
                Ready = False
            if self.TrackingAdjustOnOff.checkState()==2 and not self.isInt(self.TrackingChannel.text()):
                self.update_info(3,1,'Laser Adjustment requires tracking channel to be entered.')
                Ready = False
            #_____Lasers wavelengths actually exist
            if self.Laser_assignment_error == True:
                Ready = False
            #_____jobs to be used actually available as records in Matrix Screener?
            socket = open_socket()
            joblist =  getjoblist(socket)
            socket = close_socket(socket)
            if joblist.find(self.Overview_job)==-1:
                print "Job not found: ", self.Overview_job
                self.update_info(3,1,"The job '%s' was not found in the matrix screener list of jobs. \n Check the spelling in the config file. \n Check the job is loaded as a record in matrix screener." %(self.Overview_job))
                Ready = False
            if joblist.find(self.Zoom_job)==-1:
                print "Job not found: ", self.Zoom_job
                self.update_info(3,1,"The job '%s' was not found in the matrix screener list of jobs. \n Check the spelling in the config file. \n Check the job is loaded as a record in matrix screener." %(self.Zoom_job))
                Ready = False
                
            if Ready==True: 
                print 'Starting new experiment'
                self.update_info(4,1,'Starting Experiment')
                self.clear_preview_images()
                self.sender().setText('Pause')
                self.DataGoTo.setEnabled(False)
                self.startpause.state = 0
                self.block_settings_edit(True)
                #start experiment
                with self.lock2:
                    self.experimentSTOP     = False
                    self.experimentPAUSE    = False
                #create new folder and log files for experiment
                self.update_expt_name()
                self.update_info(4,1,'saving experiment too: %s' %self.FileAddress.text())
                os.mkdir(self.FileAddress.text())
                
                self.ImagingLoopThread   = threading.Thread(target=self.start_imaging, args=('Start',))
                self.ImagingLoopThread.start()
                
                    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                      Main Imaging Loop                        #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def start_imaging(self, arg):
        
        if self.experiment_reloaded == True:
            # completed loops and tracking channel will be taken from pickle file
            self.experiment_reloaded = False
        else:
            self.completed_loops         = 0
            self.tracking_channel        = self.TrackingChannel.text()
           
        ready_for_loop          = False
        target_loops            = int(self.TimingLoops.text())
        loop_interval           = int(self.TimingInterval.text())
        experiment_start_time   = time.time()
        number_of_scans = self.model.rowCount()
        #backup data in case of reload
        self.pickle_model()
        self.clear_info()

        #___________________LOOPS
        while self.completed_loops <target_loops:
            #Clear alerts
            self.update_info(3,1,'')
            self.InfoModel.item(3,1).setBackground(QtGui.QColor(255,255,255))
            #Timing loop, including pause and stop responce
            ready_for_loop = False
            while ready_for_loop == False:
                self.update_info(4,1,'Waiting for next loop...')
                pause_time = 0
                while True:
                    with self.lock2:
                        if self.experimentPAUSE == False:
                            break
                    time.sleep(0.1)
                    pause_time = pause_time+0.1
                    self.update_info(4,1,'Experiment Paused...%s s' %pause_time)

                with self.lock2:        
                    if self.experimentSTOP == True:
                        break
                next_loop_start_time = experiment_start_time + (self.completed_loops*loop_interval)
                wait_time = str(round((next_loop_start_time - time.time())*10)/10)
                self.update_info(2,1,'%s' %wait_time)
                if time.time() > next_loop_start_time + 1:
                    #Time issues! Either pause was used or imaging does not fit into interval
                    self.update_info(3,1,'Running %s seconds behind schedule' %(round(time.time() - next_loop_start_time)))
                    #adjust experiment_start_time to accommodate change
                    if time.time() > next_loop_start_time + 20:
                        experiment_start_time = experiment_start_time+(time.time()-next_loop_start_time)
                        self.update_info(3,1,'Running %s seconds behind schedule\nLoop timer re-calibrated!' %(round(time.time() - next_loop_start_time)))
                if time.time() > next_loop_start_time:
                    #Time to start next scan
                    ready_for_loop = True
                time.sleep(0.1)   
            self.update_info(0,1,'%s of %s' %(self.completed_loops+1,target_loops))  
            if self.experimentSTOP == True:
                break
            self.update_info(2,1,'')
            socket = open_socket()

            
            # Loop through checked scans
            #___________________SCANS
            for i in range(number_of_scans):

                #Pause and Stop~~~~~~~~~~~~~~
                pause_time = 0
                while True:
                    with self.lock2:
                        if self.experimentPAUSE == False:
                            break
                    time.sleep(0.1)
                    pause_time = pause_time+0.1
                    self.update_info(4,1,'Experiment Paused...%s s' %pause_time)

                with self.lock2:        
                    if self.experimentSTOP == True:
                        break
                    
                #Pause and Stop~~~~~~~~~~~~~~

                with self.lock:
                    self.pickle_model()
                    do_this_scan = self.model.item(i,0).checkState()
                    if do_this_scan==2:
                        self.update_info(4,1,'Scan setup...')
                        #colour current imaging row
                        for r in range(self.model.rowCount()):
                            self.model.item(r,1).setBackground(QtGui.QColor(255,255,255))
                        self.model.item(i,1).setBackground(QtGui.QColor(200,200,255))
                        #Setup Scan~~~~~~~~~~~~~~~~~~
                        #grab current xyz values                    
                        x   = self.model.item(i,2).text()
                        y   = self.model.item(i,3).text()
                        z   = self.model.item(i,4).text()
                        job = self.model.item(i,1).text()
                        if(job=="OV"):
                            assign_job(self.Overview_job,socket)
                            self.apply_settings(self.Overview_job,socket,i) #model access
                        if(job=="zoom"):
                            assign_job(self.Zoom_job,socket)
                            self.apply_settings(self.Zoom_job,socket,i) #model access
                    
                if do_this_scan==2:        
                    set_XYZ(x,y,z,socket)
                    self.update_info(1,1,'%s of %s (%s)' %(i+1,number_of_scans,job))
                    
                    #Start Scan~~~~~~~~~~~~~~~~~~
                    start_scan(socket)
                    self.update_info(4,1,'Scanning...')
                    # -TO DO- append scan information to log file
                    time.sleep(smallDelay)
                    folderLocation = get_scan_finish(self,socket)
                    self.update_info(4,1,'Scan Complete')
                    check_confocal_ready(socket) #causes suffient delay to stop confocal skipping commands
                    
                    #Add job to processing queue ~~~~~~~~~~~~~~~~~~
                    self.update_info(4,1,'Processing image files...')
                    self.AnalysisThread      = threading.Thread(target=self.image_processing, args=(folderLocation,i,self.completed_loops, job))
                    self.AnalysisThread.start()
                    
                    time.sleep(smallDelay)
                    
            close_socket(socket)
            #loop count
            self.completed_loops = self.completed_loops + 1
            #update GUI
#            self.tree.repaint()

        # experiment ended, call stop function to reset GUI
        self.update_info(4,1,'Experiment Complete')
        print 'Experiment Complete'
        self.startpause.setText('Start')
        self.startpause.setCheckable(False)
        self.startpause.setCheckable(True)
        self.startpause.state = 0
        self.block_settings_edit(False)
        self.experimentSTOP = True
        self.experimentPAUSE = False
        

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                       IMAGE PROCESSING                        #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    def image_processing(self, folderLocation, scan_number, loop_number, job):
        # !! This function operates in a separate thread !!

            #get vital information about job
            voxelx, voxelz, zoom, L1, L2, L3, pinhole     = get_info_from_metadata(self,folderLocation)
            print "From metadata: \t\t",voxelx, voxelz, zoom, L1, L2, L3, pinhole
            Cs, Zs, sizex, sizey                                = incoming_image_format(folderLocation)

            time.sleep(2) #IMPORTANT
                          #Allows processing to occur during 'scan time' and not 'setup time'

            #lock
            with self.lock:
                #process job
                if job == 'zoom':
                    if not self.TrackingLaserOff.isChecked():
                        tracking_channel_name                       = 'C0%s' %str(int(self.tracking_channel)-1)
                        COMx,COMy,COMz                              = find_COM(folderLocation, tracking_channel_name)
                        
                        dY = (COMx-(sizex/2))*voxelx        #   Deliberate swap of X and Y to counter
                        dX = (COMy-(sizey/2))*voxelx        #   Leica's reversed stage control
                        dZ = (COMz-(Zs/2))*voxelz
                        distance_score = math.sqrt(math.pow(dX,2)+math.pow(dY,2)+math.pow(dZ,2))
                        if distance_score>15:
                            bg_col = QtGui.QColor(255,0,0)
                        if distance_score<15:
                            bg_col = QtGui.QColor(255,126,0)
                        if distance_score<10:
                            bg_col = QtGui.QColor(255,205,0)
                        if distance_score<5:
                            bg_col = QtGui.QColor(166,255,0)
                        if distance_score<2:
                            bg_col = QtGui.QColor(0,255,0)
                        
                        self.model.item(scan_number,0).setBackground(bg_col)
                        X = float(self.model.item(scan_number,2).text()) - dX
                        Y = float(self.model.item(scan_number,3).text()) + dY
                        Z = float(self.model.item(scan_number,4).text()) + dZ
                        self.model.item(scan_number,2).setText("%.2f"%X)
                        self.model.item(scan_number,3).setText("%.2f"%Y)
                        self.model.item(scan_number,4).setText("%.2f"%Z)
                        
                    #Make adjustment if too many pixels are saturated, or image is too dark
                    if self.TrackingAdjustOnOff.isChecked():
                        if self.TrackingLaser1.isChecked():
                            L1 = self.laserAdjust(folderLocation, tracking_channel_name, L1)
                        if self.TrackingLaser2.isChecked():    
                            L2 = self.laserAdjust(folderLocation, tracking_channel_name, L2)
                        if self.TrackingLaser3.isChecked():    
                            L3 = self.laserAdjust(folderLocation, tracking_channel_name, L3)
                        
                if job == 'OV':
                    if self.TrackingOV.checkState()==2:
                        row     = scan_number+1
                        _sum    = 0
                        count   = 0
                        
                        Z = float(self.model.item(scan_number,4).text())
                        
                        while True:
                            if row>self.model.rowCount()-1:
                                if count >0:
                                    Z = _sum/count
                                break
                            if self.model.item(row,1).text()=='OV':
                                if count >0:
                                    Z = _sum/count
                                break
                            else:
                                if self.model.item(row,0).checkState()==2:
                                    _sum  = _sum + float(self.model.item(row,4).text())
                                    count = count + 1
                                row = row+1
                        self.model.item(scan_number,4).setText("%.2f"%Z)
                        
                #set data back to model
                self.model.item(scan_number,6).setText("%.1f"%L1)
                self.model.item(scan_number,7).setText("%.1f"%L2)
                self.model.item(scan_number,8).setText("%.1f"%L3)
                self.model.item(scan_number,9).setText("%.1f"%float(pinhole))
                self.model.item(scan_number,5).setText("%s"%(int(loop_number)+1))
            #unlock

            #Build preview
            try:
                preview_location = build_preview(folderLocation, Cs, scan_number+1)
            except:
                print 'error in build preview function'
            
            #transfer files
            dest_folder = ('%s\\%02d-%s\\t%03d') %(self.FileAddress.text(),scan_number,job,loop_number)
            shutil.move(folderLocation,dest_folder)
            
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                      Lesser Functions                         #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#Go to location
    def go_to(self):
        selection   = self.tree.selectionModel().selectedRows()
        i = self.model.itemFromIndex(selection[0]).row()
        x   = self.model.item(i,2).text()
        y   = self.model.item(i,3).text()
        z   = self.model.item(i,4).text()
        job = self.model.item(i,1).text()
        socket = open_socket()
        if(job=="OV"): job_name = self.Overview_job
        if(job=="zoom"): job_name = self.Zoom_job
        assign_job(job_name,socket)
        if self.model.item(i,6).text() != 'default':
            self.apply_settings(job_name,socket,i)
        set_XYZ(x,y,z,socket)
        close_socket(socket)
#TO DO - implement function to allow replacement of oil without having to disturb imaging dish. Move  
#        objective to a lower position, then to the side so it is accessable to the oil dropper.
##    def oil_escape():
##        if self.oilEscape == True:
##            #return to position
##            pass
##        else:
##            socket = open_socket()
##            #store return position
##            self.return_position = []
##            #move to escape position
##            
##            set_XYZ(20000,40000,2000,socket)
##            close_socket(socket)
        
#info functions
    def clear_info(self):
        for r in range(5):
            for c in range(2):
                item      = QtGui.QStandardItem('')
                self.InfoModel.setItem(r,c,item)
        self.update_info(0,0,'       Loops :')
        self.update_info(1,0,'        Scans :')
        self.update_info(2,0,'Wait Time :')
        self.update_info(3,0,'        Alerts :')
        self.update_info(4,0,'           Info :')
        self.InfoModel.item(3,1).setBackground(QtGui.QColor(255,255,255))

    def update_info(self,r,c,text):
        self.InfoModel.item(r,c).setText("%s"%text)
        if r==3:
            self.InfoModel.item(3,1).setBackground(QtGui.QColor(255,0,0))

    def report_error(self, error_msg):
        self.InfoModel.item(3,1).setText("%s"%error_msg)
        self.InfoModel.item(3,1).setBackground(QtGui.QColor(255,0,0))
            
#Automatic laser power adjustment
    def laserAdjust(self, folderLocation, tracking_channel_name, laser_power):
        laser_limit = 2                                                                                     #To add to Config file
        tifList =  glob.glob(folderLocation + '/*.tif')
        high_pixels = 0
        low_pixels = 0
        total_pixels = 0
        for tif in tifList:
            if tif.find(tracking_channel_name)>0:
                image_array     = numpy.asarray(Image.open(tif))
                high_pixels     = high_pixels   + numpy.histogram(image_array, bins=1, range=(250,256))[0][0]
                low_pixels      = low_pixels    + numpy.histogram(image_array, bins=1, range=(0,50))[0][0]
                total_pixels    = total_pixels  + image_array.shape[0]*image_array.shape[1]

        good_pixels     = total_pixels - high_pixels - low_pixels
        high_pixels     = float(high_pixels)/total_pixels*100
        low_pixels      = float(low_pixels)/total_pixels*100
        good_pixels     = float(good_pixels)/total_pixels*100
        new_laser_power = laser_power
        if (high_pixels/(good_pixels+0.0000001))<0.01 and laser_power<self.Laser_limit:
            new_laser_power = laser_power + 0.1
        else:
            new_laser_power = round((1-(high_pixels/(good_pixels+0.0000001)))*laser_power*10)/10
            if new_laser_power<0.2: pass
        return new_laser_power
        
#Preview Image functions
    def clear_preview_images(self):
        junkList =  glob.glob('Scans\\Scan*.tif')       #RELPATH!!!
        for image in junkList:
            os.remove(image)

    def change_image_state(self,image,colour):
        if image == 'Curr':
            if colour == 'Red':
                self.CurrRed = not self.CurrRed
            if colour == 'Green':
                self.CurrGreen = not self.CurrGreen
            if colour == 'Blue':
                self.CurrBlue = not self.CurrBlue
            self.update_preview_image('Curr')
        if image == 'OV':
            if colour == 'Red':
                self.OVRed = not self.OVRed
            if colour == 'Green':
                self.OVGreen = not self.OVGreen
            if colour == 'Blue':
                self.OVBlue = not self.OVBlue
            self.update_preview_image('OV')

    def update_preview_image(self,destination):
        #opens image from file
        try:
            if destination == 'OV':
                im = Image.open(self.PrevOVFileName)
                im = self.do_colours(im, self.OVRed, self.OVGreen, self.OVBlue)
                im.save('Scans\\tempOV.tif',"TIFF")                                              #RELPATH!!!
                self.PrevOVImage = QtGui.QImage('Scans\\tempOV.tif')                             #RELPATH!!!
                self.PrevOVpixmap = QtGui.QPixmap(self.PrevOVImage)
                self.PrevOVlabel.setPixmap(self.PrevOVpixmap)

            if destination == 'Curr':
                im = Image.open(self.PrevCurrFileName)
                im = self.do_colours(im, self.CurrRed, self.CurrGreen, self.CurrBlue)
                im.save('Scans\\tempCurr.tif',"TIFF")                                             #RELPATH!!!
                self.PrevCurrImage = QtGui.QImage('Scans\\tempCurr.tif')                         #RELPATH!!!
                self.PrevCurrpixmap = QtGui.QPixmap(self.PrevCurrImage)
                self.PrevCurrlabel.setPixmap(self.PrevCurrpixmap)

            if destination == 'Overlay':
                self.PrevOverlayImage = QtGui.QImage('overlay.png')                         #RELPATH!!!
                self.PrevOverlaypixmap = QtGui.QPixmap(self.PrevOverlayImage)
                self.PrevOverlaylabel.setPixmap(self.PrevOverlaypixmap)
        except:
            print 'image not available'
            
    def set_preview_image(self):
        with self.lock:
            selection = self.tree.selectionModel().selectedRows()
            scan = (self.model.itemFromIndex(selection[0]).row())+1
            timepoint = self.model.item(scan-1,5).text()
            scan_x = float(self.model.item(scan-1,2).text())
            scan_y = float(self.model.item(scan-1,3).text())

        if self.model.item(scan-1,5).text()=='0':
            print 'Image not available'
        else:
            self.PrevCurrFileName = 'Scans\\Scan%s.tif' %scan                                    #RELPATH!!!
            #get corresponding overview
            OV_scan_number, OV_loop_number = self.find_overview(scan)
            #get voxel size
            if OV_scan_number !=-1:
                dest_folder = ('%s\\%02d-%s\\t%03d') %(self.FileAddress.text(),int(OV_scan_number)-1,'OV',int(OV_loop_number)-1)
                voxelx, voxelz, zoom, L1, L2, L3, pinhole = get_info_from_metadata(self,dest_folder)
                with self.lock:
                    OV_x = float(self.model.item(OV_scan_number-1,2).text())
                    OV_y = float(self.model.item(OV_scan_number-1,3).text())

            #build overlay
            if OV_scan_number == scan:
                self.clear_overlay()
            else:
                if OV_scan_number !=-1:
                    self.build_overlay(scan_x, scan_y, OV_x, OV_y, voxelx, 512) #TO DO!! get OV image size, don't assume 512
            
            if OV_scan_number != -1:
                self.PrevOVFileName = 'Scans\\Scan%s.tif' %OV_scan_number                             #RELPATH!!!
                self.update_preview_image('OV')
                self.PrevOVInfoLabel.setText('Scan: %s, Loop: %s' %(OV_scan_number,timepoint))
                self.update_preview_image('Overlay')
            self.update_preview_image('Curr')
            self.PrevCurrInfoLabel.setText('Scan: %s, Loop: %s' %(scan,timepoint))
            
    def clear_overlay(self):
        mask = Image.new("L", (256,256), (0))
        overlay = Image.new("L", (256,256), (256))
        overlay.putalpha(mask)
        overlay.save('overlay.png',"PNG")

    def build_overlay(self, scan_x, scan_y, OV_x, OV_y, voxelx, OV_width):
        box_y = ((OV_x - scan_x)/voxelx) + (OV_width/2)
        box_x = ((scan_y - OV_y)/voxelx) + (OV_width/2)

        mask = Image.new("L", (OV_width,OV_width), (0))
        draw = ImageDraw.Draw(mask)
        draw.rectangle([(box_x-20,box_y-20),(box_x+20,box_y+20)], outline=256)
        draw.rectangle([(box_x-19,box_y-19),(box_x+19,box_y+19)], outline=256)

        draw.rectangle([(box_x-14,box_y-20),(box_x+14,box_y+20)], fill=0)
        draw.rectangle([(box_x-20,box_y-14),(box_x+20,box_y+14)], fill=0)
        mask = mask.resize((256,256))

        del draw
        overlay = Image.new("L", (256,256), (256))
        overlay.putalpha(mask)
        overlay.save('overlay.png',"PNG")                             #RELPATH!!!

    def find_overview(self, scan_number):
        scan_number = scan_number-1
        #if image is zoom
        with self.lock:
            if self.model.item(scan_number,1).text() != 'Overview':
                for i in range(scan_number,-1,-1):
                    if self.model.item(i,1).text() == 'OV':
                        return i+1, self.model.item(i,5).text()
                return -1, -1
        
    def do_colours(self, im, R, G, B):
        im = im.resize((256,256))
        r,g,b = im.split()
        e = Image.open('empty.tif')                             #RELPATH!!!
        if not R:
            r=e
        if not G:
            g=e
        if not B:
            b=e
        return Image.merge("RGB",(r,g,b))
        
#Leica control functions        
    def apply_settings(self, job, socket, scan_number):
        if self.model.item(scan_number,6).text() != 'default':
            columns         = [6,7,8,9]
            command = 'laser:%s:%s&laser:%s:%s&laser:%s:%s&pinhole:%s' %(self.Laser1,self.model.item(scan_number,6).text(),self.Laser2,self.model.item(scan_number,7).text(),self.Laser3,self.model.item(scan_number,8).text(),self.model.item(scan_number,9).text())
            adjust_job(job,command,socket)

    def do_setup_scan(self):
        socket = open_socket()
        joblist =  getjoblist(socket)
        close_socket(socket)
        if joblist.find(self.Setup_job)==-1:
            print "Job not found:", self.Setup_job
            self.update_info(3,1,"The job '%s' was not found in the matrix screener list of jobs. \n Check the spelling in the config file. \n Check the job is loaded as a record in matrix screener.\nRestart RTC." %(self.Setup_job))
            return    
                
        self.update_info(4,1,'Performing setup scan, please wait...')
        #inactivate rest of GUI
        self.SettingGroup.setEnabled(False)
        self.Prevsetupscan.setEnabled(False)
        self.SettingGroup.repaint()
        
        #Do the scan based on current position
        socket = open_socket()
        self.curr_stage_position =  get_XYZ(socket)                             # X, Y, Z
        assign_job(self.Setup_job,socket)
        set_XYZ(self.curr_stage_position[0],self.curr_stage_position[1],self.curr_stage_position[2],socket)
        start_scan(socket)
        self.curr_folderLocation = get_scan_finish(self, socket)
        self.curr_image_info = incoming_image_format(self.curr_folderLocation)  #Cs, Zs, sizex, sizey
        self.curr_scan_info = get_info_from_metadata(self,self.curr_folderLocation)  #voxelx, voxelz, zoom
        filename = self.model.rowCount()+1
        preview_location = build_preview(self.curr_folderLocation, self.curr_image_info[0], filename)
        print preview_location
        #Display the z-projection
        self.PrevOVFileName = preview_location
        self.update_preview_image('OV')
        
        #Prepare for CLICKING MODE
            #add overview to scan_list
        self.add_to_scan_list('OV',self.curr_stage_position[0],self.curr_stage_position[1],self.curr_stage_position[2])    
            #Label to say : 'Click points'
        self.update_info(4,1,"Click on image to register scan locations\nClick 'Finished' to end")
            #Finish Button to become active
        self.Prevfinishbutton.setEnabled(True)
            #Turn on clicking
        self.PrevOverlayimage_clickable = True
        close_socket(socket)
        
#Setup image functions        
    def finish_clicking(self):
        self.PrevOverlayimage_clickable = False
        self.Prevfinishbutton.setEnabled(False)
        self.SettingGroup.setEnabled(True)
        self.Prevsetupscan.setEnabled(True)
        self.SettingGroup.repaint()
        self.update_info(4,1,'')

    def get_click_position(self , event):
        if self.PrevOverlayimage_clickable == True:
            #get channel to analyze
            self.tracking_channel = 0
            _x = event.pos().x()
            _y = event.pos().y()
            x = self.curr_stage_position[0] + ((self.curr_image_info[2]/2) - _y) * self.curr_scan_info[0]
            y = self.curr_stage_position[1] - ((self.curr_image_info[3]/2) - _x) * self.curr_scan_info[0]

            #get z from image data!
            z = find_Z_from_click(self,_x,_y)

            #add to scan_list
            self.add_to_scan_list('zoom',x,y,z)
            
    def clear_selection(self):
        selection = self.tree.selectionModel().selectedRows()
        #remove row
        for item in selection:
            row = self.model.itemFromIndex(item).row()
            self.model.removeRows(row,1)
        #renumber scans
        scans = self.model.rowCount()
        for scan in range(scans):
            scanNum = scan + 1
            self.model.item(scan,0).setText('%s' %scanNum)
        
    def add_to_scan_list(self,job,_x,_y,_z):
        n           = self.model.rowCount()+1
        job         = QtGui.QStandardItem("%s" %job)
        x           = QtGui.QStandardItem("%s" %_x)
        y           = QtGui.QStandardItem("%s" %_y)
        z           = QtGui.QStandardItem("%s" %_z)
        enable      = QtGui.QStandardItem("%s" %n)
        enable.setCheckable(True)
        enable.setCheckState(QtCore.Qt.Checked)
        loops       = QtGui.QStandardItem('0')
        L1        = QtGui.QStandardItem("%s" %'default')
        L2        = QtGui.QStandardItem("%s" %'default')
        L3        = QtGui.QStandardItem("%s" %'default')
        pinhole     = QtGui.QStandardItem("%s" %'default')
        self.model.appendRow([enable,job,x,y,z,loops,L1,L2,L3,pinhole])
        for c in range(10):
            self.tree.resizeColumnToContents(c)
                
    def scan_options(self):
        pass
    
#gui maintenence functions
    def block_settings_edit(self,state):
        self.FileGroup.setEnabled(not state)
        self.TimingGroup.setEnabled(not state)
        self.TrackingGroup.setEnabled(not state)
        self.Prevsetupscan.setEnabled(not state)
        self.clearSelection.setEnabled(not state)

    def block_preview_edit(self,state):
        self.TimingLoops.setReadOnly(state)
        self.TimingInterval.setReadOnly(state)
        self.Prevsetupscan.setEnabled(not state)
        self.Prevfinishbutton.setEnabled(state)
        
    def update_expt_name(self):
        UserName    = self.FileUserList.currentText()
        ExptName    = self.FileExptName.text()
        startdate   = datetime.date.today()

        if len(ExptName)>0:
            ExptName = ' (%s)' %(ExptName)
        i=0
        while True:
            i=i+1
            if i==1:
                StoreLocation = '%s\\%s\\%s%s' %(self.User_root,UserName,startdate,ExptName)
            else:
                StoreLocation = '%s\\%s\\%s (%s)%s' %(self.User_root,UserName,startdate,i,ExptName)
            if not os.path.exists(StoreLocation):
                self.FileAddress.setText(StoreLocation)
                break

    def update_duration(self):
        #get interval (in seconds)
        try:
            interval    = int(self.TimingInterval.text())
            loops       = int(self.TimingLoops.text())

            DurationH   = int(math.floor(interval*loops/3600))
            DurationM   = int(math.floor((interval*loops-(DurationH*3600))/60))
            DurationS   = int(math.floor((interval*loops-(DurationH*3600)-(DurationM*60))))
            self.TimingDuration.setText('%02d : %02d : %02d' %(DurationH,DurationM,DurationS))
        except:
            print 'please enter an integer'
            
#reset loop count
    def reset_all_loop_counts(self):
        for i in range(self.model.rowCount()):
            self.model.item(i,5).setText('0')

    def pickle_model(self):
        to_store = []
        #save completed loops
        to_store.append(self.completed_loops)
        to_store.append(self.tracking_channel)
        #Save model dimensions
        rows = self.model.rowCount()
        cols = self.model.columnCount()
        to_store.append(rows)
        to_store.append(cols)
        #Save contents of model
        for r in range(rows):
            for c in range(cols):
                to_store.append(self.model.item(r,c).text())

        #pickle
        address = '%s\\expt_restore.p' %self.FileAddress.text()                             #RELPATH!!!
        pickle.dump(to_store, open(address, 'wb'))

    def restore_experiment(self):
        UserName    = self.FileUserList.currentText()
        basic_dir = '%s\\%s\\' %(self.User_root,UserName)                                         #RELPATH!!!
        address = QtGui.QFileDialog.getOpenFileName(self, 'Open File', basic_dir)
        print 'restoring experiment from: ',address
        to_restore = pickle.load(open(address, 'rb'))

        self.completed_loops = to_restore[0]
        self.tracking_channel = to_restore[1]
        self.TrackingChannel.setText(str(self.tracking_channel))
        self.experiment_reloaded = True
        rows = to_restore[2]
        cols = to_restore[3]
        self.model.clear()
        self.model.setRowCount(rows)
        self.model.setColumnCount(cols)
        self.model.setHorizontalHeaderLabels([self.tr("Scan"),self.tr("Job"),self.tr("X"),self.tr("Y"),self.tr("Z"),self.tr("Loops"),self.tr(self.Laser1),self.tr(self.Laser2),self.tr(self.Laser3),self.tr("Pinhole")])

        #insert data
        count = 4
        for r in range(rows):
            for c in range(cols):
                self.model.setItem(r,c,QtGui.QStandardItem(to_restore[count]))
                if c==0:
                    self.model.item(r,c).setCheckable(True)
                    self.model.item(r,c).setCheckState(QtCore.Qt.Checked)
                count = count +1
        for c in range(10):
            self.tree.resizeColumnToContents(c)
            
    def isInt(self,v):
        try:     i = int(v)
        except:  return False
        return True
    
def main():
    app = QtGui.QApplication(sys.argv)
    gui = ResponsiveTimelapseController()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
