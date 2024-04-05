from pylive import live_plotter
import numpy as np
import tldevicesync

tio = tldevicesync.DeviceSync()

streams = []
streams += [tio.vmr0.vector]
streams += [tio.vmr1.vector]
streams += [tio.vmr2.vector]
ss = tldevicesync.SyncStream(streams)

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
    line1 = live_plotter(x_vec,y_vec,line1) # Draw
    x_vec = np.append(x_vec[1:],0.0) # Drop the first point
    y_vec = np.append(y_vec[1:],0.0)
