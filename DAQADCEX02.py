#DAQADCEX02.CPP
#
# apply V0(t) to ACH8  ;channel 0 ; [signal range: -10 .. 10V]
#       V1(t) to ACH0  ;channel 1
#       V2(t) to ACH5  ;channel 2
#
# uses 32bit enh API  
#
# This example starts a multiple channel scan with a software trigger 
#	and a scan number stop event.  
#
# Note that the DaqBoard3K can only support one scan rate for pre 
#	and post trigger and that the buffer does not need to be rotated.  
# 
#
#  Functions used:
#	daqOpen(handle);	
#	daqAdcSetAcq(handle, mode, preTrigCount, postTrigCount);
#	daqAdcSetScan(handle, &channels, &gains, &flags, chanCount);
#	daqAdcSetFreq(handle, freq );
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
import daqx  as daq
import daqxh as daqh

#Scan will start immediatly and stop when the requested scans have been performed
STARTSOURCE =	daqh.DatsSoftware	
STOPSOURCE	 =  daqh.DatsScanCount
CHANCOUNT	 =  3
SCANS		 =  1000
RATE		 =  100	#Hz	

#used to configure scan
buffer   = np.zeros((SCANS*CHANCOUNT,), dtype=np.uint16)    #WORD        buffer[SCANS*CHANCOUNT];	
gains    = [daqh.DgainDbd3kX1]*CHANCOUNT                    #DaqAdcGain  gains[CHANCOUNT]     = {DgainDbd3kX1, DgainDbd3kX1, DgainDbd3kX1};	
channels = [8,0,5]                                         
flags    = [daqh.DafBipolar]*3                              

# This is the default name for a DaqBoard3000 when configured through the 
# Control Panel Applet. If you have named your device differently than the default,
# it must be changed here for this example to function.
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
#Set buffer location, size and flag settings
daq.AdcTransferSetBuffer(handle, buffer, SCANS, CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOff)

#Set to Trigger on software trigger
daq.SetTriggerEvent(handle, STARTSOURCE, daqh.DetsRisingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStartEvent)
#Set to stop when the requested number of scans is completed
daq.SetTriggerEvent(handle, STOPSOURCE,  daqh.DetsRisingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, 0, 0, daqh.DaqStopEvent)
#set scan rate
daq.AdcSetFreq(handle, RATE)
#begin data acquisition
print "Scanning...\n"
daq.AdcTransferStart(handle)
daq.AdcArm(handle)

#Note, kbhit() doesn't work in interpreter, only in console mode
#print "Hit any key to issue software trigger...\n"
#while not msvcrt.kbhit():
#    time.sleep(0.1)		

key = raw_input("Hit return to issue software trigger...\n")

daq.AdcSoftTrig(handle) #issue software trigger
print "--triggered--\n"

active = 1
while not msvcrt.kbhit() and (active & daqh.DaafAcqActive):
    time.sleep(0.1)
    #transfer data into computer memory and halt acquisition when done
    active, retCount = daq.AdcTransferGetStat(handle)
    print active, retCount

#Disarm when completed    
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
scale   = [maxVolt/(65535 - (flag & daqh.DafBipolar)*16384) for flag in flags]
offset  = [maxVolt*(flag & daqh.DafBipolar)/2 for flag in flags]

#buffer data format [ch0_scan0, ch1_scan0, ch2_scan0, ch0_scan1, ch1_scan1, ch2_scan1, ...]
bufch0 = buffer.reshape(-1,CHANCOUNT)[:,0]
bufch1 = buffer.reshape(-1,CHANCOUNT)[:,1]
bufch2 = buffer.reshape(-1,CHANCOUNT)[:,2]

#convert to volts
ch0V = bufch0*scale[0] - offset[0]
ch1V = bufch1*scale[1] - offset[1]
ch2V = bufch2*scale[2] - offset[2]

pylab.plot(ch0V, 'b', ch1V, 'r', ch2V, 'g')
pylab.show()