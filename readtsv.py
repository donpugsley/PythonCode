# try out different Read and plot...

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# TODO - pass in fn as argument
# fn = '../testvmr.dat1.tsv'
if len(sys.argv) > 1:
    fn = sys.argv[1]
else:
    fn = '../hotel-floor-more1.tsv'
    
# Maybe change backend behavior
# mpl.use('QtAgg')

data = pd.read_csv(fn,delimiter='\t')

def threeplot(t,x,y,z,units,title):
    fig, ax = plt.subplots()
    mx = np.mean(x)
    my = np.mean(y)
    mz = np.mean(z)
    ax.plot(t, x-mx,label=f'X {mx:.0f} DC')
    ax.plot(t, y-my,label=f'Y {my:.0f} DC')
    ax.plot(t, z-mz,label=f'Z {mz:.0f} DC')

    ax.legend()
    ax.set_title(title)
    ax.set_ylabel(units)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    plt.tick_params(axis='both', which='major', labelsize=12)
    # plt.axis([0, 1100, 0, 1100000])
    plt.grid(visible='true')
    plt.show()

threeplot(data['t'],data['/1/vector.x'],data['/1/vector.y'],
          data['/1/vector.z'],'nT','Twinleaf VMR Mag')

pass
# seaborn:
# iloc()
# figsize()
# lineplot()
# tick_params()
# tight_layout()
# show()
#
