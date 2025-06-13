This is all a work in progress, part of my efforts to improve my Python skills.

This code is focused on practical uses of Twinleaf magnetometers, particularly the VMR triax and the PPM scalar.  Sync4 devices are also mentioned here but I think twinleaf has discontinued them due to parts availability issues.


# Exploring RPC commands available (a little risky, lots of commands have unexpected side effects)

rpcwalk - bash script to read out values from SYNC4/VMR 
RPCWALK.txt - output from rpcwalk

Bash command to extract a list of all RPC commands from a device:
NRPC=0x\`tio-rpc -r /dev/ttyACM0 rpc.list | head -1 | awk '{ print $1 }'\` && for ((i=0;i<$NRPC;i++)) do echo -e "\nRPC $i  " && tio-rpc -r /dev/ttyACM0 rpc.listinfo u16:$i | xxd -r -p ; done > ../SYNC4-RPC.txt

After removing problematic commands like reboot, we can create an rpcwalk script to read out all the available configuration values.  

initializeVMR - bash script to get a VMR back to a known state

# Python support routines

readtsv.py - read magnetic data created by Twinleaf tio-record/tio-logparse

plotters.py - analysis plots for magnetic data

# Python standalone programs

poke.py - a start at a python-based rpcwalk 

livevmr.py - my first try with matplotlib, works but very slow.

vmrlivetio.py - realtime PyQtGraph GUI plot of time series and spectrum for VMR

ppmlivetio.py - realtime PyQtGraph GUI plot of time series and spectrum for PPM




