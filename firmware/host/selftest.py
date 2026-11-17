#!/usr/bin/env python3
"""Generates logs in the firmware's exact line format from known data and runs capture/analysis on them."""
import random,subprocess,sys,os,numpy as np
random.seed(5)
def mk(bits,name,prefix='D'):
    by=[sum(bits[i+j]<<(7-j) for j in range(8)) for i in range(0,len(bits)-7,8)]
    with open(name,'w') as f:
        f.write('I:SI5351TRNG fw1 08M2 mode=RAW\nI:chip 0 ok\nI:chip 1 ok\nI:clocks A=8.000 B=8.001 MHz nominal, run\n')
        for i in range(0,len(by),16):
            f.write('%s:%s\n'%(prefix,''.join('%02X'%v for v in by[i:i+16])))
            if (i//16)%16==15: f.write('S:r=%d a=0 d=0 o=%d t=%d\n'%((i+16)*8,i+16,(i+16)//12))
    return by
n=100000
good=[random.getrandbits(1) for _ in range(n)]
per=[(1 if (i%7)<3 else 0) for i in range(n)]            # balanced-looking periodic pattern
bias=[1 if random.random()<0.55 else 0 for _ in range(n)]
for nm,b in (('good',good),('periodic',per),('bias55',bias)):
    by=mk(b,nm+'.in')
    subprocess.run([sys.executable,'capture_raw.py','--replay',nm+'.in','--bits',str(n),'--out',nm],check=True,stdout=subprocess.DEVNULL)
    assert open(nm+'.bin','rb').read()==bytes(by), nm+' round-trip mismatch'
    print('=== %s: capture round trip OK'%nm)
    subprocess.run([sys.executable,'analyze_raw.py',nm+'.bin'])
