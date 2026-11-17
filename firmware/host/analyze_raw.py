#!/usr/bin/env python3
"""Screening statistics for a raw bit capture (the .bin from capture_raw.py).  NOT a proof of randomness.

Main purpose: catch the failure the hardware is most likely to have - a deterministic or periodic bit
pattern (beat phase of two clocks) that still has a balanced histogram.
"""
import sys,math,numpy as np
from math import erfc,sqrt
b=np.fromfile(sys.argv[1],dtype=np.uint8)
bits=np.unpackbits(b).astype(np.int8); n=len(bits)
if n<1000: sys.exit('need at least 1000 bits, have %d'%n)
print('bits: %d'%n)
p=bits.mean(); z=(bits.sum()-n/2)/(math.sqrt(n)/2)
print('ones fraction %.5f   monobit z %.2f (|z|>3 suspicious)'%(p,z))
# runs
runs=1+int(np.count_nonzero(bits[1:]!=bits[:-1])); er=2*n*p*(1-p)+1; vr=2*n*p*(1-p)*(2*n*p*(1-p)-1)/(n-1) if n>1 else 1
print('runs %d  expected %.1f  z %.2f'%(runs,er,(runs-er)/math.sqrt(vr) if vr>0 else float('nan')))
# longest run
ch=np.flatnonzero(np.diff(bits))+1; ln=np.diff(np.concatenate(([0],ch,[n]))); print('longest run %d  (expected about %.0f for random)'%(ln.max(),math.log2(n)))
# overlapping 2-bit patterns
pair=bits[:-1]*2+bits[1:]; cnt=np.bincount(pair,minlength=4); print('2-bit patterns 00 01 10 11:',cnt.tolist(),' (expected %.0f each)'%((n-1)/4))
chi=((cnt-(n-1)/4)**2/((n-1)/4)).sum(); print('  chi-square(3 dof) %.2f  (about 7.8 is the 5%% point)'%chi)
# autocorrelation by FFT, lags 1..L
x=(2*bits-1).astype(float); x-=x.mean(); L=min(8192,n//4)
f=np.fft.rfft(x,2*n); ac=np.fft.irfft(f*np.conj(f))[:L+1]/ac0 if (ac0:=np.sum(x*x))>0 else None
lim=4/math.sqrt(n); bad=[k for k in range(1,L+1) if abs(ac[k])>lim]
print('bit autocorrelation lags 1..%d: max |r| %.4f at lag %d   (4-sigma limit %.4f, lags over limit: %d)'%(L,np.abs(ac[1:]).max(),1+int(np.abs(ac[1:]).argmax()),lim,len(bad)))
print('  lags 1..8:',' '.join('%+.4f'%ac[k] for k in range(1,9)))
# byte histogram
if len(b)>=2560:
    h=np.bincount(b,minlength=256); e=len(b)/256; c2=((h-e)**2/e).sum()
    try:
        from scipy.stats import chi2; pv=chi2.sf(c2,255); print('byte chi-square %.1f (255 dof)  p=%.4f'%(c2,pv))
    except Exception: print('byte chi-square %.1f (255 dof, about 293 is the 5%% point)'%c2)
# spectral flatness check on blocks of 4096 bits (periodic patterns show as lines)
if n>=8192:
    m=4096; k=n//m; X=x[:k*m].reshape(k,m); P=(np.abs(np.fft.rfft(X,axis=1))**2).mean(axis=0)[1:]; P/=P.mean()
    print('average power spectrum (4096-bit blocks): max/mean %.1f  (random data gives about 1-2 after averaging; large values mean spectral lines, i.e. a periodic pattern; %d bins)'%(P.max(),len(P)))
# most-common-value min-entropy estimate for bits (screening bound, 99%% upper confidence)
pm=max(p,1-p); pu=min(1,pm+2.576*math.sqrt(pm*(1-pm)/n)); print('min-entropy per bit, most-common-value estimate: %.4f (upper bound on p: %.4f)'%(-math.log2(pu),pu))
# Von Neumann on the host
pr=bits[:n//2*2].reshape(-1,2); d=pr[:,0]!=pr[:,1]; vn=pr[d,0]; print('Von Neumann: %d pairs, %d kept (%.1f%%), kept ones fraction %.4f'%(len(pr),int(d.sum()),100*d.mean(),vn.mean() if len(vn) else float('nan')))
print('A balanced histogram and passing these tests do NOT prove unpredictability; see the notes.')
