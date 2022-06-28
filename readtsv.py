# try out different Read and plot...

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Maybe change backend behavior
# mpl.use('QtAgg')

# TODO - pass in fn as argument
fn = '../testvmr.dat1.tsv'
data = pd.read_csv(fn,delimiter='\t')


t = data['t']
x = data['/1/vector.x']
y = data['/1/vector.y']
z = data['/1/vector.z']
title = 'VMR'
units = 'nT'

def threeplot(x,y,z,units,title):
    fig, ax = plt.subplots()
    ax.plot(t, x-np.mean(x))
    ax.plot(t, y-np.mean(y))
    ax.plot(t, z-np.mean(z))
    ax.set_title(title)
    ax.set_ylabel(units)
    ax.set_xlabel('Time')
    
    plt.show()

threeplot(x,y,z,units,title)
pass

# seaborn:
# iloc()
# figsize()
# lineplot()
# tick_params()
# tight_layout()
# show()
#

