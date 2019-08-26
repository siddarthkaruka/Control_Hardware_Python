#

import time
import numpy as np
import daqx as daq
import daqxh as daqh

FREQ = 10000

STARTSOURCE	= daqh.DdtsImmediate
STOPSOURCE	= daqh.DatsScanCount
CHANCOUNT	 =  2
xsize = 256 + 2*11
ysize = 256
SCANS       =  xsize*ysize
COUNT = xsize*ysize

#used to configure scan
buffer   = np.ones((SCANS*CHANCOUNT,), dtype=np.uint16)    #WORD        buffer[SCANS*CHANCOUNT];	
channels = [0,1]                                    # 16 bit counter, 16 bit counter
gains    = [daqh.DgainDbd3kX1, daqh.DgainDbd3kX1]  #ignored
flags    = [daqh.DafCtr16,daqh.DafCtr16]


line    = np.ones((xsize,), dtype=np.uint16) 
line    = line.cumsum(dtype=np.uint16)*16 + 32768
bufx    = np.tile(line,ysize)

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
daq.AdcSetFreq(handle, FREQ)

#Setup Channel 0 for count mode
daq.SetOption(handle, channels[0], daqh.DcofChannel, daqh.DcotCounterEnhMeasurementMode, daqh.DcovCounterEnhMode_Counter + daqh.DcovCounterEnhCounter_ClearOnRead)
#Setup Channel 1 for count mode
daq.SetOption(handle, channels[1], daqh.DcofChannel, daqh.DcotCounterEnhMeasurementMode, daqh.DcovCounterEnhMode_Counter + daqh.DcovCounterEnhCounter_ClearOnRead)

#Set buffer location, size and flag settings
daq.AdcTransferSetBuffer(handle, buffer, SCANS, CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOff)
#Set to Trigger on software trigger
daq.SetTriggerEvent(handle, STARTSOURCE, daqh.DetsRisingEdge,  channels[0], gains[0], flags[0], daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStartEvent)
#Set to Stop when the requested number of scans is completed
daq.SetTriggerEvent(handle, STOPSOURCE,  daqh.DetsRisingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStopEvent)

daq.DacSetOutputMode     (handle, daqh.DddtLocal, 0, daqh.DdomStaticWave) 
daq.DacWaveSetTrig       (handle, daqh.DddtLocal, 0, daqh.DdtsImmediate, 0)
daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 0, daqh.DdcsAdcClock)
daq.DacWaveSetFreq       (handle, daqh.DddtLocal, 0, FREQ)  
daq.DacWaveSetMode       (handle, daqh.DddtLocal, 0, daqh.DdwmInfinite, 0)	
daq.DacWaveSetBuffer     (handle, daqh.DddtLocal, 0, bufx, COUNT, daqh.DdtmUserBuffer)

#begin data acquisition
daq.AdcTransferStart(handle)
daq.AdcArm(handle)
daq.DacWaveArm(handle, daqh.DddtLocal)

#print "waiting for soft trigger..."
#time.sleep(10)
#daqAdcSoftTrig(handle)
#print "triggered..."

active, retCount = daq.AdcTransferGetStat(handle)
while active & daqh.DaafAcqActive:
    active, retCount = daq.AdcTransferGetStat(handle)

#Disarm when completed
daq.AdcDisarm(handle)
daq.DacWaveDisarm(handle, daqh.DddtLocal)
print "Scan Completed\n"
daq.Close(handle)

#buffer data format [CTR0, CTR1, CTR0, CTR1, CTR0, CTR1, ...]
bufCTR0 = buffer.reshape(-1,CHANCOUNT)[:,0]
bufCTR1 = buffer.reshape(-1,CHANCOUNT)[:,1]

print "bufCTR0 ", bufCTR0
print "bufCTR1 ", bufCTR1
