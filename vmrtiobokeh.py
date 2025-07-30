# Read and plot live data from one VMR using the tio tcp proxy interface
# Bokeh plotting version, use bokeh serve --show vmrtiobokey.py to start

# How fast will this go?  200 Hzseems to work OK
# TODO - try streaming, the simple scheme loses some data points

SR = 200 # VMR Sampling rate
WINDOWSEC = 5 # Seconds of data in plot window
BUFFERSIZE = int(SR*WINDOWSEC)
UPDATEMILLISEC = 100
DATASIZE = (UPDATEMILLISEC/1000)*SR # Points of data to get at a time

import argparse
import numpy as np
import tldevice
from bokeh.plotting import figure, curdoc
from bokeh.driving import linear
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.layouts import column
from scipy.fft import fft

# import ptvsd # For server-side debugging

def getTimebase(dev): # Get VMR timebase clock rate
  timebase_id = dev._tio.protocol.streamInfo['stream_timebase_id']
  return dev._tio.protocol.timebases[timebase_id]['timebase_Fs']

def vmrdevice(url,sr): # Open VMR port and set requested sampling rate
  dev = tldevice.Device(url)
  assert(dev.dev.name()=='VMR')
  timebasehz = getTimebase(dev)
  decimation = int(timebasehz/sr)
  dev.vector.data.decimation(decimation)
  return dev

def getVMRdata(dev,DATASIZE): 
    # Get new data from the sensor
    d = dev.data(DATASIZE+1,timeaxis=False, flush=False)
    return np.array(d) # np.transpose(d) - this was a tio version change?  Working as of 6/11/2024

parser = argparse.ArgumentParser(prog='vectorMonitor', description='Vector Field Graphing Monitor')
parser.add_argument("url", nargs='?', default='tcp://localhost', help='URL: tcp://localhost')
args = parser.parse_args()
dev = vmrdevice(args.url,SR)

Dx = np.linspace(0,0,BUFFERSIZE) # Create the data array that will be plotted
Dy = np.linspace(0,0,BUFFERSIZE)
Dz = np.linspace(0,0,BUFFERSIZE)
Dt = np.linspace(0,0,BUFFERSIZE)

signal_source = ColumnDataSource(data=dict(t=[], mx=[], my=[], mz=[])) # t,mx,my,mz
signal_plot = figure(width=1000, height=500, title="Signal")
signal_plot.background_fill_color = "white" # "#eaeaea"
signal_plot.line(x="t", y="mx", line_color="red", source=signal_source, legend_label="Mx")
signal_plot.line(x="t", y="my", line_color="green", source=signal_source, legend_label="My")
signal_plot.line(x="t", y="mz", line_color="blue", source=signal_source, legend_label="Mz")
signal_plot.legend.location = "top_left"
signal_plot.legend.click_policy="hide"
signal_plot.y_range.only_visible = True

spectrum_source = ColumnDataSource(data=dict(f=[], px=[], py=[], pz=[])) # f,px,py,pz
spectrum_plot = figure(width=1000, height=500, title="Power spectrum (WARNING: unscaled FFT)",x_axis_type="log",y_axis_type="log")
spectrum_plot.background_fill_color = "white" #  "#eaeaea"
spectrum_plot.line(x="f", y="px", line_color="red", source=spectrum_source, legend_label="Mx")
spectrum_plot.line(x="f", y="py", line_color="green", source=spectrum_source, legend_label="My")
spectrum_plot.line(x="f", y="pz", line_color="blue", source=spectrum_source, legend_label="Mz")
spectrum_plot.legend.location = "top_left"
spectrum_plot.legend.click_policy="hide"
spectrum_plot.y_range.only_visible = True

@linear()
def update(step):
    global i,dev,Dt,Dx,Dy,Dz,Dtf, BUFFERSIZE, DATASIZE, signal_source,spectrum_source
    
    mx,my,mz,ax,ay,az,gx,gy,gz,bar,temp = getVMRdata(dev,DATASIZE)
    
    # # attach to VS Code debugger if this script was run with BOKEH_VS_DEBUG=true
    # # (place this just before the code you're interested in)
    # if os.environ['BOKEH_VS_DEBUG'] == 'true':
    #     # 5678 is the default attach port in the VS Code debug configurations
    #     print('Waiting for debugger attach')
    #     ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
    #     ptvsd.wait_for_attach()

    Dx = np.append(Dx, mx)              
    Dy = np.append(Dy, my)              
    Dz = np.append(Dz, mz)  
    Dt = np.arange(len(Dx))/SR # Assumes no dropped points
    
    if len(Dx) > BUFFERSIZE: # If we have filled the data buffer, keep only the end
        Dx = Dx[-BUFFERSIZE:]
        Dy = Dy[-BUFFERSIZE:]
        Dz = Dz[-BUFFERSIZE:]
        Dt = Dt[-BUFFERSIZE:]

    # # BEST PRACTICE --- update .data in one ste
    sig = dict(t=Dt,mx=Dx,my=Dy,mz=Dz) # new data dict
    N = len(Dx)
    lsd = dict(f=10*(np.arange(int(len(Dx)/2))/(SR/4)),px = abs(fft(Dx))[:int(N/2)], py = abs(fft(Dy))[:int(N/2)], pz = abs(fft(Dz))[:int(N/2)])
    
    signal_source.data = sig
    spectrum_source.data = lsd

curdoc().add_root(column(signal_plot,spectrum_plot,sizing_mode="stretch_both"))

# Add a periodic callback to be run every ?? milliseconds
curdoc().add_periodic_callback(update, UPDATEMILLISEC)

curdoc().title = "VMR"
# show(p)
    
