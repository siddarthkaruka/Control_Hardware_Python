# Library containing python wrappers for the API of the IOtech boards 
#
# Used 'PyIOTech.py' (https://github.com/fake-name/PyIOTech) as a template
#
# Use ctypes to wrap C-functions described in the ProgrammersManual.pdf
# The C-functions are exported by a DLL provided by IOtech.
# Use: daqx64.dll  for 64-bit OS
#        daqx.dll  for 32-bit OS
#
# This is still a work in progress. Not all C-functions are wrapped 
# and the interfacing is not as uniform as it should be.
#
# Suggest to import daqx as daq
#
#
# JM, 6/10/2015


# ctypes needed to convert parameters from python to C representation and vice versa
import ctypes as ct
from ctypes import wintypes as wt
from ctypes.util import find_library

import sys
import traceback
import daqxh              #definitions found in daqx.h

import numpy as np

#detect if OS is 64bit or 32bit; this code is a bit of a hack, but found no better solution
is_64bit = sys.maxsize > 2**32
if is_64bit:
    daq = ct.OleDLL("daqx64")  #load 64bit dll 'daqx64.dll'
else:
    daq = ct.OleDLL("daqx")    #load 32bit dll 'daqx.dll'

#
# assume enum types in header file are 32bit integers
#


#======================================================================
#
#Error Handling
#
#======================================================================

class IOTechLibraryBaseError( Exception ):
    """base class for all IOTechLibrary exceptions"""
    pass

class IOTechLibraryError( IOTechLibraryBaseError ):
    """error occurred within the C layer of IOTech Library"""
    def __init__(self, errNum):
        errstr = 'Error %d: %s' % (errNum, FormatError(errNum))
        self.errno = errNum
        Exception.__init__(self, errstr)

class IOTechLibraryPythonError( IOTechLibraryBaseError ):
    """error occurred within the Python layer of IOTech Library"""
    pass

class DaqError(Exception):
    def __init__(self, errcode):
        self.errcode = errcode
        self.msg = FormatError(errcode)
        #print '----------------------'
        #print self.errcode, self.msg
        self.args = (self.errcode, self.msg)
    def __str__(self):
        return '%i ' % self.errcode + self.msg
    def __getitem__(self,key):
        return self.args[key]

def FormatError(errNum):
    """Returns the text-string equivalent for the specified error condition code"""
    msg = (ct.c_char*64)() #Messages at minimum is 64 characters
    CHK(daq.daqFormatError(errNum, ct.byref(msg)))
    return msg.value

#----------------------------------------------------------------------------------------------
#checks if call to c-function retruned an error
def CHK(Status):
    """raise appropriate exception if error occurred"""
    if Status != daqxh.DerrNoError:
        raise DaqError(Status)

#checks proper formatting of the numpy array to be passed to a c-function
def CHK_ARRAY( arr, N, nxtype ):
    if not hasattr(arr,'shape'):
        raise IOTechLibraryPythonError("input argument is not an array")
    if len(arr.shape) != 1:
        raise IOTechLibraryPythonError("array is not rank 1")
    if arr.dtype != nxtype:
        raise IOTechLibraryPythonError("array is not correct data type '%s'"%str(nxtype))
    if len(arr) < N:
        raise IOTechLibraryPythonError("array is not large enough")
    if not arr.flags['CONTIGUOUS']:
        raise IOTechLibraryPythonError("array is not contiguous")
    return arr
#----------------------------------------------------------------------------------------------




#daqOnline determines if a device is online
def Online(handle):
    online = ct.c_bool(False)
    CHK(daq.daqOnline(handle, ct.byref(online)))
    return online.value

#daqGetDeviceCount returns the number of currently configured devices.
def GetDeviceCount():
    count = ct.c_uint32(0)
    CHK(daq.daqGetDeviceCount(ct.byref(count)))
    return count.value

#daqGetDeviceList returns a list of currently configured device names.
def GetDeviceList():
    class daqDeviceListT(ct.Structure):
        """
        This class emulates a C struct for the device name
        """
        _fields_ = [("devicename", ct.c_char * 64)]

    count = GetDeviceCount()
    count_uint32 = ct.c_uint32(count)
    devlist = (daqDeviceListT*count)() #Iterable ctypes array
    CHK(daq.daqGetDeviceList(devlist, ct.byref(count_uint32)))
    return [i.devicename for i in devlist]

#======================================================================
#
#Event Handling   --   General Commands
#
#======================================================================

#daqSetTimeout sets the time-out for waiting on either a single event or multiple events.
def SetTimeout (handle, mSecTimeout):
    CHK(daq.daqSetTimeout (handle, mSecTimeout))

#daqWaitForEvent waits on a specific event to occur on the specified device.
def WaitForEvent(handle, event):
    CHK(daq.daqWaitForEvent(handle, event))

#daqGetDriverVersion retrieves the revision level of the driver currently in use
def GetDriverVersion():
    version = ct.c_uint32(0)
    CHK(daq.daqGetDriverVersion(ct.byref(version)))
    return version.value

#daqGetDeviceProperties returns the properties for a specified device
def GetDeviceProperties(deviceName):

    class deviceProps(ct.Structure):
        """
        This class emulates a C struct for the device properties calls
        """
        _fields_ = [("deviceType", ct.c_ulong),
                    ("basePortAddress", ct.c_ulong),
                    ("dmaChannel", ct.c_ulong),
                    ("socket", ct.c_ulong),
                    ("interruptLevel", ct.c_ulong),
                    ("protocol", ct.c_ulong),
                    ("alias", ct.c_char*64),
                    ("maxAdChannels", ct.c_ulong),
                    ("maxDaChannels", ct.c_ulong),
                    ("maxDigInputBits", ct.c_ulong),
                    ("maxDigOutputBits", ct.c_ulong),
                    ("maxCtrChannels", ct.c_ulong),
                    ("mainUnitAdChannels", ct.c_ulong),
                    ("mainUnitDaChannels", ct.c_ulong),
                    ("mainUnitDigInputBits", ct.c_ulong),
                    ("mainUnitDigOutputBits", ct.c_ulong),
                    ("mainUnitCtrChannels", ct.c_ulong),
                    ("adFifoSize", ct.c_ulong),
                    ("daFifoSize", ct.c_ulong),
                    ("adResolution", ct.c_ulong),
                    ("daResolution", ct.c_ulong),
                    ("adMinFreq", ct.c_float),
                    ("adMaxFreq", ct.c_float),
                    ("daMinFreq", ct.c_float),
                    ("daMaxFreq", ct.c_float)]

    properties = {}
    deviceNamepnt = ct.c_char_p(deviceName)
    devProps = deviceProps()
    devicePropspnt = ct.pointer(devProps)
    CHK(daq.daqGetDeviceProperties(deviceNamepnt,devicePropspnt))

    #Rather than return a class, device properties are put into
    # a python dictionary
    for i in dir(devProps):
        if not i.startswith('_'):
            val = getattr(devProps, i)
            properties[i]=val

    return properties

def GetLastError(handle):
    errCode_uint32 = ct.c_uint32(0)
    CHK(daq.daqGetLastError(handle, ct.byref(errCode_uint32)))
    return errCode_uint32.value


#======================================================================
#
#ADC
#
#======================================================================

#daqAdcArm arms an ADC acquisition by enabling the currently defined ADC configuration for an acquisition.
def AdcArm(handle):
    CHK(daq.daqAdcArm(handle))

#daqAdcBufferRotate

#daqAdcCalcTrig  --obsolete

#daqAdcDisarm disarms an ADC acquisition, if one is currently active.
def AdcDisarm(handle):
    CHK(daq.daqAdcDisarm(handle))

#daqAdcExpSetBank

#daqAdcGetFreq reads the sampling frequency of the pacer clock
def AdcGetFreq(handle):
    freq = ct.c_float(0)
    CHK(daq.daqAdcGetFreq(handle, ct.byref(freq)))
    return freq.value

#daqAdcGetScan reads the current scan group, which consists of all configured channels
#def AdcGetScan(handle, channels, gains, flags, chanCount):
#
#    CHK(daq.daqAdcGetScan(handle, channels, gains, flags, chanCount))
#

#daqAdcRd takes a single reading from the given local A/D channel using a software trigger
def AdcRd(handle, chan, sample, gain, flags):
    sample_WORD = wt.WORD()
    CHK(daq.daqAdcRd(handle, chan, ct.byref(sample_WORD), gain, flags))
    return sample_WORD.value

#daqAdcSetAcq configures the acquisition mode and the pre- and post-trigger scan durations
def AdcSetAcq(handle, mode, preTrigCount, postTrigCount):
    CHK(daq.daqAdcSetAcq(handle, mode, preTrigCount, postTrigCount))

#daqAdcSetScan configures an acquisition scan group consisting of multiple channels.
def AdcSetScan(handle, channels, gains, flags):
    chanCount = len(channels)
    if type(flags) != list:
        flags = [flags]
    #Making ctypes iterable arrays
    chan_array = (wt.DWORD * chanCount)()
    gain_array = (wt.DWORD * chanCount)()
    flag_array = (wt.DWORD * chanCount)()
    #Take the values of a python list and put them in a Ctypes array
    for i in range(chanCount):
        chan_array[i] = channels[i]
    for i in range(chanCount):
        gain_array[i] = gains[i]
    for i in range(chanCount):
        flag_array[i] = flags[i]
    pchan_array = ct.pointer(chan_array)
    pgain_array = ct.pointer(gain_array)
    pflag_array = ct.pointer(flag_array)
    CHK(daq.daqAdcSetScan(handle, pchan_array, pgain_array, pflag_array, wt.DWORD(chanCount)))

#daqAdcSetClockSource sets up the clock source to be used to drive the acquisition frequency.
def AdcSetClockSource(handle, clockSource):
    CHK(daq.daqAdcSetClockSource(handle, clockSource))


#daqAdcSetDiskFile sets a destination file for ADC data transfers. ADC direct-to-disk data transfers will be directed to the specified disk file.
def AdcSetDiskFile(handle, filename, openMode, preWrite):
    pfilename = ct.c_char_p(filename)
    CHK(daq.daqAdcSetDiskFile(handle, pfilename, openMode, preWrite))


#daqAdcSetFreq calculates and sets the frequency of the internal scan pacer clock of the device using the frequency specified in Hz
def AdcSetFreq(handle, freq):
    CHK(daq.daqAdcSetFreq(handle, ct.c_float(freq)))

#daqSetOption allows the setting of options for a devices channel/signal path configuration
def SetOption (handle, chan, flags, optionType, optionValue):
    CHK(daq.daqSetOption (handle, chan, flags, optionType, ct.c_float(optionValue)))

#daqAdcSoftTrig is used to send a software trigger command to the device
def AdcSoftTrig(handle):
    CHK(daq.daqAdcSoftTrig(handle))

#daqAdcTransferSetBuffer configures transfer buffers for acquired data, and can also be used to
#    configure the specified user- or driver-allocated buffers for subsequent acquisition transfers.
def AdcTransferSetBuffer(handle, buf, scanCount, channelCount,transferMask):
    if buf is None:
        CHK(daq.daqAdcTransferSetBuffer(handle, None, scanCount,transferMask))
    else:
        CHK_ARRAY( buf, scanCount*channelCount, np.uint16 )
        CHK(daq.daqAdcTransferSetBuffer(handle, buf.ctypes.data, scanCount,transferMask))

#daqSetTriggerEvent sets an acquisition trigger start event or an acquisition stop event.
def SetTriggerEvent(handle, trigSource, trigSensitivity, channel, gainCode, flags, channelType, level, variance, event):
    CHK(daq.daqSetTriggerEvent(handle, trigSource, trigSensitivity, channel, gainCode, flags, channelType, ct.c_float(level), ct.c_float(variance), event))

#daqAdcTransferStart initiates an ADC acquisition transfer.
def AdcTransferStart(handle):
    CHK(daq.daqAdcTransferStart(handle))

#daqAdcTransferBufData requests a transfer of scanCount scans from the driver allocated acquisition
#buffer (driver buffer) to the specified linear data retrieval buffer (buf). The driver buffer is configured with
#the daqAdcTransferSetBuffer function.
def AdcTransferBufData(handle, buf, scanCount, channelCount, bufMask):
    retCount_uint32 = ct.c_uint32(0)
    CHK_ARRAY( buf, scanCount*channelCount, np.uint16 )
    CHK(daq.daqAdcTransferBufData(handle, buf.ctypes.data, scanCount, bufMask, ct.byref(retCount_uint32)))
    return retCount_uint32.value

#daqAdcTransferGetStat retrieves the current state of an acquisition transfer, and can be used to initiate transfers to the disk.
def AdcTransferGetStat(handle):
    active = wt.DWORD()
    retCount = wt.DWORD()
    CHK(daq.daqAdcTransferGetStat(handle, ct.byref(active), ct.byref(retCount)))
    return active.value, retCount.value




#daqIOwrite writes to the specified port on the selected device
def IOWrite(handle, devType, devPort, whichDevice, whichExpPort, value):
    CHK(daq.daqIOWrite(handle, devType, devPort, whichDevice, whichExpPort, value))

#daqIOWriteBit writes a specified bit on the selected device and port.
def IOWriteBit(handle, devType, devPort, whichDevice, whichExpPort, bitNum, bitValue):
    CHK(daq.daqIOWriteBit(handle, devType, devPort, whichDevice, whichExpPort, bitNum, ct.c_bool(bitValue)))

#daqIORead reads the specified port on the selected device
def IORead(handle, devType, devPort, whichDevice, whichExpPort):
    value_ct = wt.DWORD()
    CHK(daq.daqIORead(handle, devType, devPort, whichDevice, whichExpPort, ct.byref(value_ct)))
    return value_ct.value

#daqIOReadBit reads a specified bit on the selected device and port.
def IOReadBit(handle, devType, devPort, whichDevice, whichExpPort, bitNum):
    bitvalue_ct = ct.c_bool(bitValue)
    CHK(daqIOReadBit(handle, devType, devPort, whichDevice, whichExpPort, bitNum, ct.byref(bitvalue_ct)))
    return bitvalue_ct.value

def Open(deviceName):
    """daqOpen opens an installed device for operation

    Inputs
    ------
    deviceName

    Returns
    -------
    handle
    """
    daq.daqOpen.restype = ct.c_int32
    #daq.daqOpen.argtypes(ct.c_char_p)

    pdeviceName = ct.c_char_p(deviceName)
    handle = daq.daqOpen(pdeviceName)
    return handle


def Close(handle):
    """daqOpen opens an installed device for operation

    Inputs
    ------
    deviceName

    Returns
    -------
    handle
    """
    daq.daqClose.restype = ct.c_int32
    #daq.daqClose.argtypes(ct.c_int32)

    CHK(daq.daqClose(handle))


def DacSetOutputMode(handle, deviceType, chan, outputMode):
    CHK(daq.daqDacSetOutputMode(handle, deviceType, chan, outputMode))


def DacWt(handle, deviceTypes, chan, dataVal):
    CHK(daq.daqDacWt(handle, deviceTypes, chan, dataVal))

def DacWtMany(handle, deviceTypes, chans, dataVals):
#     daqDacWtMany(handle, [DddtLocal,DddtLocal,DddtLocal,DddtLocal],[0,1,2,3],[100,1000,10000,20000],4)
    #if chans = [0,1,2,3]  then convert to WORD Array by  (ct.c_uint16 * len(chans))(*chans)
    channelcount = len(chans)
    chans_i32vec       = (ct.c_uint32 * len(chans)) (* chans)
    deviceTypes_i32vec = (ct.c_int32  * len(deviceTypes)) (* deviceTypes)
    dataVals_ui16vec   = (ct.c_uint16 * len(dataVals)) (* dataVals)
    CHK(daq.daqDacWtMany(handle, ct.byref(deviceTypes_i32vec), ct.byref(chans_i32vec), ct.byref(dataVals_ui16vec), channelcount))

def DacTransferGetStat(handle, deviceType, chan):

    active = wt.DWORD()
    retCount = wt.DWORD()

    #daq.daqDacTransferGetStat.argtypes = (ct.cint32, ct.cint32, wt.DWORD, ct.POINTER(wt.DWORD), ct.POINTER(wt.DWORD))    

    CHK(daq.daqDacTransferGetStat(handle, deviceType, chan, ct.byref(active), ct.byref(retCount)))

    return active.value, retCount.value

def DacWaveSetMode(handle, deviceType, chan, mode, updateCount):
    CHK(daq.daqDacWaveSetMode(handle, deviceType, chan, mode, updateCount))

def DacWaveSetClockSource(handle, deviceType, chan, clockSource):
    CHK(daq.daqDacWaveSetClockSource(handle, deviceType, chan, clockSource))

def DacWaveSetFreq(handle, deviceType, chan, freq):
    CHK(daq.daqDacWaveSetFreq(handle, deviceType, chan, ct.c_float(freq)))

def DacWaveGetFreq(handle, deviceType, chan):
    freq = ct.c_float(0)
    CHK(daq.daqDacWaveGetFreq(handle, deviceType, chan, ct.byref(freq)))
    return freq.value

def DacWaveSetBuffer(handle, deviceType, chan, buf, scanCount,transferMask):
    CHK_ARRAY( buf.flatten(), scanCount, np.uint16 )
    CHK(daq.daqDacWaveSetBuffer(handle, deviceType, chan, buf.ctypes.data, scanCount,transferMask))

def DacWaveSetUserWave(handle, deviceType, chan):
    CHK(daq.daqDacWaveSetUserWave(handle, deviceType, chan))

def DacWaveSetTrig(handle, deviceType, chan, triggerSource, rising):
    CHK(daq.daqDacWaveSetTrig(handle, deviceType, chan, triggerSource, ct.c_bool(rising)))

def DacWaveArm(handle, deviceType):
    CHK(daq.daqDacWaveArm(handle, deviceType))

def DacWaveDisarm(handle, deviceType):
    CHK(daq.daqDacWaveDisarm(handle, deviceType))

def DacTransferStart(handle, deviceType, chan):
     CHK(daq.daqDacTransferStart(handle, deviceType, chan))

def DacTransferStop(handle, deviceType, chan):
     CHK(daq.daqDacTransferStop(handle, deviceType, chan))

def DacWaveSoftTrig(handle, deviceType, chan):
     CHK(daq.daqDacWaveSoftTrig(handle, deviceType, chan))

def DacWaveSetPredefWave(handle, deviceType, chan, waveType, amplitude, offset, dutyCycle, phaseShift):
    CHK(daq.daqDacWaveSetPredefWave(handle, deviceType, chan, waveType, amplitude, offset, dutyCycle, phaseShift))