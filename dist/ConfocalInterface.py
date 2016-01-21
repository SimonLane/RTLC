#!/usr/bin/env python
import                      socket, time, datetime, os, glob, thread, pickle
from ImageProcessing        import find_COM, get_info_from_metadata, build_preview
from PIL                    import Image
from PyQt4                  import QtGui, QtCore

TrackingChannel = 0
smallDelay      = 0.1
bigDelay        = 0.5
standaloneMode  = False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   LEICA INTERFACE FUNCTIONS                   #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def clear_stream(s):
    while True:
        if standaloneMode:
            return
        time.sleep(smallDelay)
        try:
            data = s.recv(1024).strip()
            if data:
                #print data
                pass
        except:
            #print 'stream empty'
            return

def get_XYZ(s):
    if standaloneMode:
        return 11520.3457, 64210.7221, 1900.002
    time.sleep(smallDelay)
    clear_stream(s)
    s.settimeout(0.5)
    s.send("/cli: Simon /app:matrix /sys: 1 /cmd: get /scmd: position")
    try:
        while True:
            data = s.recv(1024)
            if data.find('zpos')!=-1:
                xposa   = data.find('xpos:')
                xposb   = data.find('/', xposa)
                xpos    = float(data[xposa+5:xposb].strip())*1000000
                yposa   = data.find('ypos:')
                yposb   = data.find('/', yposa)
                ypos    = float(data[yposa+5:yposb].strip())*1000000
                zposa   = data.find('zpos:')
                zposb   = data.find('/', zposa)
                zpos    = float(data[zposa+5:zposb].strip())*1000000
                return xpos, ypos, zpos
            time.sleep(0.02)
    except:
        return 'Error: incorrect responce from confocal','',''

def getjoblist(s):
    time.sleep(smallDelay)
    clear_stream(s)
    s.send("/cli: Simon /app:matrix /sys: 1 /cmd: getinfo /dev: joblist")
    try:
        while True:
            data = s.recv(1024)
            if data.find('jobname')!=-1:
                return data.strip()
    except:
        return 'Error: incorrect responce from confocal'

def adjust_laser(job, laser, power,s):
    if standaloneMode:
        return 
    time.sleep(smallDelay)
    command = '/cli:Simon /app:matrix /cmd:adjustls /exp:%s /seq:1 /lsq:vis /lid:%s /tar:laser /value:%s' %(job,laser,power)
    s.send(command)

def adjust_job(job, cmnd,s):
    if standaloneMode:
        return
    time.sleep(smallDelay)
#    print cmnd
    commands = cmnd.split('&')
    for command in commands:
        bits = command.split(':')
        if bits[0] =='gain':
            gain = str(int(round(float(bits[2])))) + ',01'
            command = '/cli:Simon /app:matrix /cmd:adjust /tar:pmt /num:%s /exp:%s /prop:gain /value:%s' %(bits[1],job,gain)
            s.send(command)
        if bits[0] =='offset':
            command = '/cli:Simon /app:matrix /cmd:adjust /tar:pmt /num:%s /exp:%s /prop:offset /value:%s' %(bits[1],job,bits[2])
            s.send(command)
        if bits[0] =='pinhole':
            command = '/cli:test /app:matrix /cmd:adjust /tar:pinhole /exp:%s /value:%s' %(job,bits[1])
            s.send(command)
        if bits[0] =='laser':
            command = '/cli:Simon /app:matrix /cmd:adjustls /exp:%s /seq:1 /lsq:vis /lid:%s /tar:laser /value:%s' %(job,bits[1],bits[2])
            s.send(command)
        time.sleep(smallDelay)

def get_scan_finish(self,s):
    clear_stream(s)
    time.sleep(bigDelay)
    while True:
        try:
            data = s.recv(1024)
            if data.find('relpath')>0:
                a=data.find('/relpath:')
                b=data.find('image--')
                return self.Confocal_out + '\\' + data[a+9:b-1].strip()
            if data.find('scanfinished')>0:
                return get_file_location(self)
        except:
            pass
        time.sleep(0.2)
            
def start_scan(s):
    time.sleep(bigDelay)
    s.send("/cli: Simon /app:matrix /sys: 1 /cmd: startscan")
    
def assign_job(jobname,s):
    time.sleep(smallDelay)
    s.send("/cli: Simon /app:matrix /sys: 1 /cmd: enableall /value:true")
    time.sleep(smallDelay)
    s.send("/cli: Simon /app:matrix /sys: 1 /cmd: selectallfields")
    time.sleep(smallDelay)
    s.send("/cli: Simon /app:matrix /sys: 1 /cmd: assignjob /job:%s" %jobname)
    
def set_XYZ(x,y,z,s):
    time.sleep(smallDelay)
    command = "/cli: Simon /app:matrix /sys: 1 /cmd: adjustmatrix /startx: %s /starty: %s /startz: %s" %(x,y,z)
    s.send(command)
    
def check_confocal_ready(s):
    command = "/cli: Simon /app:matrix /sys: 1 /cmd: getinfo /dev:scanstatus"
    s.send(command)
#    clear_stream(s)
    time.sleep(smallDelay)
    i=0
    while True:
        try:
            data = s.recv(1024)
#            print data.strip()
            if data.find('scanfinished')>0:
                return 'ready'
        except:
            pass
        time.sleep(0.2)
        i=i+1
        if i == 15:
            return 'ready'
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                   FILE HANDELING FUNCTIONS                    #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def current_datetime(self):
    return self.Confocal_out + datetime.datetime.now().strftime("\\Experiment--20%y_%m_%d_%H_%M_%S")

def get_file_location(self):
    #list all folders
    folderList = glob.glob(self.Confocal_out + '\\Experiment--*')
    #return most recent folder
    return folderList[len(folderList)-1]
     
def incoming_image_format(folderLocation):
##    print 'Directory correct?', os.path.exists(folderLocation)
    fileList = glob.glob(folderLocation + '\*.tif')
    Cs = 0
    Zs = 0
    for file in fileList:
        bits = file.replace('--','&').split('&')
        if int(bits[12][1:3]>Zs):
            Zs = int(bits[12][1:3])
        if int(bits[13][1:3]>Zs):
            Cs = int(bits[13][1:3])
    im = Image.open(fileList[0])
    sizex, sizey = im.size
    return Cs+1, Zs+1, sizex, sizey

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                       SOCKET CONNECTION                       #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def open_socket():
    if standaloneMode:
        print "Running in Standalone mode, no socket connection made."
        return 1
    TCP_IP = 'localhost'
    TCP_PORT = 8895
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.1)
    s.connect((TCP_IP, TCP_PORT))
    return s

def close_socket(s):
    if standaloneMode:
        return
    s.close()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#                       MAIN SCRIPT                             #
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

if __name__ == '__main__':
    pass

