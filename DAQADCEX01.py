#DAQADCEX01.CPP
#
# apply V(t) to ACH0 [range" -10 .. 10V]
#
# uses 32bit enh API  
#
#	The purpose of this example is to show the user how to test for and
#	select the DaqBoard3000 and perform an immediate acquisition using the
#	new daqAdcSetTriggerEvent function
# 
#
# Functions used:
#	daqGetDeviceCount( &deviceCount);
#	daqGetDeviceList( DaqDeviceList );
#	daqGetDeviceProperties( daqName, &devProps);
#	daqOpen(handle);	
#	daqAdcSetAcq(handle, mode, preTrigCount, postTrigCount);
#	daqAdcSetScan(handle, &channels, &gains, &flags, chanCount);
#	daqAdcSetFreq(handle, freq );
#	daqSetTriggerEvent(handle, trigSource, trigSensitivity,
#						  channel, gainCode, flags, channelType,
#						  level, variance, trigevent);					
#	daqAdcTransferSetBuffer(handle, buf, scanCount,transferMask);
#	daqAdcTransferStart(DaqHandleT handle);
#	daqAdcTransferGetStat(DaqHandleT handle, active, retCount);
#	daqAdcArm(handle);
#	daqAdcDisarm(handle);
#	daqClose(handle);

import sys
import time
import msvcrt
import numpy as np
import pylab
import daqx as daq   #import IOtech library
from daqxh import *  #so that I can use constants DatsImmediate without the prefix daq (i.e daq.DatsImmediate)

#Scan will start immediatly and stop when the requested scans have been performed
STARTSOURCE =	DatsImmediate
STOPSOURCE	 =  DatsScanCount
CHANCOUNT	 =  1
SCANS		 =  1000
RATE		 =  100	#Hz	

#used to configure scan
buffer   = np.zeros((SCANS*CHANCOUNT,), dtype=np.uint16)    #WORD        buffer[SCANS*CHANCOUNT];	
gains    = [DgainDbd3kX1]                              #gains[0]    = DgainDbd3kX1;     #gain of X1
channels = [0]                                              #channels[0] = 0;           #select channel 0
flags    = [DafBipolar]                                #flags[0]    = DafBipolar;  #select Bipolar mode


# This is the default name for a DaqBoard3000 when configured through the 
# Control Panel Applet. If you have named your device differently than the default,
# it must be changed here for this example to function.
devName = daq.GetDeviceList()[0]  #find 1st IOtech device

print "Connected to %s\n\n" % devName  
handle = daq.Open(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

print "Setting up scan...\n"

daq.AdcSetAcq(handle, DaamNShot, 0, SCANS)
#Scan settings
daq.AdcSetScan(handle, channels, gains, flags)
#set scan rate
daq.AdcSetFreq(handle, RATE)
#Set buffer location, size and flag settings
daq.AdcTransferSetBuffer(handle, buffer, SCANS,CHANCOUNT, DatmUpdateSingle + DatmCycleOff)

#Set to trigger immediatly
daq.SetTriggerEvent(handle, STARTSOURCE, DetsRisingEdge, channels[0], gains[0], flags[0], DaqTypeAnalogLocal, 0, 0, DaqStartEvent)
#Set to stop when the requested number of scans is completed
daq.SetTriggerEvent(handle, STOPSOURCE,  DetsRisingEdge, channels[0], gains[0], flags[0], DaqTypeAnalogLocal, 0, 0, DaqStopEvent)
#begin data acquisition
print "Scanning...\n"
daq.AdcTransferStart(handle)
daq.AdcArm(handle)

active = 1
while not msvcrt.kbhit() and (active & DaafAcqActive):
    time.sleep(1)
    #transfer data into computer memory and halt acquisition when done
    active, retCount = daq.AdcTransferGetStat(handle)
    print active, retCount
    
daq.AdcDisarm(handle)
print "Scan Completed\n"

#close device connections
daq.Close(handle)

#convert the data to volts:
#DaqBoards convert all data to an unsigned, 16-bit number (range 0 to 65535).  Zero corresponds 
#to the minimum voltage, which is -maxVolt if in bipolar mode, or zero if unipolar.  
#65535 corresponds to maxVolt if bipolar, or 2 * maxVolt if unipolar.  Note that a voltage 
#higher than the device's absolute range (+/-10V for DaqBoard3000 , +/-5V for other Daq* devices)
#can damage the device.  Setting flags and gain settings which indicate a voltage higher than 
#the device's max, such as an unipolar, unscaled scan will result in an error before the scan 
#is performed.
#
#The following routine automatically determines the max voltage for the device used
#and the proper scaling and offset factors for the polarity flags selected.

maxVolt = 10.0		#Max voltage for Daq3K is +/-10V
scale   = [maxVolt/(65535 - (flag & DafBipolar)*16384) for flag in flags]
offset  = [maxVolt*(flag & DafBipolar)/2 for flag in flags]

#this only works for a single channel as is the case for this example
conv_buffer = buffer*scale[0] - offset[0]

#print scan data
print "Here is the Test Data: \n"
print "Analog ch %d\n" % channels[0]
for data in conv_buffer: print "%1.3f\t\t" % data

pylab.plot(conv_buffer)
pylab.show()

