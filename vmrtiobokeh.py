# Read and plot live data from one VMR using the tio tcp proxy interface
# Bokeh plotting version, use bokeh serve --show vmrtiobokey.py to start
#
# To Dos:
# Interactive control of waterfall.ts high value in this line:
# this.cmap = new LinearColorMapper({palette: this.model.palette, low: 0, high: 1e4})
#
# Control to toggle removal of DC from time series
#
# Better tio acquisition - precise time, no drops 
# 
# A quit button on the GUI?
#   
# DEBUG flag
DEBUG = False
HEIGHT = 200
WIDTH = 200

SR = 200 # VMR Sampling rate; 200 works well
WINDOWSEC = 5.12 # Seconds of data in plot window
BUFFERSIZE = 1024; # int(SR*WINDOWSEC)
UPDATEMILLISEC = 100
DATASIZE = (UPDATEMILLISEC/1000)*SR # Points of data to get at a time

import argparse
import numpy as np
import tldevice
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import row, column, grid, layout
from bokeh.models import CustomJS, MultiChoice, CheckboxButtonGroup, PreText
from scipy.fft import fft
from scipy.signal import periodogram, welch
from waterfall import WaterfallRenderer

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

Dx = np.empty(shape=[0]) # linspace(0,0,1) # Create the data arrays that will be plotted
Dy = np.empty(shape=[0]) # linspace(0,0,1)
Dz = np.empty(shape=[0]) # linspace(0,0,1)
Dt = np.empty(shape=[0]) # linspace(0,0,1)

signal_source = ColumnDataSource(data=dict(t=[], mx=[], my=[], mz=[])) # t,mx,my,mz
signal_plot = figure(title="Time Series", min_width=WIDTH, min_height=HEIGHT)
signal_plot.sizing_mode = 'scale_both'
signal_plot.background_fill_color = "white" # "#eaeaea"
tsx = signal_plot.line(x="t", y="mx", line_color="red", source=signal_source, legend_label="Mx")
tsy = signal_plot.line(x="t", y="my", line_color="green", source=signal_source, legend_label="My")
tsz = signal_plot.line(x="t", y="mz", line_color="blue", source=signal_source, legend_label="Mz")
signal_plot.legend.location = "top_left"
signal_plot.legend.click_policy="hide"
signal_plot.y_range.only_visible = True

spectrum_source = ColumnDataSource(data=dict(f=[], px=[], py=[], pz=[])) # f,px,py,pz
spectrum_plot = figure(title="Linear Spectral Density",x_axis_type="log",y_axis_type="log", min_width=WIDTH, min_height=HEIGHT)
spectrum_plot.sizing_mode = 'scale_both'
spectrum_plot.background_fill_color = "white" #  "#eaeaea"
spx = spectrum_plot.line(x="f", y="px", line_color="red", source=spectrum_source, legend_label="Mx")
spy = spectrum_plot.line(x="f", y="py", line_color="green", source=spectrum_source, legend_label="My")
spz = spectrum_plot.line(x="f", y="pz", line_color="blue", source=spectrum_source, legend_label="Mz")
spectrum_plot.legend.location = "top_left"
spectrum_plot.legend.click_policy="hide"
spectrum_plot.y_range.only_visible = True

MAX_FREQ_KHZ = (SR/2.0)*0.001
NUM_GRAMS = 300
GRAM_LENGTH = 86
TILE_WIDTH = HEIGHT

PALETTE = ['#081d58', '#253494', '#225ea8', '#1d91c0', '#41b6c4', '#7fcdbb', '#c7e9b4', '#edf8b1', '#ffffd9']
PLOTARGS = dict(tools="", toolbar_location=None, outline_line_color='#595959')

waterfall_renderer = WaterfallRenderer(palette=PALETTE, num_grams=NUM_GRAMS,gram_length=GRAM_LENGTH, tile_width=TILE_WIDTH)
waterfall_plot = figure(width=3*HEIGHT, height=HEIGHT,x_range=[0, NUM_GRAMS], y_range=[0, MAX_FREQ_KHZ], **PLOTARGS)
waterfall_plot.grid.grid_line_color = None
waterfall_plot.background_fill_color = "#024768"
waterfall_plot.renderers.append(waterfall_renderer)

removeDC = False

def update():
    # global i,dev,Dt,Dx,Dy,Dz,Dtf, BUFFERSIZE, DATASIZE, signal_source,spectrum_source
    global dev, Dt,Dx,Dy,Dz, BUFFERSIZE, DATASIZE, signal_source,spectrum_source, removeDC
    
    vmx,vmy,vmz,ax,ay,az,gx,gy,gz,bar,temp = getVMRdata(dev,DATASIZE)
    
    # # attach to VS Code debugger if this script was run with BOKEH_VS_DEBUG=true
    # # (place this just before the code you're interested in)
    # if os.environ['BOKEH_VS_DEBUG'] == 'true':
    #     # 5678 is the default attach port in the VS Code debug configurations
    #     print('Waiting for debugger attach')
    #     ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
    #     ptvsd.wait_for_attach()

    if removeDC:
       vmx = vmx - np.mean(vmx)
       vmy = vmy - np.mean(vmy)
       vmz = vmz - np.mean(vmz)

    Dx = np.append(Dx, vmx)              
    Dy = np.append(Dy, vmy)              
    Dz = np.append(Dz, vmz)  
    Dt = np.arange(len(Dx))/SR # Assumes no dropped points
    
    if len(Dx) > BUFFERSIZE: # If we have filled the data buffer, keep only the end
        Dx = Dx[-BUFFERSIZE:]
        Dy = Dy[-BUFFERSIZE:]
        Dz = Dz[-BUFFERSIZE:]
        Dt = Dt[-BUFFERSIZE:]

    # # BEST PRACTICE --- update .data in one ste
    sig = dict(t=Dt,mx=Dx,my=Dy,mz=Dz) # new data dict
    f, px = welch(Dx,SR,window='hann',nperseg=BUFFERSIZE/6,detrend='constant') 
    f, py = welch(Dy,SR,window='hann',nperseg=BUFFERSIZE/6,detrend='constant') 
    f, pz = welch(Dz,SR,window='hann',nperseg=BUFFERSIZE/6,detrend='constant') 

    lsd = dict(f=f,px=px,py=py,pz=pz)

    # DEBUG
    # print(f"mx({len(vmx)}, my({len(vmy)}), mz({len(vmz)}) -> Dx({len(Dx)})")
    # print(f"px({len(px)}, py({len(py)}), pz({len(pz)}, f({len(f)}))")


    # seems to be a problem with Array property, using List for now
    wd = px.tolist()
    wd[0] = wd[1] # avoid the lowest frequency point
    waterfall_renderer.latest = wd 
    waterfall_plot.y_range.end = SR/2

    signal_source.data = sig
    spectrum_source.data = lsd

def cbbg(options,initialstate):
  checkbox_button_group = CheckboxButtonGroup(labels=options, active=initialstate,button_type='primary') 
  checkbox_button_group.js_on_event("button_click", CustomJS(args=dict(btn=checkbox_button_group), code="""
      console.log('checkbox_button_group: active=' + btn.active, this.toString())
  """))
  return checkbox_button_group
    
def cbbg_callback(attr,old,new):
    global removeDC,tsx,tsy,tsz,spx,spy,spz
    # print('CBBG new is ', new)
    # last_clicked_ID = list(set(old)^set(new))[0] # [0] since there will always be just one different element at a time
    # print ('last button clicked: ', last_clicked_ID)
    tsx.visible = (0 in new)
    tsy.visible = (1 in new)
    tsz.visible = (2 in new)
    spx.visible = (0 in new)
    spy.visible = (1 in new)
    spz.visible = (2 in new)
    removeDC = (3 in new)
        
    
# curdoc().theme = 'dark_minimal'
choice = cbbg(['X On','Y On','Z On','DC Removed'],[0,1,2]) # DC removal is not active at startup
choicelabel = PreText(text='Toggle Controls: ') # ,width=WIDTH,height=HEIGHT)
choice.on_change("active", cbbg_callback)

# curdoc().add_root(column(children=[signal_plot,spectrum_plot],sizing_mode="stretch_both"))
curdoc().add_root(column(row(choicelabel,choice),signal_plot, spectrum_plot,waterfall_plot,sizing_mode="stretch_both"))

# Add a periodic callback to be run every ?? milliseconds
curdoc().add_periodic_callback(update, UPDATEMILLISEC)

curdoc().title = "VMR"

# For debuggering only!!!
# while True:
#    update()

    
