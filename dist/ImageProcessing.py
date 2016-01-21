from PIL import Image, ImageFilter
from xml.etree import ElementTree

import time, os, glob, operator, numpy

def make_z_projection(folderLocation, channel):
    tifList =  glob.glob(folderLocation + '/*.tif')
    image = Image.open(tifList[0])
    width, height = image.size
    zpX=[0 for i in range(width*height)]
    zpY=[0 for i in range(width*height)]
    zpZ = []
    for tif in tifList:
        if tif.find(channel)>0:
            imageY = Image.open(tif).getdata()
            imageX = Image.open(tif).rotate(270).getdata()
            zpZ.append(sum(imageX))
            zpY = map(operator.add, zpY,imageY)
            zpX = map(operator.add, zpX,imageX)
    zpmax =  max(zpY)
    return height, width, zpmax, zpX, zpY, zpZ


def find_COM(folderLocation,channel):
    #prepare z-projections
    height, width, zpmax, zpX, zpY, zpZ = make_z_projection(folderLocation,channel)
    
    #do COM - y
    rowsum = float(0)
    weighted = float(0)
    for h in range(height):
        a = sum(zpY[h*width:(h*width)+width-1])
        b = a*h
        weighted = weighted + b
        rowsum = rowsum + a
    y = weighted/rowsum
    
    #do COM - x
    rowsum = float(0)
    weighted = float(0)
    for h in range(height):
        a = sum(zpX[h*width:(h*width)+width-1])
        b = a*h
        weighted = weighted + b
        rowsum = rowsum + a
    x = weighted/rowsum

    #do COM - z
    weighted = 0
    for z in range(len(zpZ)):
        b = zpZ[z]*z
        weighted = weighted + b
    weighted = float(weighted)
    z = weighted/sum(zpZ)
    return x+0.5,y+0.5,z+0.5

def find_Z_from_click(self,x,y):
    tifList     =  glob.glob(self.curr_folderLocation + '/*.tif')
    channel     = 'C0%s' %self.tracking_channel
    Zs          = self.curr_image_info[1]
    Zsep        = self.curr_scan_info[1]
    intensity   = []
    
    for tif in tifList:
        if tif.find(channel)>0:
            image = Image.open(tif).crop((x-10, y-10, x+10, y+10)).getdata()
#            temp = Image.open(tif).crop((x-10, y-10, x+10, y+10)).show()
            intensity.append(sum(image))
    _slice =  intensity.index(max(intensity))
    #calculate z position
    return self.curr_stage_position[2] + ((Zsep*_slice) - ((Zsep*(Zs-1))/2))

def build_preview(folderLocation,Cs, filename):
    tifList =  glob.glob(folderLocation + '/*.tif')
    image = Image.open(tifList[0])
    width, height = image.size

    zpc1 = Image.new('L', (width, height), (0))
    zpc2 = Image.new('L', (width, height), (0))
    zpc3 = Image.new('L', (width, height), (0))

    if int(Cs)==0:
        return 'error, no channels'
    if int(Cs)>0:
        zp1=[0 for i in range(width*height)]
        for tif in tifList:
            if tif.find('C00')>0:
                image = Image.open(tif).getdata()
                zp1 = map(operator.add, zp1,image)
        maxi = max(zp1)
        if maxi == 0:
            maxi = 1
            print "Warning, image channel 2 is empty"
        zp1 = map(lambda x: (x*255)/maxi, zp1)
        zpc1.putdata(zp1,1,0)

    if int(Cs)>1:
        zp2=[0 for i in range(width*height)]

        for tif in tifList:
            if tif.find('C01')>0:

                image = Image.open(tif).getdata()
                zp2 = map(operator.add, zp2,image)

        maxi = max(zp2)
        if maxi == 0:
            maxi = 1
            print "Warning, image channel 2 is empty"
        zp2 = map(lambda x: (x*255)/maxi, zp2)
        zpc2.putdata(zp2,1,0)

    if int(Cs)>2:
        zp3=[0 for i in range(width*height)]
        for tif in tifList:
            if tif.find('C02')>0:
                image = Image.open(tif).getdata()
                zp3 = map(operator.add, zp3,image)
        maxi = max(zp3)
        if maxi == 0:
            maxi = 1
            print "Warning, image channel 3 is empty"
        zp3 = map(lambda x: (x*255)/maxi, zp3)
        zpc3.putdata(zp3,1,0)

    zpmc = Image.merge('RGB',(zpc1,zpc2,zpc3)) 
    filename = 'Scans\Scan%s.tif' %filename
    zpmc.save(filename,'TIFF')
    return filename


def get_info_from_metadata(self,folderLocation):
    fileLocation =  glob.glob(folderLocation + '\metadata\*ome.xml')
    with open(fileLocation[0], 'rt') as f:
        metadata = f.read()

    a = metadata.find('" Zoom="')
    b = metadata.find('" Type="',a)
    zoom = float(metadata[a+8:b])
    
    a = metadata.find('" PhysicalSizeX="')
    b = metadata.find('" PhysicalSizeY="',a)
    voxelx = float(metadata[a+17:b])   

    a = metadata.find('" PhysicalSizeZ="')
    b = metadata.find('" TimeIncrement="',a)
    voxelz = float(metadata[a+17:b])
    
    a = metadata.find('LaserLine" Value="%s" />' %self.Laser1)
    if a==-1:
        self.report_error("Laser value %s is not a valid wavelength for this microscope. \nPlease adjust your config file and restart RTC" %self.Laser1)
        self.Laser_assignment_error = True
        return voxelx, voxelz, 1,1,1,1,1
    b = metadata.find('IntensityDev" Value="',a)
    c = metadata.find('" />',b)
    L1 = float(metadata[b+21:c])
    
    a = metadata.find('LaserLine" Value="%s" />' %self.Laser2)
    if a==-1:
        self.report_error("Laser value %s is not a valid wavelength for this microscope. \nPlease adjust your config file and restart RTC" %self.Laser2)
        self.Laser_assignment_error = True
        return voxelx, voxelz, 1,1,1,1,1
    b = metadata.find('IntensityDev" Value="',a)
    c = metadata.find('" />',b)
    L2 = float(metadata[b+21:c])

    a = metadata.find('LaserLine" Value="%s" />' %self.Laser3)
    if a==-1:
        self.report_error("Laser value %s is not a valid wavelength for this microscope. \nPlease adjust your config file and restart RTC" %self.Laser3)
        self.Laser_assignment_error = True
        return voxelx, voxelz, 1,1,1,1,1
    
    b = metadata.find('IntensityDev" Value="',a)
    c = metadata.find('" />',b)
    L3 = float(metadata[b+21:c])

    a = metadata.find('PinholeAiry" Value="')
    b = metadata.find('" />',a)
    pinhole = (metadata[a+20:b])
    
    return voxelx, voxelz, zoom, L1, L2, L3, pinhole

