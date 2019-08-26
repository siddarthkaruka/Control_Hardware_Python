#DAQADCEX05.CPP
#
# apply V0(t) to ACH0  ;channel 0 ; [signal range: -10 .. 10V]
#
# uses 32bit enh API  
#
#	This example demonstrates the use of an external clock source.  
#  A new error handler is written to bypass a Time Out error
# 
#
# Functions used:
#	daqOpen(handle);	
#	daqSetErrorHandler(handle, &ErrorHandler);
#  daqDefaultErrorHandler(handle, error_code);	
#	daqAdcSetAcq(handle, mode, preTrigCount, postTrigCount);
#	daqAdcSetScan(handle, &channels, &gains, &flags, chanCount);
#  daqAdcSetClockSource(handle, clockSource);
#  daqAdcSetFreq(handle, freq );
#	daqSetTriggerEvent(handle, trigSource, trigSensitivity,
#						  channel, gainCode, flags, channelType,
#						  level, variance, trigevent);
#  daqSetTimeout(handle, time);
#  daqWaitForEvent(handle, DteEvent);	
#	daqAdcTransferSetBuffer(handle, buf, scanCount,transferMask);
#	daqAdcTransferStart(DaqHandleT handle);
#	daqAdcTransferGetStat(DaqHandleT handle, active, retCount);
#	daqAdcArm(handle);
#	daqAdcDisarm(handle);
#	daqClose(handle);

#   How to run this script?
#   Start interpreter:  
#       from iotech import *
#       execfile('DAQADCEX05.py')

import sys
import time
import msvcrt
import numpy as np
import pylab

STARTSOURCE	= daqh.DatsImmediate
STOPSOURCE	= daqh.DatsScanCount

CHANCOUNT	 =  1
SCANS		 =  1000
BUFFSIZE     =  SCANS*CHANCOUNT

#used to configure scan
buffer   = np.zeros((BUFFSIZE,), dtype=np.uint16)    #WORD        buffer[SCANS*CHANCOUNT];	
gains    = [daqh.DgainDbd3kX1]*CHANCOUNT                    #DaqAdcGain  gains[CHANCOUNT]     = {DgainDbd3kX1, DgainDbd3kX1, DgainDbd3kX1};	
channels = [0]                                         
flags    = [daqh.DafBipolar]*CHANCOUNT                             

devName = daqGetDeviceList()[0]
print "Connecting to %s\n\n" % devName  
handle = daqOpen(devName)
if handle == -1:
    print "Cannot conncet to device\n"
    print "Exit"
    sys.exit(handle)

print "Setting up scan...\n"

daqAdcSetAcq(handle, daqh.DaamNShot, 0, SCANS)
#Scan settings
daqAdcSetScan(handle, channels, gains, flags)
#set clock source
daqAdcSetClockSource(handle, daqh.DacsExternalTTL)
#set scan rate even though it won't be used
daqAdcSetFreq(handle, 1)
#Set buffer location, size and flag settings
daqAdcTransferSetBuffer(handle, buffer, BUFFSIZE, daqh.DatmUpdateSingle + daqh.DatmCycleOff)

#Set to Trigger immediately
daqSetTriggerEvent(handle, STARTSOURCE, daqh.DetsRisingEdge,  channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStartEvent)
#Set to Stop on scan count
daqSetTriggerEvent(handle, STOPSOURCE,  daqh.DetsFallingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStopEvent)

#set timeout : 50 seconds
daqSetTimeout(handle, 50000)
#begin data acquisition
daqAdcTransferStart(handle)
daqAdcArm(handle)
print "Scanning...\n"
daqWaitForEvent(handle, daqh.DteAdcData)

active, retCount = daqAdcTransferGetStat(handle)

if active & daqh.DaafAcqTriggered:
    print "Triggered!\n"
    daqWaitForEvent(handle, daqh.DteAdcDone)

#Disarm when completed
daqAdcDisarm(handle)

#test if triggered or timed out
active, retCount = daqAdcTransferGetStat(handle)

daqClose(handle)

if retCount > 0 and retCount < SCANS:
    print "\nExternal Pacer Clock not fast enough?\n"
elif retCount == SCANS:
    print "\nExternal Pacer Clock Successful!\n"
else:
    print "\nExternal Pacer Clock Not Successful\n"


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
#(flag&DafBiplor) equals 2 if bipolar or 0 if unipolar
#scale should equal maxVolt/65335 for unipolar, maxVolt/32767 for bipolar
scale   = [maxVolt/(65535 - (flag & daqh.DafBipolar)*16384) for flag in flags]
offset  = [maxVolt*(flag & daqh.DafBipolar)/2 for flag in flags]

#this only works for a single channel as is the case for this example
conv_buffer = buffer*scale[0] - offset[0]

#print scan data
print "Here is the Test Data: \n"
print "Analog ch %d\n" % channels[0]
#for data in conv_buffer: print "%1.3f\t\t" % data

pylab.plot(conv_buffer[0:retCount])
pylab.show()