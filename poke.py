import tldevice
tio = tldevice.Device("tcp://localhost")

for row in tio.data.stream_iter():
    rowstring = "\t".join(map(str,row))+"\n"
    print(rowstring)
    
