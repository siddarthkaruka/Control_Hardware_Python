#DAQADCEX03.CPP
#
# apply V0(t) to ACH0  ;channel 0 ; [signal range: -10 .. 10V]
#
#       use sinusoidal V0(t) with amplitude=3V and freq=2Hz
#
#  This program demonstrates the Analog Hardware and Analog Software Trigger for both 
#  the start and stop event.  It will start at an analog voltage and stop at the
#  negative of that voltage with opposite direction, capturing half of the signal.
#  Stop event can only accept Software Analog.
#

#
# Functions used:
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
import daqx as daq
import daqxh as daqh

#set to trigger if input rises above 2V and stop if it rises above -2V or 1000 scans 
#are performed, which ever comes first
STARTSOURCE	= daqh.DatsHardwareAnalog	#Hardware Analog is limited to Rising Edge, Falling Edge,
STOPSOURCE	= daqh.DatsSoftwareAnalog	#Above Level and Below Level and can only be a Start Event.
										#No limitations for Software Analog
VOLTAGESTART	= 2.0     #trigger voltage
VOLTAGEEND	    = -2.0
CHANCOUNT	 =  1
SCANS		 =  100     #this many scans will be completed before stop event is looked for
RATE		 =  100	#Hz	
BUFFSIZE     =  SCANS*100

#used to configure scan
buffer   = np.zeros((BUFFSIZE,), dtype=np.uint16)    #WORD        buffer[SCANS*CHANCOUNT];	
gains    = [daqh.DgainDbd3kX1]*CHANCOUNT                    #DaqAdcGain  gains[CHANCOUNT]     = {DgainDbd3kX1, DgainDbd3kX1, DgainDbd3kX1};	
channels = [0]                                         
flags    = [daqh.DafBipolar]*CHANCOUNT                             

# This is the default name for a DaqBoard3000 when configured through the 
# Control Panel Applet. If you have named your device differently than the default,
# it must be changed here for this example to function.
devName = "DaqBoard3K0"

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
daq.AdcTransferSetBuffer(handle, buffer, BUFFSIZE,CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOn)

#Set to Trigger on hardware analog
daq.SetTriggerEvent(handle, STARTSOURCE, daqh.DetsRisingEdge,  channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, VOLTAGESTART, 0, daqh.DaqStartEvent)
#SSet to Stop on software analog
daq.SetTriggerEvent(handle, STOPSOURCE,  daqh.DetsFallingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeAnalogLocal, VOLTAGEEND,   0, daqh.DaqStopEvent)

#begin data acquisition
print "waiting for trigger voltage...\n"
daq.AdcTransferStart(handle)
daq.AdcArm(handle)

active, retCount = daq.AdcTransferGetStat(handle)
while not (active & daqh.DaafAcqTriggered) and (active & daqh.DaafAcqActive):
    time.sleep(0.1)
    active, retCount = daq.AdcTransferGetStat(handle)

print "\nScan triggered\n"

while( active & daqh.DaafAcqActive):
    time.sleep(0.1)
    #transfer data into computer memory and halt acquisition when done
    active, retCount = daq.AdcTransferGetStat(handle)
    print "Scans acquired: %u\r" % retCount

#Disarm when completed    
daq.AdcDisarm(handle)
print "Scan Completed\n"
print "Performed %d scans\n\n" % retCount

#close device connections
daq.Close(handle)

tail = 0
#calc where the daq left off writing
head = retCount % BUFFSIZE
if retCount > BUFFSIZE: tail = (head+1) % BUFFSIZE


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
for data in conv_buffer: print "%1.3f\t\t" % data

pylab.plot(conv_buffer[0:retCount])
pylab.show()