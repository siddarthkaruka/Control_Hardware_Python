__author__ = 'Siddarth'

# This is the main program of DAQ board that incorporates all desired functions. Any further modifications can be built as classes and appended to this.

import numpy as np
import pylab
import time as tm
import daqx as daq
import daqxh as daqh
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import matplotlib.pyplot as plt
import matplotlib.cm as cm



class Board:    # Hardware control. Connect to the device in the beginning and close the connection only as the last step. This helps avoid initialization problems.

    def __init__(self):
        self.devName = daq.GetDeviceList()[0]        # Find 1st IOtech device

    def open(self): # Connects to the hardware
        print "Connecting to %s\n\n" % self.devName
        handle = daq.Open(self.devName)          # Open device
        if handle == -1:
            print "Cannot connect to device\n"
            print "Exit"
            sys.exit(handle)
        return handle

    def close(self):
        daq.Close(handle)
        print "\nConnection to %s closed" % self.devName

    def Ctrig(self):
        # Set port C to output and initialize [C7 ... C0] as LOW
        daq.SetOption(handle,2,daqh.DcofChannel,daqh.DcotP2Local8Mode,daqh.DcovDigitalOutput)
        daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2, 0)
        # provide hardware trigger by changing C0 from 0 to 1 and back
        # connect TTLTRG to C0
        daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2, 1)
        daq.IOWrite(handle, daqh.DiodtP2Local8, daqh.DiodpP2Local8, 2, daqh.DioepP2, 0)
        print("Hardware trigger passed.\n")


class Form(QDialog):        # Bring the piezo to focus before performing a z-scan
                            # Contains options for setting by voltage or distance
    def __init__(self, parent=None):

        self.maxVolt = 10.0
        self.minVolt = -10.0
        self.voltage = 1

        super(Form, self).__init__(parent)

        VoltageLabel = QLabel(" Voltage:         ")
        self.voltageSpinBox = QDoubleSpinBox()
        self.voltageSpinBox.setRange(1, 3)
        self.voltageSpinBox.setValue(2)
        self.voltageSpinBox.setSuffix("     ")
        self.voltageSpinBox.setSingleStep(0.01)

        DistanceLabel = QLabel(" Distance:           ")
        self.distanceSpinBox = QDoubleSpinBox()
        self.distanceSpinBox.setRange(15, 45)
        self.distanceSpinBox.setValue(30)
        self.distanceSpinBox.setSuffix("     ")
        self.distanceSpinBox.setSingleStep(1)

        grid = QGridLayout()
        grid.addWidget(VoltageLabel, 0, 0)
        grid.addWidget(self.voltageSpinBox, 0, 1)
        grid.addWidget(DistanceLabel, 1, 0)
        grid.addWidget(self.distanceSpinBox, 1, 1)
        self.setLayout(grid)


        self.connect(self.voltageSpinBox,
                     SIGNAL("valueChanged(double)"), self.updateVt)
        self.connect(self.distanceSpinBox,
                     SIGNAL("valueChanged(double)"), self.updateDt)

        self.setWindowTitle("Piezo focus")
        self.updateDt()

    def updateVt(self):
        self.voltage = self.voltageSpinBox.value()
        self.distanceSpinBox.setValue(self.voltage*15)      # Assumes that piezo moves 15 um per volt.
        cnt_vlt = int(round( (self.voltage-self.minVolt)*65535/(self.maxVolt-self.minVolt) ))
        daq.DacSetOutputMode(handle, daqh.DddtLocal, 0, daqh.DdomVoltage)
        daq.DacWt(handle, daqh.DddtLocal, 0, cnt_vlt)

    def updateDt(self):
        distance = self.distanceSpinBox.value()
        self.voltageSpinBox.setValue(distance/15)           # Assumes that piezo moves 15 um per volt.
        self.voltage = self.voltageSpinBox.value()
        cnt_vlt = int(round( (self.voltage-self.minVolt)*65535/(self.maxVolt-self.minVolt) ))
        daq.DacSetOutputMode(handle, daqh.DddtLocal, 0, daqh.DdomVoltage)
        daq.DacWt(handle, daqh.DddtLocal, 0, cnt_vlt)


class Zscan:    # Developing the z-scan program with a continuous voltage ramp

    def __init__(self):
        self.i = 0      # Used in self.run() to check if the device is setup at least once

    def setup(self):
        # DAC:
        #   Use channel 0 for z-axis output
        #   Use PortAB for digital output streaming (provide a sync pulse indicating the start of the scan)
        #   run DAC output and ADC input (counters) synchronously at a low frequency (traditionally we used a binning frequency of 50000Hz/80 ~ 625Hz
        # dz/dV slope of piezo controller
        self.dz_dV = 15.0 # um/V (depends on controller and is an approximate value)
        self.z0    = 15.0 # um; z-offset (has to be positive to not damage the piezo)
        self.delz  = 24.0 # um; typical travel of a z-scan
        self.T = float(input("Enter the desired time, in seconds, for one complete zscan\n "))  # s;  half period = time to complete an up (or down) ramp
        self.N= int(input("How many scans do you wish to perform in single run?\n"))
        self.Thalf = self.T/2
        self.resolution = 1 << 16       # =2**16 (shift bit to left); 16-bit DAC
        self.resolution_half = 1 << 15  # =2**15
        self.Vrange     = 20.0    # V; +-10V output range of DAC
        self.dV_DAC     = self.Vrange/self.resolution
        self.vz    = self.delz/self.Thalf  # speed of the ramp um/s

        # calculate the minimum update rate of DAC to ensure that voltage changes of dV_DAC result in an output update
        self.delV = self.delz/self.dz_dV # voltage amplitude of ramp
        self.V0   = form.voltage   # voltage offset
        self.freq_min = self.delV/self.dV_DAC/self.Thalf # minimum update frequency
        self.FREQ = max(1000, self.freq_min)  # set a lower floor for freq of 1kHz
        # make sure the freq is compatible (commensurable) with the number of data point per scan
        self.nwavehalf = int(round(self.FREQ*self.Thalf)) # number of data points in half of waveform
        self.nwave = self.nwavehalf * 2
        self.FREQ = self.nwavehalf/self.Thalf

        # generate scan waveform
        self.Vtup    = (np.ones(self.nwavehalf).cumsum()-1)/(self.nwavehalf-1)*self.delV     # up-ramp voltage waveform
        self.Vtdown  = np.fliplr([self.Vtup])[0]      # down-ramp voltage waveform
        self.l = len(self.Vtup)/2  # facilitates to make a ramp that starts from middle rather than bottom or top
        self.Vtmid = self.Vtup[self.l]
        self.Vtadjust = self.V0 - self.Vtmid      # facilitates the mid-ramp to start at the focus point set by piezo
        self.Vt = np.concatenate([self.Vtup[self.l:] + self.Vtadjust, self.Vtdown + self.Vtadjust, self.Vtup[:self.l] + self.Vtadjust])
        self.Vt = np.tile(self.Vt,self.N)

        # convert Vt into DAC count waveform (-10V = 0,  0V = 32768,  +9.99969482421875V = 65535)
        # ((65535 - 32768 - 65535) + count) * dV_DAC = (count - 32768)*dV_DAC
        self.DACwave = np.around(self.Vt/self.dV_DAC + self.resolution_half).astype('uint16')


        # prepare waveform for digital output; used to mark the start of the scan
        # Note: make sure that the output port is initialized to LOW before start of waveform
        self.COUNT = self.N*self.nwave   # = SCANS
        self.bufSYNC = np.zeros(self.COUNT , dtype=np.uint16)
        self.bufSYNC[0] = 1                                  # |^|________ single pulse at start of digital waveform
        # to read SYNC connect A0 to CNT1

        # prepare ADC readSCAN
        self.SCANS = self.N*self.nwave # = COUNT
        self.CHANCOUNT = 2
        self.channels = [0,1]                                    # 16 bit counter, 16 bit counter
        self.gains    = [daqh.DgainDbd3kX1, daqh.DgainDbd3kX1]   # ignored
        self.flags    = [daqh.DafCtr16,daqh.DafCtr16]

        # get read buffer for photoncounts and sync pulses
        self.readbuffer    = np.ones((self.SCANS*self.CHANCOUNT,), dtype=np.uint16)

        # set start and stop conditions of readSCAN
        self.STARTSOURCE	= daqh.DatsExternalTTL
        self.STOPSOURCE	= daqh.DatsScanCount

        print "Setting up ADC scan...\n"
        daq.AdcSetAcq(handle, daqh.DaamNShot, 0, self.SCANS)
        # Scan settings
        daq.AdcSetScan(handle, self.channels, self.gains, self.flags)
        # set scan rate
        daq.AdcSetFreq(handle, self.FREQ)
        # Setup Channel 0 (photon counts) for count mode 16 bit, clear on read
        daq.SetOption(handle, self.channels[0], daqh.DcofChannel, daqh.DcotCounterEnhMeasurementMode, daqh.DcovCounterEnhMode_Counter + daqh.DcovCounterEnhCounter_ClearOnRead)
        # Setup Channel 1 (SYNC pulse read) for count mode 16 bit, clear on read
        daq.SetOption(handle, self.channels[1], daqh.DcofChannel, daqh.DcotCounterEnhMeasurementMode, daqh.DcovCounterEnhMode_Counter + daqh.DcovCounterEnhCounter_ClearOnRead)
        # Set buffer location, size and flag settings
        daq.AdcTransferSetBuffer(handle, self.readbuffer, self.SCANS, self.CHANCOUNT, daqh.DatmUpdateSingle + daqh.DatmCycleOff)
        # Set to Trigger on hardware trigger
        daq.SetTriggerEvent(handle, self.STARTSOURCE, daqh.DetsRisingEdge,  self.channels[0], self.gains[0], self.flags[0], daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStartEvent)
        # Set to Stop when the requested number of scans is completed
        daq.SetTriggerEvent(handle, self.STOPSOURCE,  daqh.DetsRisingEdge, self.channels[0], self.gains[0], self.flags[0], daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStopEvent)
        print("Setup complete.\n")

    def run(self):

        if self.i is 0:     # Check to see if the zscan is setup at least once.
            print("You need to setup the program first. Starting setup.. \n")
            self.setup()
            self.i = 1
            print("Starting the process now.. \n")

        if self.V0 is not form.voltage:         # Check to see if the focus has changed
            self.V0 = form.voltage              # Change the mid-ramp settings caused by change in focus
            self.Vtadjust = self.V0 - self.Vtmid      # facilitates the mid-ramp to start at the focus point set by piezo
            self.Vt = np.concatenate([self.Vtup[self.l:] + self.Vtadjust, self.Vtdown + self.Vtadjust, self.Vtup[:self.l] + self.Vtadjust])
            self.Vt = np.tile(self.Vt,self.N)
            self.DACwave = np.around(self.Vt/self.dV_DAC + self.resolution_half).astype('uint16')

        # initialize DAC output
        # ch0 = V(t)
        daq.DacSetOutputMode     (handle, daqh.DddtLocal, 0, daqh.DdomStaticWave)
        daq.DacWaveSetTrig       (handle, daqh.DddtLocal, 0, daqh.DdtsImmediate, 0)
        daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 0, daqh.DdcsAdcClock)         #slave DAC to ADC clock (synchronous mode)
        daq.DacWaveSetFreq       (handle, daqh.DddtLocal, 0, self.FREQ)                      #set to same frequency as ADC (not sure if this step is necessary)
        daq.DacWaveSetMode       (handle, daqh.DddtLocal, 0, daqh.DdwmInfinite, 0)
        daq.DacWaveSetBuffer     (handle, daqh.DddtLocal, 0, self.DACwave, self.COUNT, daqh.DdtmUserBuffer)
        # ch1 = SYNC(t)
        daq.DacSetOutputMode     (handle, daqh.DddtLocalDigital, 0, daqh.DdomStaticWave)
        daq.DacWaveSetTrig       (handle, daqh.DddtLocalDigital, 0, daqh.DdtsImmediate, 0)
        daq.DacWaveSetClockSource(handle, daqh.DddtLocalDigital, 0, daqh.DdcsAdcClock)
        daq.DacWaveSetFreq       (handle, daqh.DddtLocalDigital, 0, self.FREQ)
        daq.DacWaveSetMode       (handle, daqh.DddtLocalDigital, 0, daqh.DdwmInfinite, 0)
        daq.DacWaveSetBuffer     (handle, daqh.DddtLocalDigital, 0, self.bufSYNC, self.COUNT, daqh.DdtmUserBuffer)



        # begin data acquisition
        daq.AdcTransferStart(handle)
        daq.AdcArm(handle)
        print "waiting for Scan trigger...\n"
        daq.DacWaveArm(handle, daqh.DddtLocal)  #need to arm ADC before DAC to ensure that both wait for hardware trigger

        tm.sleep(1)

        self.win = pg.GraphicsWindow()
        self.win.setWindowTitle('Photon Counts')

        self.p1 = self.win.addPlot()
        self.p1.setLabel('bottom', 'Time', 's')
        self.curve1 = self.p1.plot()
        self.win.nextRow()
        self.p2 = self.win.addPlot()
        self.p2.setLabel('bottom', 'Voltage', 'V')
        self.curve2 = self.p2.plot()
        self.curvetime = np.arange(self.SCANS)*(self.T*self.N/self.SCANS)       # Used to plot real time data with x-axis as time in seconds

        self.timer = pg.QtCore.QTimer()
        self.timer.setInterval(self.T)      # T milliseconds
        self.timer.timeout.connect(self.update)

        handle1.Ctrig()
        print("Scanning...\n")


        self.timer.start()



    def update(self):
        active, retCount = daq.AdcTransferGetStat(handle)
        bufCTR0 = self.readbuffer.reshape(-1,self.CHANCOUNT)[:,0]
        self.curve1.setData(self.curvetime[:retCount],bufCTR0[:retCount])
        self.curve2.setData(self.Vt[:retCount],bufCTR0[:retCount])
        if retCount >= self.SCANS:          # For some reason if retCount is self.SCANS: doesn't work ???
            self.timer.stop()
            # Disarm when completed - placed inside this to avoid possible disarming even before acquiring desired data
            daq.AdcDisarm(handle)
            daq.DacWaveDisarm(handle, daqh.DddtLocal)
            print "Scan Completed\n"

            # buffer data format [CTR0, CTR1, CTR0, CTR1, CTR0, CTR1, ...]
            bufCTR0 = self.readbuffer.reshape(-1,self.CHANCOUNT)[:,0]
            bufCTR1 = self.readbuffer.reshape(-1,self.CHANCOUNT)[:,1]

            print "bufCTR0 (photon counts)", bufCTR0
            print "bufCTR1 (SYNC   counts)", bufCTR1
            np.savetxt("PhotonCounts.csv" ,np.column_stack((bufCTR0,bufCTR1,self.DACwave)),delimiter=",",header="Photon Counts, SYNC, Voltage",comments=" ")


class Galvo(QDialog):

    def __init__(self, parent=None):

        self.maxVolt = 10.0
        self.minVolt = -10.0
        self.voltage = 1
        self.j = 0

        super(Galvo, self).__init__(parent)

        XLabel = QLabel(" Galvo X:         ")
        self.XSpinBox = QDoubleSpinBox()
        self.XSpinBox.setRange(0, 10)
        self.XSpinBox.setValue(0)
        self.XSpinBox.setSingleStep(0.1)

        YLabel = QLabel(" Galvo Y:           ")
        self.YSpinBox = QDoubleSpinBox()
        self.YSpinBox.setRange(0, 10)
        self.YSpinBox.setValue(0)
        self.YSpinBox.setSingleStep(0.1)

        button1 = QPushButton("Ellipse")
        button2 = QPushButton("Raster")
        #button3 = QPushButton("STOP")

        grid = QGridLayout()
        grid.addWidget(XLabel, 0, 0)
        grid.addWidget(self.XSpinBox, 0, 1)
        grid.addWidget(YLabel, 1, 0)
        grid.addWidget(self.YSpinBox, 1, 1)
        grid.addWidget(button1, 2, 0)
        grid.addWidget(button2, 2, 1)
        #grid.addWidget(button3, 2, 2)
        self.setLayout(grid)

        self.connect(self.XSpinBox,SIGNAL("valueChanged(double)"), self.updateX)
        self.connect(self.YSpinBox,SIGNAL("valueChanged(double)"), self.updateY)
        self.connect(button1,SIGNAL("clicked()"),self.ellipse)
        self.connect(button2,SIGNAL("clicked()"),self.raster)
        #self.connect(button3,SIGNAL("clicked()"),self.STOP)
        self.setWindowTitle("Galvo Controls")
        self.updateX()
        self.updateY()


    def updateX(self):
        self.voltage = self.XSpinBox.value()
        cnt_vlt = int(round( (self.voltage-self.minVolt)*65535/(self.maxVolt-self.minVolt) ))
        daq.DacSetOutputMode(handle, daqh.DddtLocal, 1, daqh.DdomVoltage)
        daq.DacWt(handle, daqh.DddtLocal, 1, cnt_vlt)

    def updateY(self):
        self.voltage = self.YSpinBox.value()
        cnt_vlt = int(round( (self.voltage-self.minVolt)*65535/(self.maxVolt-self.minVolt) ))
        daq.DacSetOutputMode(handle, daqh.DddtLocal, 2, daqh.DdomVoltage)
        daq.DacWt(handle, daqh.DddtLocal, 2, cnt_vlt)

    def ellipse(self):

        minVolt = -10.0
        maxVolt = 10.0
        freq = 2000                                 # frequency
        NS = freq*1                                 # total number of seconds for entire scan
        COUNT	= 32                                # 32 data points per circle
        DACFREQ	= freq*COUNT                        # frequency at which data points are updated for DAC output
        i = np.arange(COUNT)*((2*np.pi)/32)         # 2*pi*1second for 32 points => 2pi/32
        x = np.cos(i)*1
        y = np.sin(i)*1

        cnt_x = ((( (x+self.XSpinBox.value() - minVolt)*65535/(maxVolt - minVolt) ))).astype(np.uint16)
        cnt_y = ((( (y+self.YSpinBox.value() - minVolt)*65535/(maxVolt - minVolt) ))).astype(np.uint16)

        daq.DacSetOutputMode(handle, daqh.DddtLocal, 1,  daqh.DdomStaticWave)
        daq.DacWaveSetTrig(handle,  daqh.DddtLocal, 1,  daqh.DdtsImmediate, 0)
        daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 1,  daqh.DdcsDacClock)
        daq.DacWaveSetFreq(handle,  daqh.DddtLocal, 1, DACFREQ)
        daq.DacWaveSetMode(handle,  daqh.DddtLocal, 1,  daqh.DdwmNShot, NS*COUNT)
        daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 1, cnt_x, COUNT, daqh.DdtmUserBuffer)
        daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 1)


        daq.DacSetOutputMode(handle, daqh.DddtLocal, 2,  daqh.DdomStaticWave)
        daq.DacWaveSetTrig(handle,  daqh.DddtLocal, 2,  daqh.DdtsImmediate, 0)
        daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 2,  daqh.DdcsDacClock)
        daq.DacWaveSetFreq(handle,  daqh.DddtLocal, 2, DACFREQ)
        daq.DacWaveSetMode(handle,  daqh.DddtLocal, 2,  daqh.DdwmNShot, NS*COUNT)
        daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 2, cnt_y, COUNT, daqh.DdtmUserBuffer)
        daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 2)


        daq.DacWaveArm(handle, daqh.DddtLocal)
        print("Scanning in progress")
        tm.sleep(NS/freq + 0.1)
        print("Scanning complete")
        daq.DacWaveDisarm(handle, daqh.DddtLocal)

    #def STOP(self):
        #daq.DacWaveDisarm(handle, daqh.DddtLocal)

    def raster(self):
        minVolt = -10.0
        maxVolt = 10.0
        freq = 1
        COUNT = 68*62
        FREQ = freq*COUNT
        x = []
        y = []
        NS = freq*1
        i = 0
        while i < 62:
            j = 0
            while j < 62:
                x.append(j)
                y.append(i)
                j +=1
            j = 61
            if i is not 61:
                while j >= 10:
                    j -= 10
                    x.append(j)
                    y.append(i)
            if i is 61:                             # The scan now has 62+6 points in each line and when it reaches the last line, it uses the same 6 points to go to beginning point
                while j >= 10:                          # For the actual data that we are interested, we have to ignore 6 points after every 62 points
                    j -= 10
                    i -= 10
                    x.append(j)
                    y.append(i)
                i = 61
            i +=1



        cnt_x = ((( (np.array(x)*0.01 - minVolt)*65535/(maxVolt - minVolt) ))).astype(np.uint16)
        cnt_y = ((( (np.array(y)*0.01 - minVolt)*65535/(maxVolt - minVolt) ))).astype(np.uint16)

        daq.DacSetOutputMode(handle, daqh.DddtLocal, 1,  daqh.DdomStaticWave)
        daq.DacWaveSetTrig(handle,  daqh.DddtLocal, 1,  daqh.DdtsImmediate, 0)
        daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 1,  daqh.DdcsAdcClock)
        daq.DacWaveSetFreq(handle,  daqh.DddtLocal, 1, FREQ)
        daq.DacWaveSetMode(handle,  daqh.DddtLocal, 1,  daqh.DdwmNShot, NS*COUNT)
        daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 1, cnt_x, COUNT, daqh.DdtmUserBuffer)
        daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 1)


        daq.DacSetOutputMode(handle, daqh.DddtLocal, 2,  daqh.DdomStaticWave)
        daq.DacWaveSetTrig(handle,  daqh.DddtLocal, 2,  daqh.DdtsImmediate, 0)
        daq.DacWaveSetClockSource(handle, daqh.DddtLocal, 2,  daqh.DdcsAdcClock)
        daq.DacWaveSetFreq(handle,  daqh.DddtLocal, 2, FREQ)
        daq.DacWaveSetMode(handle,  daqh.DddtLocal, 2,  daqh.DdwmNShot, NS*COUNT)
        daq.DacWaveSetBuffer(handle, daqh.DddtLocal, 2, cnt_y, COUNT, daqh.DdtmUserBuffer)
        daq.DacWaveSetUserWave(handle, daqh.DddtLocal, 2)

        self.rasterbuffer = np.ones(NS*COUNT, dtype=np.uint16)

        channels = [0]
        gains    = [daqh.DgainDbd3kX1]
        flags    = [daqh.DafCtr16]
        daq.AdcSetAcq(handle, daqh.DaamNShot, 0, NS*COUNT)
        daq.AdcSetScan(handle, channels, gains, flags)
        daq.AdcSetFreq(handle, FREQ)
        daq.SetOption(handle, 0, daqh.DcofChannel, daqh.DcotCounterEnhMeasurementMode, daqh.DcovCounterEnhMode_Counter + daqh.DcovCounterEnhCounter_ClearOnRead)
        daq.AdcTransferSetBuffer(handle, self.rasterbuffer, NS*COUNT, 1, daqh.DatmUpdateSingle + daqh.DatmCycleOff)
        daq.SetTriggerEvent(handle, daqh.DatsExternalTTL, daqh.DetsRisingEdge,  0, daqh.DgainDbd3kX1, daqh.DafCtr16, daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStartEvent)
        daq.SetTriggerEvent(handle, daqh.DatsScanCount,  daqh.DetsRisingEdge, 0, daqh.DgainDbd3kX1, daqh.DafCtr16, daqh.DaqTypeCounterLocal, 0, 0, daqh.DaqStopEvent)


        daq.AdcTransferStart(handle)
        daq.AdcArm(handle)
        print "waiting for Scan trigger...\n"
        daq.DacWaveArm(handle, daqh.DddtLocal)

        tm.sleep(1)
        handle1.Ctrig()

        print("Scanning...\n")

        active, retCount = daq.DacTransferGetStat(handle,daqh.DddtLocal,1)
        while active & daqh.DdafTransferActive:
            active, retCount = daq.DacTransferGetStat(handle,daqh.DddtLocal,1)
            #print(active, retCount)
        tm.sleep(0.1)         # Sometimes Data Acquisition isn't finished yet even though the DAC output is complete. Don't know why??? (Update frequencies and # of data points are the same)
        daq.AdcDisarm(handle)
        daq.DacWaveDisarm(handle, daqh.DddtLocal)

        print(self.rasterbuffer, len(self.rasterbuffer))
        imagedata = np.zeros((62,62))
        i = j = k = 0
        while k < len(self.rasterbuffer):
            imagedata[j,i] = self.rasterbuffer[k]
            i += 1
            if i%62 is 0:
                k += 6
                j += 1
                i = 0
            k += 1
        print(imagedata)

        plt.clf()
        plt.imshow(imagedata, cmap = cm.Greys_r)
        plt.show()

class MainGUI(QDialog):

    def __init__(self, parent = None):

        super(MainGUI, self).__init__(parent)
        self.setWindowTitle("DAQ board")
        button1 = QPushButton("Setup")
        button2 = QPushButton("Run")
        button3 = QPushButton("Z-focus")
        button4 = QPushButton("Galvo controls")
        self.connect(button1,SIGNAL("clicked()"),self.one)
        self.connect(button2,SIGNAL("clicked()"), self.two)
        self.connect(button3,SIGNAL("clicked()"),self.focus)
        self.connect(button4,SIGNAL("clicked()"), self.galvo)
        ZscanLabel = QLabel("Z-scan: ")
        grid = QGridLayout()
        grid.addWidget(ZscanLabel, 0, 0)
        grid.addWidget(button1, 0, 2)
        grid.addWidget(button2, 0, 3)
        grid.addWidget(button3, 0, 1)
        grid.addWidget(button4, 1, 0)
        self.setLayout(grid)

    def one(self):
        zscan.setup()
    def two(self):
        zscan.run()
    def focus(self):
        form.show()
    def galvo(self):
        galvo.show()






if __name__ == "__main__":

    handle1 = Board()
    handle = handle1.open()

    app = QApplication([])

    zscan = Zscan()
    form = Form()
    galvo = Galvo()
    GUI = MainGUI()
    GUI.show()
    app.exec_()
    handle1.close()