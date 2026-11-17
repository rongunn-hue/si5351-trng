# Compares the exported netlist of trng_v2.kicad_sch with the baseline netlist taken from the specification and the board photos.
import xml.etree.ElementTree as ET,sys
t=ET.parse(sys.argv[1] if len(sys.argv)>1 else 'trng_v2_netlist.xml'); nets={}
for n in t.getroot().iter('net'):
    nets[n.get('name')]=sorted(f"{x.get('ref')}.{x.get('pin')}" for x in n.iter('node'))
exp={'+5V':['C1.1','C2.1','J1.1','U1.1','U2.RST','U2.VIN','U3.VIN','U4.VIN','U5.1','U5.10','U5.13','U5.14','U5.4'],
 '0V':['C1.2','C2.2','J1.2','J2.3','R2.2','U1.8','U2.A0','U2.A1','U2.A2','U2.GND','U3.GND','U4.GND','U5.7'],
 'SDA':['U1.5','U2.SDA'],'SCL':['U1.6','U2.SCL'],'CH0_SDA':['U2.SD0','U3.SDA'],'CH0_SCL':['U2.SC0','U3.SCL'],
 'CH1_SDA':['U2.SD1','U4.SDA'],'CH1_SCL':['U2.SC1','U4.SCL'],'CLK_A':['U3.0','U5.2'],'CLK_B':['U4.0','U5.3'],
 'Q1':['U5.12','U5.5'],'CAPTURE C.4 to CLK2':['U1.3','U5.11'],'SER_OUT C.0':['J2.1','U1.7'],'Q2':['U1.4','U5.9'],
 'SER_IN to R1':['J2.2','R1.1'],'PICAXE C.5 node':['R1.2','R2.1','U1.2']}
got={frozenset(v) for v in nets.values() if len(v)>1}
bad=0
for k,v in exp.items():
    if frozenset(v) not in got: print('MISSING/DIFFERENT',k,v); bad+=1
for e in got-{frozenset(v) for v in exp.values()}: print('UNEXPECTED',sorted(e)); bad+=1
print('%d nets checked: %s'%(len(exp),'MATCH' if not bad else 'MISMATCH'))
