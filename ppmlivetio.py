# Read and plot live data from one PPM using the tio tcp proxy interface
# and pyqtgraph, with a Qt Designer GUI

SR = 480 # PPM Sampling rate - set this using tio-rpc from the command line
TIMERTICKSPERSECOND = 20
DATASIZE = round(SR/TIMERTICKSPERSECOND) # Amount of data to grab at each tick
WINDOWSEC = 5    # Seconds of data in plot window
BUFFERSIZE = int(SR*WINDOWSEC)
WELCHFACTOR = 6 # Number of segments for Welch PSD

import sys
import argparse
import numpy as np
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from scipy import signal
import tldevice

def ppmdevice(url): # Open VMR port and set requested sampling rate
  dev = tldevice.Device(url)
  assert(dev.dev.name()=='PPM')
  return dev

parser = argparse.ArgumentParser(prog='PPM-Monitor', description='Scalar Field Graphing Monitor')
parser.add_argument("url", nargs='?', default='tcp://localhost', help='URL: tcp://localhost')
args = parser.parse_args()
dev = ppmdevice(args.url)

# GUI control variables
removeMean, clearPlotFlag = [False]*2
# showX, showY, showZ = [True]*3
showTF = True

# Load the QT Designer .ui file 
uiclass, baseclass = pg.Qt.loadUiType("PPM.ui")
class MainWindow(uiclass, baseclass):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.checkBoxDC.stateChanged.connect(self.DC_state_changed)
        # self.checkBoxTF.stateChanged.connect(self.TF_state_changed)
        # self.checkBoxX.stateChanged.connect(self.X_state_changed)
        # self.checkBoxY.stateChanged.connect(self.Y_state_changed)
        # self.checkBoxZ.stateChanged.connect(self.Z_state_changed)
     
    def DC_state_changed(self, int):
        global removeMean
        removeMean = not self.checkBoxDC.isChecked()
    # def TF_state_changed(self, int):
    #     global showTF, clearPlotFlag
    #     showTF = self.checkBoxTF.isChecked()
    #     clearPlotFlag = True
    # def X_state_changed(self, int):
    #     global showX, clearPlotFlag
    #     showX = self.checkBoxX.isChecked()
    #     clearPlotFlag = True
    # def Y_state_changed(self, int):
    #     global showY, clearPlotFlag
    #     showY = self.checkBoxY.isChecked()
    #     clearPlotFlag = True
    # def Z_state_changed(self, int):
    #     global showZ, clearPlotFlag
    #     showZ = self.checkBoxZ.isChecked()
    #     clearPlotFlag = True

 # Create the main window and set up the UI
app = QApplication(sys.argv)
window = MainWindow() 
w = window.mywidget # This is the promoted GraphicsLayoutWidget used for fast plottting

# Create a modeless dialog box for text data display
dialog = QDialog(None)
dialog.setWindowTitle("Twinleaf PPM Data (latest, mean, peak to peak)")
MinValue = QLabel()
MaxValue = QLabel()
MeanValue = QLabel()
layout = QVBoxLayout(dialog)
layout.addWidget(MinValue)
MinValue.setFont(QFont('Arial', 26))
layout.addWidget(MaxValue)
MaxValue.setFont(QFont('Arial', 26))
layout.addWidget(MeanValue)
MeanValue.setFont(QFont('Arial', 26))
dialog.setLayout(layout)

tplot = w.addPlot(row=0,col=0) 
tplot.showGrid(True,True)
ctf = tplot.plot(pen="y") # Add an empty curve to the timeseries plot; set the curve data later

splot = w.addPlot(row=1,col=0) 
splot.showGrid(True,True)
splot.setLogMode(True,True)
stf = splot.plot(pen="y") # Add an empty curve to the plot; set the curve data later

Dtf = np.linspace(0,0,BUFFERSIZE) # Create the data array that will be plotted
Dq = np.linspace(0,0,BUFFERSIZE)

# Get some PPM data points
def getPPMdata(dev): 
    # Get new data from the sensor
    d = dev.data(DATASIZE,timeaxis=False, flush=False)
    return np.array(d) # np.transpose(d) - this was a tio version change?  Working as of 6/11/2024

# Callback function - read data and update the plot when called
def update():
    global dev,Dtf,Dq, BUFFERSIZE, tplot,splot,clearPlotFlag,ctf,stf, MinValue,MaxValue,MeanValue,dialog

    D = getPPMdata(dev)

    tf = D[:][0] 
    quality = D[:][1]
    Dtf = np.append(Dtf, tf)
    Dq = np.append(Dq, quality)
    
    if len(Dtf) > BUFFERSIZE: # If we have filled the data buffer, keep only the end
        Dtf = Dtf[-BUFFERSIZE:]
        Dq = Dq[-BUFFERSIZE:]

    if clearPlotFlag:
        tplot.clear()
        splot.clear()        
        ctf = tplot.plot(pen="y")
        stf = splot.plot(pen="y")
        clearPlotFlag = False

    # Time series plot
    if removeMean:
        if showTF:
            ctf.setData(Dtf-np.mean(Dtf))    
    else:
        if showTF:
            ctf.setData(Dtf)    
    
    # Spectrum
    if showTF:       
        # ftf, Ptf = signal.periodogram(Dtf,SR,detrend='constant',scaling='density')
        ftf, Ptf = signal.welch(Dtf,SR,nperseg=np.floor(BUFFERSIZE/WELCHFACTOR),detrend='constant',scaling='density')
        stf.setData(ftf,np.sqrt(Ptf))

    MinValue.setText(f'Min: {np.min(Dtf):.0f} nT\t Max: {np.max(Dtf):.0f} nT\t Mean: {np.mean(Dtf):.0f} nT')
    MaxValue.setText(f'Minimum Signal Quality: {np.min(Dq)}')
    dialog.show()


# Set an update and process Qt events until the window is closed.
timer = pg.QtCore.QTimer() # Create a timer
timer.timeout.connect(update) # Call the update routine when the timer ticks
timer.start(TIMERTICKSPERSECOND) # Timer event ticks 20 times a second
window.show()
app.exec() # Fall into event loop... exits when main window is closed
dialog.close()