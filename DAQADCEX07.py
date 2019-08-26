#DAQADCEX07.CPP
#
# 
#
#	This example demonstrates synchronously scanning the frequency counters and High Speed
#  Digital I/O  on P2 
# 
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
#	daqAdcSoftTrig(handle);
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

STARTSOURCE	= daqh.DatsImmediate
STOPSOURCE	= daqh.DatsScanCount
CHANCOUNT	 =  6
SCANS		 =  10
RATE         =  10                  #you should use a low rate to allow for collection of pulses

#used to configure scan
buffer   = np.zeros((SCANS*CHANCOUNT,), dtype=np.uint16)    #WORD        buffer[SCANS*CHANCOUNT];	
channels = [0,1,2,1,0,2]                                    # P2 local digital, P3 16 bit counter, 32 bit counter (cascaded)
gains    = [daqh.DgainDbd3kX1, daqh.DgainDbd3kX1, daqh.DgainDbd3kX1, daqh.DgainDbd3kX1,daqh.DgainDbd3kX1,daqh.DgainDbd3kX1]  
flags    = [daqh.DafP2Local8, daqh.DafP2Local8, daqh.DafP2Local8,daqh.DafCtr16+daqh.DafCtrTotalize,daqh.DafCtr32Low+daqh.DafCtrPulse, daqh.DafCtr32High+daqh.DafCtrPulse]

devName = daq.GetDeviceList()[0]
print "Connecting to %s\n\n" % devName  
handle = daq.Open(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

print "Setting up scan...\n"

daq.AdcSetAcq(handle, daqh.DaamNShot, 0, SCANS)
#Scan settings
daq.AdcSetScan(handle, channels, gains, flags)
#set scan rate
daq.AdcSetFreq(handle, RATE)
#Set buffer location, size and flag settings
daq.AdcTransferSetBuffer(handle, buffer, SCANS, CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOff)
#Set to Trigger on software trigger
daq.SetTriggerEvent(handle, STARTSOURCE, daqh.DetsRisingEdge,  channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStartEvent)
#Set to Stop when the requested number of scans is completed
daq.SetTriggerEvent(handle, STOPSOURCE,  daqh.DetsFallingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStopEvent)

#begin data acquisition
daq.AdcTransferStart(handle)
daq.AdcArm(handle)

active, retCount = daq.AdcTransferGetStat(handle)
while active & daqh.DaafAcqActive:
    active, retCount = daq.AdcTransferGetStat(handle)

#Disarm when completed
daq.AdcDisarm(handle)
print "Scan Completed\n"
daq.Close(handle)

#No scaling is necessary for Digital ports or counters
#print scan data
print "Here is the Test Data: \n"
print "P2 ch0\tP2 ch1\tP2 ch2\tCounter 16Bit\tCounter 32Bit\n"

#buffer data format [ch0_scan0, ch1_scan0, ch2_scan0, ch0_scan1, ch1_scan1, ch2_scan1, ...]
bufP2ch0 = buffer.reshape(-1,CHANCOUNT)[:,0]
bufP2ch1 = buffer.reshape(-1,CHANCOUNT)[:,1]
bufP2ch2 = buffer.reshape(-1,CHANCOUNT)[:,2]
bufCnt16bit = buffer.reshape(-1,CHANCOUNT)[:,3]
bufCnt32bit_lower = buffer.reshape(-1,CHANCOUNT)[:,4]
bufCnt32bit_upper = buffer.reshape(-1,CHANCOUNT)[:,5]
bufCnt32bit = (bufCnt32bit_upper.astype('uint32')<<16) + bufCnt32bit_lower

print "P2ch0 ", bufP2ch0
print "P2ch1 ", bufP2ch1
print "P2ch2 ", bufP2ch2
print "Cnt16bit ", bufCnt16bit
print "Cnt32bit ", bufCnt32bit
#pylab.plot(buffer)
#pylab.show()