#DAQADCEX04.CPP
#
# requires TTL-trigger on TTL TRG line
# apply V0(t) to ACH0  ;channel 0 ; [signal range: -10 .. 10V]
#
# trigger by connecting TTLTRG to GND 

#  This program demonstrates an infinite TTL triggered scan, saved direct to disk.
#  Scaling should be performed on the data saved in the data file 
#
# Functions used:
#	daqOpen(handle);	
#	daqAdcSetAcq(handle, mode, preTrigCount, postTrigCount);
#	daqAdcSetScan(handle, &channels, &gains, &flags, chanCount);
#  daqAdcSetFreq(handle, freq);
#	daqAdcSetTriggerEvent(handle, trigSource, trigSensitivity,
#						  channel, gainCode, flags, channelType,
#						  level, variance, trigevent);					
#  daqAdcSetDiskFile(handle, filename, openMode, preWrite);
#  daqSetTimeout(handle, time);
#  daqWaitForEvent(handle, DteEvent);
#	daqAdcTransferStart(DaqHandleT handle);
#	daqAdcTransferGetStat(DaqHandleT handle, active, retCount);
#	daqAdcArm(handle);
#	daqAdcDisarm(handle);
#	daqClose(handle);

import time
import msvcrt
import numpy as np
import pylab
import daqx as daq
import daqxh as daqh

STARTSOURCE	= daqh.DatsExternalTTL	#Start on TTL trigger
STOPSOURCE	= daqh.DatsScanCount	
FILENAME	= "Daq3K.bin"		# name of file to save to
PREWRITE	= 0				 
CHANCOUNT	= 1
SCANS		= 10000
RATE		= 1000

buffer   = np.ones((SCANS*CHANCOUNT,), dtype=np.uint16)
gains    = [daqh.DgainDbd3kX1]
channels = [0]
flags    = [daqh.DafBipolar]

devName = daq.GetDeviceList()[0]
print "Connecting to %s\n\n" % devName 
handle = daq.Open(devName)
print "Setting up scan...\n"
daq.AdcSetAcq(handle, daqh.DaamInfinitePost, 0, SCANS)
daq.AdcSetScan(handle, channels, gains, flags)
daq.AdcSetFreq(handle, RATE)
daq.AdcTransferSetBuffer(handle, buffer, SCANS, CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOff)

#test if file exists to determine write mode
try:
    f = open(FILENAME)
    f.close()
    daq.AdcSetDiskFile(handle, FILENAME, daqh.DaomWriteFile, PREWRITE)
except IOError as e:
    daq.AdcSetDiskFile(handle, FILENAME, daqh.DaomCreateFile, PREWRITE)

daq.SetTriggerEvent(handle, STARTSOURCE, daqh.DetsRisingEdge,  channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStartEvent)
daq.SetTriggerEvent(handle, STOPSOURCE,  daqh.DetsFallingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStopEvent)
#set timeout to exit after 10 seconds if no TTL trigger occurs
daq.SetTimeout(handle, 10000)

print "Waiting for TTL trigger...\n\n"

daq.AdcTransferStart(handle)
daq.AdcArm(handle)
daq.WaitForEvent(handle, daqh.DteAdcData)

print "Scan triggered, Press <space> to halt scan\n\n"
active, retCount = daq.AdcTransferGetStat(handle)

while not msvcrt.kbhit() and (active & daqh.DaafAcqActive) and (retCount < SCANS):
    active, retCount = daq.AdcTransferGetStat(handle)
    print "Scans: ", retCount
    time.sleep(0.05)

daq.AdcDisarm(handle)
daq.Close(handle)
print "\nScan Halted, scans performed\n", retCount

pylab.plot(buffer)
pylab.show()
    