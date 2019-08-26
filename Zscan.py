__author__ = 'Siddarth'
# Developing the z-scan program with a continuous voltage ramp
# Trial to incorporate user defined values for peak voltage, start and stop signals for a continuous ramp

# DAC:
#   Use channel 0 for z-axis output
#   Use PortAB for digital output streaming (provide a sync pulse indicating the start of the scan)
#   run DAC output and ADC input (counters) synchronously at a low frequency (traditionally we used a binning frequency of 50000Hz/80 ~ 625Hz


import numpy as np
import pylab
import time
import daqx as daq
import daqxh as daqh

# dz/dV slope of piezo controller
dz_dV = 15.0 # um/V (depends on controller and is an approximate value)
z0    = 15.0 # um; z-offset (has to be positive to not damage the piezo)
delz  = 24.0 # um; typical travel of a z-scan
T = float(input("Enter the desired time, in seconds, for one complete scan\n "))  # s;  half period = time to complete an up (or down) ramp
Thalf = T/2
resolution = 1 << 16       # =2**16 (shift bit to left); 16-bit DAC
resolution_half = 1 << 15  # =2**15
Vrange     = 20.0    # V; +-10V output range of DAC
dV_DAC     = Vrange/resolution
vz    = delz/Thalf  # speed of the ramp um/s

# calculate the minimum update rate of DAC to ensure that voltage changes of dV_DAC result in an output update
delV = delz/dz_dV # voltage amplitude of ramp
V0   = z0/dz_dV   # voltage offset
freq_min = delV/dV_DAC/Thalf # minimum update frequency
FREQ = max(1000, freq_min)  # set a lower floor for freq of 1kHz
# make sure the freq is compatible (commensurable) with the number of data point per scan
nwavehalf = int(round(FREQ*Thalf)) # number of data points in half of waveform
nwave = nwavehalf * 2
FREQ = nwavehalf/Thalf

# generate scan waveform
Vtup    = (np.ones(nwavehalf).cumsum()-1)/(nwavehalf-1)*delV + V0    # up-ramp voltage waveform
Vtdown  = np.fliplr([Vtup])[0]      # down-ramp voltage waveform
l = len(Vtup)/2  # facilitates to make a ramp that starts from middle rather than bottom or top
Vt = np.concatenate([Vtup[l:],Vtdown,Vtup[:l]])

# convert Vt into DAC count waveform (-10V = 0,  0V = 32768,  +9.99969482421875V = 65535)
# ((65535 - 32768 - 65535) + count) * dV_DAC = (count - 32768)*dV_DAC
DACwave = np.around(Vt/dV_DAC + resolution_half).astype('uint16')


# prepare waveform for digital output; used to mark the start of the scan
# Note: make sure that the output port is initialized to LOW before start of waveform
COUNT = nwave   # = SCANS
bufSYNC = np.zeros(COUNT , dtype=np.uint16)
bufSYNC[0] = 1                                  # |^|________ single pulse at start of digital waveform
# to read SYNC connect A0 to CNT1

# prepare ADC readSCAN
SCANS = nwave # = COUNT
CHANCOUNT = 2
channels = [0,1]                                    # 16 bit counter, 16 bit counter
gains    = [daqh.DgainDbd3kX1, daqh.DgainDbd3kX1]   # ignored
flags    = [daqh.DafCtr16,daqh.DafCtr16]

# get read buffer for photoncounts and sync pulses
readbuffer    = np.ones((SCANS*CHANCOUNT,), dtype=np.uint16)

# set start and stop conditions of readSCAN
STARTSOURCE	= daqh.DatsExternalTTL
STOPSOURCE	= daqh.DatsScanCount

print "Setting up ADC scan...\n"
daq.AdcSetAcq(handle, daqh.DaamNShot, 0, SCANS)
# Scan settings
daq.AdcSetScan(handle, channels, gains, flags)
# set scan rate
daq.AdcSetFreq(handle, FREQ)
# Setup Channel 0 (photon counts) for count mode 16 bit, clear on read
daq.SetOption(handle, channels[0], daqh.DcofChannel, daqh.DcotCounterEnhMeasurementMode, daqh.DcovCounterEnhMode_Counter + daqh.DcovCounterEnhCounter_ClearOnRead)
# Setup Channel 1 (SYNC pulse read) for count mode 16 bit, clear on read
daq.SetOption(handle, channels[1], daqh.DcofChannel, daqh.DcotCounterEnhMeasurementMode, daqh.DcovCounterEnhMode_Counter + daqh.DcovCounterEnhCounter_ClearOnRead)
# Set buffer location, size and flag settings
daq.AdcTransferSetBuffer(handle, readbuffer, SCANS, CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOff)
# Set to Trigger on hardware trigger
daq.SetTriggerEvent(handle, STARTSOURCE, daqh.DetsRisingEdge,  channels[0], gains[0], flags[0], daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStartEvent)
# Set to Stop when the requested number of scans is completed
daq.SetTriggerEvent(handle, STOPSOURCE,  daqh.DetsRisingEdge, channels[0], gains[0], flags[0], daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStopEvent)

# Set port C to output and initalize [C7 ... C0] as LOW
daq.SetOption(handle,2,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalOutput)
daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2, 0)

# initalize DAC output
# ch0 = V(t)
daq.DacSetOutputMode     (handle, daqh.DddtLocal, 0, daqh.DdomStaticWave)
daq.DacWaveSetTrig       (handle, daqh.DddtLocal, 0, daqh.DdtsImmediate, 0)
daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 0, daqh.DdcsAdcClock)         #slave DAC to ADC clock (synchronous mode)
daq.DacWaveSetFreq       (handle, daqh.DddtLocal, 0, FREQ)                      #set to same frequency as ADC (not sure if this step is necessary)
daq.DacWaveSetMode       (handle, daqh.DddtLocal, 0, daqh.DdwmInfinite, 0)
daq.DacWaveSetBuffer     (handle, daqh.DddtLocal, 0, DACwave, COUNT, daqh.DdtmUserBuffer)
# ch1 = SYNC(t)
daq.DacSetOutputMode     (handle, daqh.DddtLocalDigital, 0, daqh.DdomStaticWave)
daq.DacWaveSetTrig       (handle, daqh.DddtLocalDigital, 0, daqh.DdtsImmediate, 0)
daq.DacWaveSetClockSource(handle, daqh.DddtLocalDigital, 0, daqh.DdcsAdcClock)
daq.DacWaveSetFreq       (handle, daqh.DddtLocalDigital, 0, FREQ)
daq.DacWaveSetMode       (handle, daqh.DddtLocalDigital, 0, daqh.DdwmInfinite, 0)
daq.DacWaveSetBuffer     (handle, daqh.DddtLocalDigital, 0, bufSYNC, COUNT, daqh.DdtmUserBuffer)

# begin data acquisition
daq.AdcTransferStart(handle)
daq.AdcArm(handle)
print "waiting for Scan trigger..."
daq.DacWaveArm(handle, daqh.DddtLocal)  #need to arm ADC before DAC to ensure that both wait for hardware trigger

time.sleep(2)
# provide hardware trigger by changing C0 from 0 to 1 and back
# connect TTLTRG to C0
daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2, 1)
daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2, 0)

# monitor the data aquisition
active, retCount = daq.AdcTransferGetStat(handle)
while active & daqh.DaafAcqActive:
    active, retCount = daq.AdcTransferGetStat(handle)
    print active, retCount

# Disarm when completed
daq.AdcDisarm(handle)
daq.DacWaveDisarm(handle, daqh.DddtLocal)
print "Scan Completed\n"

# buffer data format [CTR0, CTR1, CTR0, CTR1, CTR0, CTR1, ...]
bufCTR0 = readbuffer.reshape(-1,CHANCOUNT)[:,0]
bufCTR1 = readbuffer.reshape(-1,CHANCOUNT)[:,1]

print "bufCTR0 (photon counts)", bufCTR0
print "bufCTR1 (SYNC   counts)", bufCTR1
np.savetxt("PhotonCounts.csv" ,np.column_stack((bufCTR0,bufCTR1)),delimiter=",",header="Photon Counts, SYNC",comments=" ")

pylab.plot(Vt,bufCTR0)
pylab.show()