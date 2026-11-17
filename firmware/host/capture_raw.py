#!/usr/bin/env python3
"""Capture the Si5351 TRNG firmware output (ASCII hex lines) from the PICAXE serial port.

  capture_raw.py /dev/ttyUSB0 --bits 100000 --out run1        (live capture, 4800 baud default)
  capture_raw.py --replay saved.log --out test                (parse a saved log, no hardware)

Writes <out>.bin (raw bytes, MSB first = firmware bit order), <out>.log (every line with a host timestamp).
Line types: I: info, E: error, D: raw bytes, C: conditioned bytes, S: status.
The measured rate is from host arrival times of the data lines; it includes the firmware's own pauses.
"""
import argparse,sys,time,re
ap=argparse.ArgumentParser()
ap.add_argument('port',nargs='?'); ap.add_argument('--baud',type=int,default=4800)
ap.add_argument('--bits',type=int,default=100000); ap.add_argument('--out',default='capture')
ap.add_argument('--replay'); a=ap.parse_args()
import os
if a.replay and os.path.abspath(a.replay)==os.path.abspath(a.out+'.log'): sys.exit('--replay file would be overwritten by the output log; choose a different --out')
if a.replay: src=open(a.replay)
else:
    import serial
    if not a.port: sys.exit('give a serial port or --replay')
    ser=serial.Serial(a.port,a.baud,timeout=2,dsrdtr=False,rtscts=False)
    def gen():
        while True:
            l=ser.readline()
            if l: yield l.decode('ascii','replace')
    src=gen()
hexline=re.compile(r'^([DC]):([0-9A-Fa-f]*)$')
data=bytearray(); log=open(a.out+'.log','w'); first=last=None; kinds=set(); bad=0
t0=time.time()
try:
    for raw in src:
        line=raw.strip(); now=time.time()
        if not line: continue
        log.write('%.3f %s\n'%(now-t0,line)); log.flush()
        m=hexline.match(line)
        if m:
            h=m.group(2)
            if len(h)%2 or len(h)>32: bad+=1; print('bad data line (length %d)'%len(h)); continue
            kinds.add(m.group(1)); data+=bytes.fromhex(h)
            if first is None: first=(now,len(data)*8)
            last=(now,len(data)*8)
            if len(data)*8>=a.bits: break
        else:
            print(line)
            if line.startswith('E:'): print('firmware reported an error; stopping'); break
except KeyboardInterrupt: pass
open(a.out+'.bin','wb').write(data)
print('bytes %d (%d bits), bad lines %d, types %s'%(len(data),len(data)*8,bad,''.join(sorted(kinds))))
if first and last and last[0]>first[0]:
    print('measured rate %.2f bits/s (host arrival times; first to last data line)'%((last[1]-first[1])/(last[0]-first[0])))
