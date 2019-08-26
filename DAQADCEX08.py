#DAQADCEX08.CPP
#
# 
#
# This example demonstrates the use of the driver buffer for collecting a circular scan (i.e. more 
# scans than the buffer can hold.  Data will be displayed as it is acquired from the driver buffer
#
# Functions used:
#	daqOpen(handle);	
#	daqAdcSetAcq(handle, mode, preTrigCount, postTrigCount);
#	daqAdcSetScan(handle, &channels, &gains, &flags, chanCount);
#  daqAdcSetFreq(handle, freq );
#	daqSetTriggerEvent(handle, trigSource, trigSensitivity,
#						  channel, gainCode, flags, channelType,
#						  level, variance, trigevent);	
#	daqAdcTransferSetBuffer(handle, buf, scanCount,transferMask);
#	daqAdcTransferStart(DaqHandleT handle);
#  daqAdcTransferBufData(DaqHandleT handle, PWORD buf, DWORD scanCount, DaqAdcBufferXferMask bufMask,
#                        PDWORD retCount);
#	daqAdcTransferGetStat(DaqHandleT handle, active, retCount);
#	daqAdcArm(handle);
#	daqAdcDisarm(handle);
#	daqClose(handle);

import sys
import time
import msvcrt
import numpy as np
import pylab
import daqx as daq
import daqxh as daqh

STARTSOURCE	= daqh.DatsSoftware
STOPSOURCE	= daqh.DatsScanCount
CHANCOUNT	 =  2
READSCANS	 =  10
RATE         =  100
TRIGSENSE	 =  daqh.DetsRisingEdge



#used to configure scan
buffer   = np.zeros((READSCANS*CHANCOUNT,), dtype=np.uint16)
channels = [0,2]
gains    = [daqh.DgainDbd3kX1, daqh.DgainDbd3kX1]
flags    = [daqh.DafBipolar, daqh.DafBipolar]
#used to monitor scan
scansCollected=0

devName = daq.GetDeviceList()[0]
print "Connecting to %s\n\n" % devName  
handle = daq.Open(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

print "Setting up scan...\n"

daq.AdcSetAcq(handle, daqh.DaamInfinitePost, 0, READSCANS)
#Scan settings
daq.AdcSetScan(handle, channels, gains, flags)
#set scan rate
daq.AdcSetFreq(handle, RATE)
#Set buffer size and flag settings
#for circular driver buffer, set location to NULL, and set a size larger than the number of scans per second
daq.AdcTransferSetBuffer(handle, None, READSCANS*RATE, CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOn + daqh.DatmDriverBuf)
#Set to Trigger Immediatly
daq.SetTriggerEvent(handle, STARTSOURCE, TRIGSENSE, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStartEvent)
#Set to Stop when scan is complete
daq.SetTriggerEvent(handle, STOPSOURCE,  TRIGSENSE, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStopEvent)

#begin data acquisition
daq.AdcTransferStart(handle)
daq.AdcArm(handle)
print "\nTrigger Armed..."
key = raw_input("Hit return to issue software trigger...\n")
daq.AdcSoftTrig(handle) #issue software trigger
print "--triggered--\n"

maxVolt = 10.0
scale   = [maxVolt/(65535 - (flag & daqh.DafBipolar)*16384) for flag in flags]
offset  = [maxVolt*(flag & daqh.DafBipolar)/2 for flag in flags]

scans = 0
while not msvcrt.kbhit() and scans < 1000:
    #Collect data from the driver's circular buffer as it becomes available 
    #Transfer data from driver buffer to ours, will wait until READSCANS scans are collected
    scansCollected = daq.AdcTransferBufData(handle, buffer, READSCANS, CHANCOUNT, daqh.DabtmWait)

    buffer0 = buffer.reshape(-1,CHANCOUNT)[:,0]
    buffer1 = buffer.reshape(-1,CHANCOUNT)[:,1]
    conv_buffer0 = buffer0*scale[0] - offset[0]
    conv_buffer1 = buffer0*scale[1] - offset[1]
    scans += scansCollected
    print "total number of scans collected: %5u: " % scans
    print "Channel 0:", conv_buffer0
    print "Channel 1:", conv_buffer1

#Disarm when completed
daq.AdcDisarm(handle)
print "Scan Completed\n"
daq.Close(handle)
