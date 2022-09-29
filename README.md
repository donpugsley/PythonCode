Contents:

This is all a work in progress, part of my efforts to improve my Python skills.

Bash command to extract a list of all RPC commands from a device:
NRPC=0x`tio-rpc -r /dev/ttyACM0 rpc.list | head -1 | awk '{ print $1 }'` && for ((i=0;i<$NRPC;i++)) do echo -e "\nRPC $i  " && tio-rpc -r /dev/ttyACM0 rpc.listinfo u16:$i | xxd -r -p ; done > ../SYNC4-RPC.txt

After removing problematic commands like reboot, we can create an rpcwalk script to read out all the available configuration values.  

rpcwalk - bash script to read out values from SYNC4/VMR 
RPCWALK.txt - output from rpcwalk

initializeVMR - bash script to get VMR back to a known state

poke.py - a start at a python-based rpcwalk 

readtsv.py - read magnetic data created by tio-record/tio-logparse
plotters.py - analysis plots for magnetic data





