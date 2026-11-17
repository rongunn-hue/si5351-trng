#!/usr/bin/env python3
"""Si5351 register values for the TRNG firmware (AN619 rev 0.8 equations) with an independent decode check.

PLLA = XTAL x (a + b/c)           P1 = 128a + floor(128 b/c) - 512 ; P2 = 128b - c floor(128 b/c) ; P3 = c
MS0  = PLLA / (a + b/c)           same encoding, output divider R0 = 1
Registers: PLLA (MSNA) 26..33, MS0 42..49.  Byte layout (AN619 regs 26-33 / 42-49):
  +0 P3[15:8]  +1 P3[7:0]  +2 (R_DIV<<4 | DIVBY4<<2 | P1[17:16])  (reg 28 has only P1[17:16] in bits 1:0)
  +3 P1[15:8]  +4 P1[7:0]  +5 (P3[19:16]<<4 | P2[19:16])  +6 P2[15:8]  +7 P2[7:0]
"""
import sys
from fractions import Fraction
XTAL=int(sys.argv[1]) if len(sys.argv)>1 else 25_000_000   # printed on the Si5351 board: 25 MHz
def enc(a,b,c):
    assert 0<=b<c<=1048575 and c>=1
    fl=(128*b)//c
    P1=128*a+fl-512; P2=128*b-c*fl; P3=c
    assert 0<=P1<2**18 and 0<=P2<2**20 and 0<=P3<2**20
    return P1,P2,P3
def regbytes(a,b,c,rdiv=0):
    P1,P2,P3=enc(a,b,c)
    return [(P3>>8)&255,P3&255,(rdiv<<4)|((P1>>16)&3),(P1>>8)&255,P1&255,(((P3>>16)&15)<<4)|((P2>>16)&15),(P2>>8)&255,P2&255]
def decode(bs):
    P3=(bs[0]<<8)|bs[1]|((bs[5]>>4)<<16); P1=((bs[2]&3)<<16)|(bs[3]<<8)|bs[4]; P2=((bs[5]&15)<<16)|(bs[6]<<8)|bs[7]
    # invert: ratio = (P1+512)/128 + P2/(128 P3)
    return Fraction(P1+512,128)+Fraction(P2,128*P3)
def solve(target,vco):
    r=Fraction(vco,target); a=r.numerator//r.denominator; f=r-a
    b,c=f.numerator,f.denominator
    assert c<=1048575, 'denominator too big'
    return a,b,c
vco_mult=32; VCO=XTAL*vco_mult
assert 600e6<=VCO<=900e6
pll=regbytes(vco_mult,0,1)
print('XTAL %d Hz, PLLA multiplier %d -> VCO %d Hz (valid 600-900 MHz)'%(XTAL,vco_mult,VCO))
print('PLLA regs 26..33:',' '.join('%02X'%x for x in pll),' decoded mult =',decode(pll))
for name,f in (('A',8_000_000),('B',8_001_000)):
    a,b,c=solve(f,VCO); bs=regbytes(a,b,c); d=decode(bs)
    out=Fraction(VCO)/d
    print('Si5351 %s: target %d Hz  MS0 = %d + %d/%d  (divider must be >= 8 and < 2048)'%(name,f,a,b,c))
    print('   MS0 regs 42..49:',' '.join('%02X'%x for x in bs),'  BASIC: hi2cout 42,(%s)'%','.join('$%02X'%x for x in bs))
    print('   decoded divider %s -> output %s Hz (error %s Hz, assuming an ideal crystal)'%(d,float(out),float(out-f)))
    assert out==f
print('PLLA BASIC: hi2cout 26,(%s)'%','.join('$%02X'%x for x in pll))
