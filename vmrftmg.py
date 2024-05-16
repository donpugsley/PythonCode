from pylive import live_plotter,live_plotter_xy
import numpy as np
import tldevicesync

def getTimebase(dev):
  timebase_id = dev.vmr0._tio.protocol.streamInfo['stream_timebase_id']
  tb0 = dev.vmr0._tio.protocol.timebases[timebase_id]['timebase_Fs']
  timebase_id = dev.vmr1._tio.protocol.streamInfo['stream_timebase_id']
  tb1 = dev.vmr1._tio.protocol.timebases[timebase_id]['timebase_Fs']
  timebase_id = dev.vmr2._tio.protocol.streamInfo['stream_timebase_id']
  tb2 = dev.vmr2._tio.protocol.timebases[timebase_id]['timebase_Fs']

  if tb0 != tb1 | tb0 != tb2:
    print('Please fix VMR timebases, they are not all the same {tb0}, {tb1}, {tb2}')
    exit
  return tb1

# At 100 this doesn't keep up... 20 Seems OK
SR = 20 # VMR Sampling rate
WINDOWSEC = 10 # Seconds of data in plot window
GETSEC = 1.0 # Get this many seconds of data at a time
FRAMEINTERVALMS = 1.0/GETSEC # milliseconds between draw events

tio = tldevicesync.DeviceSync()

streams = []
streams += [tio.vmr0.vector]
streams += [tio.vmr1.vector]
streams += [tio.vmr2.vector]
ss = tldevicesync.SyncStream(streams)

# Set sampling rate on all VMRs
timebasehz = getTimebase(tio)
decimation = int(timebasehz/SR)
print(f'Setting sampling rate (decimation = {timebasehz}/{SR} = {decimation})')
tio.vmr0.vector.data.decimation(decimation)
tio.vmr1.vector.data.decimation(decimation)
tio.vmr2.vector.data.decimation(decimation)
print(f'Sampling rate set to {tio.vmr2.data.rate()}')

# Choose one axis for plotting
k = 1; 
print('Using ', ss.columnnames()[k])

size = 100 # number of points to show

# Preload arrays to be drawn
x_vec = []
y_vec = []
for i,d in enumerate(ss.iter()):
    x_vec = np.append(x_vec,d[0])
    y_vec = np.append(y_vec,d[k])
    if i > size:
        break

# Drop the first point
x_vec = np.append(x_vec[1:],0.0)
y_vec = np.append(y_vec[1:],0.0)

line1 = [] # Tell pylive to initialize on first call
for d in ss.iter():
    newtime = d[0]
    newvalue = d[k]

    x_vec[-1] = newtime # Add new point to the end
    y_vec[-1] = newvalue 
    line1 = live_plotter_xy(x_vec,y_vec,line1) # Draw
    x_vec = np.append(x_vec[1:],0.0) # Drop the first point
    y_vec = np.append(y_vec[1:],0.0)
