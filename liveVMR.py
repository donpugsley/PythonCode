#!/usr/bin/env python3
# Works OK at 2 Hz 0.5 tick, works but cant keep up at 10 Hz 0.1
# Configure rate on VMR to match tick, otherwise errors
 
import time, random
import math
import collections
import matplotlib.pyplot
import matplotlib.animation
import matplotlib.ticker as mtick
import tldevice
import argparse

def getTimebase(dev):
  timebase_id = dev._tio.protocol.streamInfo['stream_timebase_id']
  print(f"Stream 0: timebase ID: {timebase_id}"
       +f", components: {dev._tio.protocol.streamInfo['stream_total_components']}"
       +f", period: {dev._tio.protocol.streamInfo['stream_period']} uS")
  print(f"Timebase {timebase_id} rate: {dev._tio.protocol.timebases[timebase_id]['timebase_Fs']:.3f} Hz"
       +f" ({dev._tio.protocol.timebases[timebase_id]['timebase_period_num_us']}/{dev._tio.protocol.timebases[timebase_id]['timebase_period_denom_us']} µs)"
       +f", epoch: {dev._tio.protocol.timebases[timebase_id]['timebase_epoch']}"
       +f", stability: {dev._tio.protocol.timebases[timebase_id]['timebase_stability_ppb']:.0f} ppb")
  for i, column in enumerate(dev._tio.protocol.streams):
    print(f"Component {i}: {column['source_name']} ({column['source_title']}), period {column['source_period']}, {column['stream_Fs']:.3f} Hz")
  return dev._tio.protocol.timebases[timebase_id]['timebase_Fs']

class RealtimePlot:
  def __init__(self, dev, windowLength, tickTime, xlabel="Time (s)", ylabel="Field (nT)"):
    
    self.dev = dev
    self.windowLength = windowLength
    self.tickTime = tickTime
    queueLength = int(windowLength)
    
    print(f'Setup: VMR sampling at {SR}, Window {WINDOWSEC}, GetSec {GETSEC}, frame every {FRAMEINTERVALMS} ms, Queue {queueLength} points')

    # Initialize data arrays as Double Ended Queue (d e que), which
    # auto-discards objects when max length is reached
    self.data_t = collections.deque(maxlen=queueLength)
    self.data_x = collections.deque(maxlen=queueLength)
    self.data_y = collections.deque(maxlen=queueLength)
    self.data_z = collections.deque(maxlen=queueLength)

    matplotlib.rcParams['font.family'] = 'Palatino'
    self.fig = matplotlib.pyplot.figure(constrained_layout=True)
    gs = matplotlib.gridspec.GridSpec(3,1, figure=self.fig, hspace= 0.08, wspace=0.1)
    self.ax3 = self.fig.add_subplot(gs[2]) 
    self.ax1 = self.fig.add_subplot(gs[0], sharex=self.ax3)
    self.ax2 = self.fig.add_subplot(gs[1], sharex=self.ax3)
    matplotlib.pyplot.setp(self.ax1.get_xticklabels(), visible=False)
    matplotlib.pyplot.setp(self.ax2.get_xticklabels(), visible=False)
    self.ax3.xaxis.set_major_formatter(mtick.FormatStrFormatter('%5.1f')) 
 
    self.ax1line = matplotlib.lines.Line2D([],[], color='black', linewidth = 0.5)
    self.ax2line = matplotlib.lines.Line2D([],[], color='black', linewidth = 0.5)
    self.ax3line = matplotlib.lines.Line2D([],[], color='black', linewidth = 0.5)
    self.ax1.add_line(self.ax1line)
    self.ax2.add_line(self.ax2line)
    self.ax3.add_line(self.ax3line)

    self.ax1.set_xlabel(xlabel)
    self.ax1.set_ylabel('X '+ylabel)
    self.ax2.set_ylabel('Y '+ylabel)
    self.ax3.set_ylabel('Z '+ylabel)

    self.animate()

    # Call self.animate repeatedly, 10 ms interval between frames
    self.ani = matplotlib.animation.FuncAnimation(self.fig, self.animate, interval=FRAMEINTERVALMS)
    matplotlib.pyplot.show()

  def animate(self,*args):

    # Get new data from the sensor
    data = self.dev.vector(duration=self.tickTime, timeaxis=True, flush=False)

    if len(self.data_t)==self.data_t.maxlen:
      print('Full')
    else:
      print(len(self.data_t))

    self.data_t.extend(data[0]) # Add new data to the queue
    # print(self.data_t)
    self.data_x.extend(data[1])
    self.data_y.extend(data[2])
    self.data_z.extend(data[3])

    self.ax1line.set_data(self.data_t, self.data_x)
    self.ax2line.set_data(self.data_t, self.data_y)
    self.ax3line.set_data(self.data_t, self.data_z)

    # Set left and right plot limits, handling either single or multiple values
    #self.ax1.set_xlim(min(self.data_t[0]), max(self.data_t[0]))
    self.ax1.relim()
    self.ax1.autoscale_view()
    #self.ax2.set_xlim(self.data_t[0], self.data_t[-1])
    self.ax2.relim()
    self.ax2.autoscale_view()
    #self.ax3.set_xlim(self.data_t[0], self.data_t[-1])
    self.ax3.relim()
    self.ax3.autoscale_view()
    return self.ax1line, self.ax2line, self.ax3line,

parser = argparse.ArgumentParser(prog='vectorMonitor', 
                            description='Vector Field Graphing Monitor')
parser.add_argument("url", 
              nargs='?', 
              default='tcp://localhost',
              help='URL: tcp://localhost')
args = parser.parse_args()

dev = tldevice.Device(args.url)
assert(dev.dev.name()=='VMR')

timebase = getTimebase(dev)

# At 400 things are not quite right... window is ~20 seconds long?  200 Seems OK
SR = 200 #VMR Sampling rate
WINDOWSEC = 10 # Seconds of data in plot window
GETSEC = 1.0 # Get this many seconds of data at a time
FRAMEINTERVALMS = 1.0/GETSEC # milliseconds between draw events

decimation = int(timebase/SR)
print(f'Setting sampling rate ({timebase}/{SR} = {decimation})')
dev.vector.data.decimation(decimation)
print(f'Sampling rate set to {dev.data.rate()}')

# Check sampling rate
# data = dev.vector(duration=1,flush=False)
# N = len(data)   
# print(f'Observed data rate is {N} Hz')

RealtimePlot(dev,WINDOWSEC*SR,GETSEC)
