from kisch import *
# ---------------- box symbols: pins exactly as labelled on the purchased boards (see board photos) ----------------
BOXES['PICAXE_08M2']=('U','PICAXE-08M2',
  [('7','C.0_SER_OUT','bidirectional'),('2','C.5_SER_IN','input')],
  [('5','C.2_SDA','bidirectional'),('6','C.1_SCL','bidirectional'),('4','C.3_IN','input')],
  [('1','+V','power_in')],[('3','C.4_CLK2_OUT','bidirectional'),('8','0V','power_in')],35.56,False,7)
tca_edge1=['VIN','GND','SDA','SCL','RST','A0','A1','A2','SD0','SC0','SD1','SC1']
tca_edge2=['SD2','SC2','SD3','SC3','SD4','SC4','SD5','SC5','SD6','SC6','SD7','SC7']
ty=lambda n:'power_in' if n in('VIN','GND') else ('bidirectional' if n=='SDA' else ('input' if n in('SCL','RST','A0','A1','A2') else 'passive'))
BOXES['TCA9548A_MODULE']=('U','TCA9548A MODULE HW-617',[(n,n,ty(n)) for n in tca_edge1],[(n,n,'passive') for n in tca_edge2],[],[],25.4,True,12,5.08)
BOXES['SI5351_MODULE']=('U','Si5351 MODULE',
  [('0','CLK0_(0)','output'),('1','CLK1_(1)','output'),('2','CLK2_(2)','output')],
  [('SDA','SDA','bidirectional'),('SCL','SCL','input')],
  [('VIN','VIN','power_in')],[('GND','GND','power_in')],25.4,True,5)
BOXES['CONN_POWER']=('J','POWER 5 V',[],[('1','+5V','power_out'),('2','0V','power_out')],[],[],17.78,False,2)
BOXES['CONN_DOWNLOAD']=('J','DOWNLOAD',[],[('1','SER_OUT','passive'),('2','SER_IN','passive'),('3','0V','passive')],[],[],17.78,False,3)
BOXES['CONN_DIAG']=('J','DIAG SERIAL',[],[('1','TX','passive'),('2','0V','passive')],[],[],17.78,False,2)
BOXES['HCT74']=('U','74HCT74',[None,None,None,('5','Q1','output'),('12','D2','input'),('9','Q2','output'),('11','CLK2','input'),('6','/Q1','output'),('8','/Q2','output')],[None,None,None,('2','D1','input'),('3','CLK1','input')],[('4','/PRE1','input'),('10','/PRE2','input'),('1','/CLR1','input'),('13','/CLR2','input'),('14','VCC','power_in')],[('7','GND','power_in')],25.4,False,9)

S=Sch('Si5351 TRNG',paper='A4')
S.meta(['Boxes are purchased modules, pins as printed. Q1 -> D2; C.4 clocks FF2; C.3 reads Q2.','Hi2c master C.2 SDA, C.1 SCL -> TCA9548A; ch0 -> A -> D1; ch1 -> B -> CLK1','Si5351 / PICAXE-08M2 TRNG V6, 5 V. All serial through the download socket (C.0, C.5).'],'11/26')
p=S.pin
def add(lib,name,ref,val,x,y,**k): return S.add(lib,name,ref,val,x,y,**k)
def align(ref,pin,y,unit=None):
    for I in S.inst:
        if I['ref']==ref and (unit is None or I['unit']==unit):
            cur=p(ref,pin,unit)[1]; I['y']=round(I['y']+(y-cur),3); return
def alignx(ref,pin,x,unit=None):
    for I in S.inst:
        if I['ref']==ref and (unit is None or I['unit']==unit):
            cur=p(ref,pin,unit)[0]; I['x']=round(I['x']+(x-cur),3); return
Yf=147.32
# ---------- placement ----------
add('filter','HCT74','U5','74HCT74',147.32,Yf,rp=(8,13),vp=(8,15.5)); align('U5','9',Yf)      # both flip-flops, one box
add('filter','SI5351_MODULE','U3','Si5351 MODULE A',200.66,127.0,rp=(3,-9),vp=(3,9))
add('filter','SI5351_MODULE','U4','Si5351 MODULE B',200.66,172.72,rp=(3,-9),vp=(3,9))
add('filter','TCA9548A_MODULE','U2','TCA9548A MODULE HW-617',264.16,68.58,rp=(-12.7,-31.5),vp=(-12.7,-29.5))
alignx('U2','VIN',248.92); align('U2','VIN',55.88)
add('filter','PICAXE_08M2','U1','PICAXE-08M2',86.36,150.0,rp=(-17.78,-15.5),vp=(-17.78,-13.2))
align('U1','4',p('U5','9')[1])
alignx('U1','4',106.68)
align('U3','0',124.46); align('U4','0',170.18)
add('filter','CONN_POWER','J1','POWER 5 V',30.48,Yf-28,rp=(-8.89,-5.5),vp=(-8.89,-3.5))
yC0=p('U1','7')[1]; yC5=p('U1','2')[1]
add('filter','CONN_DOWNLOAD','J2','DOWNLOAD',30.48,yC0+6,rp=(-8.89,-8.5),vp=(-8.89,-6.5)); align('J2','1',yC0)
add('Device','R','R1','22k',49.53,yC5+3.81,rot=0,left=True)
add('Device','R','R2','10k',59.69,yC5+3.81,rot=0)
add('Device','C','C1','100nF',96.52,Yf-20.5,rot=0)
# ---------- power ----------
S.power('+5V',*p('J1','1')); S.power('GND',*p('J1','2'))
pv=p('U1','1'); P5=(pv[0],pv[1]-15.24)
S.wire(pv,P5); S.power('+5V',*P5)
S.add('Device','C','C1','100nF',106.68,P5[1]+3.81,rot=0) if False else None
c1t=p('C1','1'); S.wire(P5,c1t); S.power('GND',*p('C1','2'))
S.power('GND',*p('U1','8'))
# ---------- download / serial socket (PICAXE manual 1 minimum circuit); sertxd uses C.0, serrxd/serin uses C.5 ----------
S.wire(p('J2','1'),p('U1','7'))
j=p('J2','2'); r1t=p('R1','1'); r1b=p('R1','2'); y0=j[1]; Nx=r1b[0]+5.08
S.wire(j,r1t)                                  # SER_IN -> R1 (stands beside the signal row, rule A8)
S.wire(r1b,(Nx,r1b[1]),(Nx,y0))                # R1 exit jogs back up to the row
S.wire((Nx,y0),p('U1','2'))                    # row to C.5; R2 hangs from this row
S.power('GND',*p('R2','2')); S.power('GND',*p('J2','3'))
# ---------- C.4 : capture clock to FF2 CLK2 ----------
yb=p('U1','3')[1]+13.97; c4=p('U1','3'); xg=p('U5','11')[0]-10.16
S.wire(c4,(c4[0],yb),(xg,yb),(xg,p('U5','11')[1]),p('U5','11'))
# ---------- I2C: PICAXE -> TCA9548A ----------
t=lambda n:p('U2',n)
c2=p('U1','5'); c1=p('U1','6')
S.wire(c2,(111.76,c2[1]),(111.76,t('SDA')[1]),t('SDA'))
S.wire(c1,(116.84,c1[1]),(116.84,t('SCL')[1]),t('SCL'))
# ---------- TCA9548A ties ----------
x0=t('VIN')[0]-5.08
S.wire(t('VIN'),(x0,t('VIN')[1])); S.power('+5V',x0,t('VIN')[1])
S.wire(t('GND'),(x0,t('GND')[1])); S.power('GND',x0,t('GND')[1])
S.wire(t('RST'),(x0,t('RST')[1])); S.power('+5V',x0,t('RST')[1]); S.inst[-1]['hidev']=True      # arrow only: its label would sit on the SCL wire
for n in ('A0','A1','A2'): S.wire(t(n),(x0,t(n)[1]))
S.wire((x0,t('A0')[1]),(x0,t('A2')[1])); S.power('GND',x0,t('A2')[1])
for n in tca_edge2: S.nc(*t(n))
# ---------- TCA channels -> Si5351 modules ----------
S.wire(t('SD0'),(226.06,t('SD0')[1]),(226.06,p('U3','SDA')[1]),p('U3','SDA'))
S.wire(t('SC0'),(231.14,t('SC0')[1]),(231.14,p('U3','SCL')[1]),p('U3','SCL'))
S.wire(t('SD1'),(238.76,t('SD1')[1]),(238.76,p('U4','SDA')[1]),p('U4','SDA'))
S.wire(t('SC1'),(243.84,t('SC1')[1]),(243.84,p('U4','SCL')[1]),p('U4','SCL'))
# ---------- Si5351 module power / NC ----------
for r in ('U3','U4'):
    v=p(r,'VIN'); S.wire(v,(v[0],v[1]-5.08)); S.power('+5V',v[0],v[1]-5.08)
    g=p(r,'GND'); S.wire(g,(g[0],g[1]+5.08)); S.power('GND',g[0],g[1]+5.08)
    S.nc(*p(r,'1')); S.nc(*p(r,'2'))
# ---------- CLK0 A -> D1 ; CLK0 B -> CLK1 ----------
a=p('U3','0'); d1=p('U5','2'); S.wire(a,(175.26,a[1]),(175.26,d1[1]),d1)
b=p('U4','0'); k1=p('U5','3'); S.wire(b,(170.18,b[1]),(170.18,k1[1]),k1)
# ---------- flip-flops ----------
q1=p('U5','5'); d2=p('U5','12'); xu=q1[0]-5.08
S.wire(q1,(xu,q1[1]),(xu,d2[1]),d2)                        # Q1 -> D2 (short U-turn on the left)
S.wire(p('U5','9'),p('U1','4'))                            # Q2 -> C.3
S.nc(*p('U5','6')); S.nc(*p('U5','8'))
# five pins tied to +5 V along the top bus; C2 across VCC / GND
tops=[p('U5',n) for n in ('4','10','1','13','14')]; yb5=tops[0][1]-13.97
for t in tops: S.wire(t,(t[0],yb5))
S.wire((tops[0][0],yb5),(tops[-1][0],yb5)); mid=tops[2]; S.power('+5V',mid[0],yb5)
add('Device','C','C2','100nF',tops[-1][0]+15.24,yb5+3.81,rot=0)
c2t=p('C2','1'); S.wire((tops[-1][0],yb5),(c2t[0],yb5),c2t) if abs(c2t[1]-yb5)<0.01 else print('C2 top y',c2t[1],'bus',yb5)
S.power('GND',*p('U5','7')); S.power('GND',*p('C2','2'))
S.center(148.5,90); S._centered=True
S.write('trng_v6.kicad_sch')
print('written')
