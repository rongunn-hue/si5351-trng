# Minimal hand-written KiCad schematic writer (new code for the "blind" filter schematics; no layout/routing logic).
import re,uuid,math
LIB='/usr/share/kicad/symbols/'
def _extract(libfile,name):
    t=open(LIB+libfile+'.kicad_sym').read(); i=t.index('(symbol "%s"'%name)
    d=0
    for j in range(i,len(t)):
        if t[j]=='(': d+=1
        elif t[j]==')':
            d-=1
            if d==0: return t[i:j+1]
def _pin(typ,x,y,a,ln,name,num,hide=''):
    return '(pin %s line (at %g %g %d) (length %g)\n        (name "%s" (effects (font (size 1.27 1.27))))\n        (number "%s" (effects (font (size 1.27 1.27))))\n      )'%(typ,x,y,a,ln,name,num)
def _opamp_text(name,both=True):
    head='(symbol "%s" (pin_names (offset 0.127)) (in_bom yes) (on_board yes)\n    (property "Reference" "U" (id 0) (at 0 6.35 0) (effects (font (size 1.27 1.27)) (justify left)))\n    (property "Value" "%s" (id 1) (at 0 3.81 0) (effects (font (size 1.27 1.27)) (justify left)))\n    (property "Footprint" "" (id 2) (at 1.27 1.27 0) (effects (font (size 1.27 1.27)) hide))\n    (property "Datasheet" "" (id 3) (at 3.81 3.81 0) (effects (font (size 1.27 1.27)) hide))\n'%(name,name)
    tri='(polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)) (stroke (width 0.254) (type default) (color 0 0 0 0)) (fill (type background)))'
    u=''
    for n,(o,m,p) in ((1,('1','2','3')),(2,('7','6','5'))):
        u+='    (symbol "%s_%d_1"\n      %s\n      %s\n      %s\n      %s\n      %s\n    )\n'%(name,n,tri,_pin('output',7.62,0,180,2.54,'~',o),_pin('input',-7.62,-2.54,0,2.54,'-',m),_pin('input',-7.62,2.54,0,2.54,'+',p),(_pin('power_in',-2.54,7.62,270,3.81,'V+','8')+'\n      '+_pin('power_in',-2.54,-7.62,90,3.81,'V-','4')) if (both or n==1) else '')
    return head+u+'  )'
def _arrow(symname,net,down):
    t=_extract('power','+12V').replace('+12V',net)
    t=t.replace('(symbol "%s"'%net,'(symbol "%s"'%symname,1).replace('(symbol "%s_'%net,'(symbol "%s_'%symname)
    if down:
        t=re.sub(r'\(xy (-?[\d.]+) (-?[\d.]+)\)',lambda m:'(xy %s %s)'%(m.group(1),('%g'%(-float(m.group(2))))),t)
        t=t.replace('(at 0 3.556 0)','(at 0 -3.556 0)').replace('(at 0 -3.81 0)','(at 0 3.81 0)').replace('(at 0 0 90) (length 0) hide','(at 0 0 270) (length 0) hide')
    return t

# ---- generic box symbols for modules/boards (pins exactly as labelled on the real board) ----
BOXES={}
def _box(name):
    ref,val,left,right,top,bottom,w,hidenum,rows,pitch=(BOXES[name]+(2.54,))[:10] if len(BOXES[name])==9 else BOXES[name]
    m=max(len(left),len(right),rows,1); T=pitch*((m-1)//2); topy=T+pitch/2; boty=T-pitch*(m-1)-pitch/2
    head='(symbol "%s" %s(pin_names (offset 0.762)) (in_bom yes) (on_board yes)\n    (property "Reference" "%s" (id 0) (at %g %g 0) (effects (font (size 1.27 1.27)) (justify left)))\n    (property "Value" "%s" (id 1) (at %g %g 0) (effects (font (size 1.27 1.27)) (justify left)))\n    (property "Footprint" "" (id 2) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n    (property "Datasheet" "" (id 3) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'%(name,'(pin_numbers hide) ' if hidenum else '',ref,-w/2,topy+2.54+(6.35 if top else 0),val,-w/2,boty-2.54-(6.35 if bottom else 0))
    body='(rectangle (start %g %g) (end %g %g) (stroke (width 0.254) (type default) (color 0 0 0 0)) (fill (type background)))'%(-w/2,topy,w/2,boty)
    pins=''
    for i,it in enumerate(left):
        if it is None: continue
        num,pn,typ=it; pins+='\n      '+_pin(typ,-w/2-2.54,T-pitch*i,0,2.54,pn,num)
    for i,it in enumerate(right):
        if it is None: continue
        num,pn,typ=it; pins+='\n      '+_pin(typ,w/2+2.54,T-pitch*i,180,2.54,pn,num)
    for L,y,a in ((top,topy+2.54,270),(bottom,boty-2.54,90)):
        n=len(L)
        for i,(num,pn,typ) in enumerate(L):
            x=round((i-(n-1)/2)*5.08/2.54)*2.54 if n>1 else 0
            pins+='\n      '+_pin(typ,x,y,a,2.54,pn,num)
    return head+'    (symbol "%s_1_1"\n      %s%s\n    )\n  )'%(name,body,pins)
def _custom(name):
    if name in BOXES: return _box(name)
    if name.startswith('UP_'): return _arrow(name,name[3:],False)
    if name.startswith('DN_'): return _arrow(name,name[3:],True)
    if name=='LM1458': return _opamp_text('LM1458',both=False)
    if name=='LM1458_2P': return _opamp_text('LM1458_2P',both=True)
    if name=='GND_DOWN':
        t=_extract('power','-12V').replace('-12V','GND_DOWN'); return t.replace('(property "Value" "GND_DOWN"','(property "Value" "GND"').replace('(name "GND_DOWN"','(name "GND"')
class Sym:
    def __init__(s,lib,name):
        s.lib,s.name=lib,name; s.text=_custom(name) if lib=='filter' else _extract(lib,name); s.pins={}
        for m in re.finditer(r'\(symbol "%s_(\d+)_\d+"'%re.escape(name),s.text):
            u=int(m.group(1)); a=m.end(); d=1; b=a
            while d: 
                b+=1; d+= (s.text[b]=='(')-(s.text[b]==')')
            blk=s.text[a:b]
            for pm in re.finditer(r'\(pin (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]+)"',blk,re.S):
                s.pins[(u,pm.group(6))]=(float(pm.group(3)),float(pm.group(4)),pm.group(1))
    def gbox(s):
        t=re.sub(r'\(pin .*?\(number "[^"]+"[^)]*\)[^)]*\)\s*\)','',s.text,flags=re.S)
        xy=[(float(a),float(b)) for a,b in re.findall(r'\((?:xy|start|end) ([-\d.]+) ([-\d.]+)\)',t)]
        if not xy: return None
        return (min(p[0] for p in xy),max(p[0] for p in xy),min(p[1] for p in xy),max(p[1] for p in xy))
    def lib_text(s):
        return s.text.replace('(symbol "%s"'%s.name,'(symbol "%s:%s"'%(s.lib,s.name),1)
def U(): return str(uuid.uuid4())
class Sch:
    def __init__(s,title,paper='A4'):
        s.title=title; s.paper=paper; s.syms={}; s.inst=[]; s.wires=[]; s.labels=[]; s.ncs=[]; s.texts=[]; s.pw=0
    def lib(s,lib,name):
        k=lib+':'+name
        if k not in s.syms: s.syms[k]=Sym(lib,name)
        return s.syms[k]
    def add(s,lib,name,ref,val,x,y,rot=0,mirror=False,unit=1,show=True,fp='',rp=None,vp=None,left=False):
        sy=s.lib(lib,name)
        if rp is None: rp=(0,-3.2) if rot in (90,270) else (2.54,-1.27)
        if vp is None: vp=(0,3.2) if rot in (90,270) else (2.54,1.27)
        vang=None
        if lib=='Device' and name=='R':   # standing rule: resistor Value INSIDE the body, along it; Reference 0.5 mm off the body
            horiz=rot in (90,270); vp=(0,0); vang=90
            rp=(0,-2.15) if horiz else (1.016+0.5,0)
        if left and lib=='Device' and name in ('R','C','C_Polarized') and rot in (0,180):   # labels on the left of an upright part (right-justified)
            rp=(-(1.516),0) if name=='R' else (-2.54,-1.27)
            if name!='R': vp=(-2.54,1.27)
        s.inst.append(dict(sy=sy,ref=ref,val=val,x=x,y=y,rot=rot,mir=mirror,unit=unit,show=show,fp=fp,rp=rp,vp=vp,vang=vang,jr=bool((left and lib=='Device' and name in ('R','C','C_Polarized') and rot in (0,180)) or (lib=='Device' and name=='R' and rot==180 and not left)))); return ref
    def pin(s,ref,num,unit=None):
        for I in s.inst:
            key=(I['unit'],num) if (I['unit'],num) in I['sy'].pins else (0,num)
            if I['ref']==ref and (unit is None or I['unit']==unit) and key in I['sy'].pins:
                px,py,_=I['sy'].pins[key]
                if I['mir']: px=-px
                r=math.radians(I['rot']); rx=px*math.cos(r)-py*math.sin(r); ry=px*math.sin(r)+py*math.cos(r)
                return (round(I['x']+rx,3),round(I['y']-ry,3))
        raise KeyError((ref,num))
    def power(s,name,x,y,rot=0,val=None,down=False):
        s.pw+=1; net=val or name
        if down: lib,sym='filter','DN_'+net
        elif name in ('+18V','VIN_POS'): lib,sym='filter','UP_'+net
        else: lib,sym='power',name
        return s.add(lib,sym,'#PWR%02d'%s.pw,net,x,y,rot,show=False,rp=(0,0),vp=(0,5.4 if down else -4.8))
    def wire(s,*pts):
        for a,b in zip(pts,pts[1:]):
            if a!=b: s.wires.append((tuple(a),tuple(b)))
    def label(s,name,x,y,ang=0,just='left'): s.labels.append((name,x,y,ang,just))
    def nc(s,x,y): s.ncs.append((x,y))
    def meta(s,desc,date,company='Ethelbert Design'): s.desc=desc; s.date=date; s.company=company
    def text(s,t,x,y,size=1.8): s.texts.append((t,x,y,size))
    def _split(s):
        pts=set()
        for I in s.inst:
            for (u,n) in I['sy'].pins:
                if u==I['unit'] or u==0: pts.add(s.pin(I['ref'],n,I['unit']))
        for l in s.labels: pts.add((l[1],l[2]))
        W=list(s.wires); out=[]
        changed=True
        while changed:
            changed=False; out=[]
            for (a,b) in W:
                cut=None
                for p in pts|{q for w in W for q in w}:
                    if p in (a,b): continue
                    if a[0]==b[0]==p[0] and min(a[1],b[1])<p[1]<max(a[1],b[1]): cut=p
                    elif a[1]==b[1]==p[1] and min(a[0],b[0])<p[0]<max(a[0],b[0]): cut=p
                    if cut: break
                if cut: out+=[(a,cut),(cut,b)]; changed=True
                else: out.append((a,b))
            W=out
        s.wires=list(dict.fromkeys(out)); return pts
    def junctions(s,pts):
        deg={}
        for a,b in s.wires:
            for p in (a,b): deg[p]=deg.get(p,0)+1
        for p in pts: deg[p]=deg.get(p,0)+1
        return [p for p,d in deg.items() if d>=3]
    def compact(s,mx=10.0,my=9.0,keep=4.0,wm=2.0,verbose=True):
        """Delete EMPTY bands (no symbol box, no crossing perpendicular wire) and slide the rest inward. Pure geometry: pins, wires and junctions
        move together, shifts are multiples of 2.54 mm, so connectivity and the 'wire ends exactly on pin' property are unchanged."""
        def gaps(iv,lo,hi):
            iv=sorted(iv); out=[]; cur=lo
            for a,b in iv:
                if a>cur: out.append((cur,a))
                cur=max(cur,b)
            return out
        ix=[(I['x']-mx,I['x']+mx) for I in s.inst]; iy=[(I['y']-my,I['y']+my) for I in s.inst]
        for (a,b) in s.wires:
            if abs(a[0]-b[0])<1e-9: ix.append((a[0]-wm,a[0]+wm))      # vertical wire blocks x-bands
            if abs(a[1]-b[1])<1e-9: iy.append((a[1]-wm,a[1]+wm))      # horizontal wire blocks y-bands
        xlo=min(a for a,b in ix); xhi=max(b for a,b in ix); ylo=min(a for a,b in iy); yhi=max(b for a,b in iy)
        def plan(iv,lo,hi):
            P=[]
            for a,b in gaps(iv,lo,hi):
                r=int(((b-a)-keep)/2.54)*2.54
                if r>0: P.append(((a+b)/2,r))
            return P
        PX=plan(ix,xlo,xhi); PY=plan(iy,ylo,yhi)
        fx=lambda v: round(v-sum(r for m_,r in PX if v>=m_),3); fy=lambda v: round(v-sum(r for m_,r in PY if v>=m_),3)
        for I in s.inst: I['x']=fx(I['x']); I['y']=fy(I['y'])
        s.wires=[((fx(a[0]),fy(a[1])),(fx(b[0]),fy(b[1]))) for a,b in s.wires]
        s.labels=[(n,fx(x),fy(y),g,j) for n,x,y,g,j in s.labels]; s.ncs=[(fx(x),fy(y)) for x,y in s.ncs]; s.texts=[(t,fx(x),fy(y),z) for t,x,y,z in s.texts]
        if verbose: print('compact: removed x %.1f mm in %d bands, y %.1f mm in %d bands'%(sum(r for _,r in PX),len(PX),sum(r for _,r in PY),len(PY)))
    def center(s,cx=148.5,cy=100.0):
        # centre everything in the usable sheet area (frame minus title block); shift snapped to the 2.54 mm grid
        xs=[];ys=[]
        for a,b in s.wires: xs+=[a[0],b[0]]; ys+=[a[1],b[1]]
        for I in s.inst:
            if not I['ref'].startswith('#'): xs.append(I['x']); ys.append(I['y'])
        for t in s.texts: xs.append(t[1]); ys.append(t[2])
        dx=round((cx-(min(xs)+max(xs))/2)/2.54)*2.54; dy=round((cy-(min(ys)+max(ys))/2)/2.54)*2.54
        for I in s.inst: I['x']=round(I['x']+dx,3); I['y']=round(I['y']+dy,3)
        s.wires=[((round(a[0]+dx,3),round(a[1]+dy,3)),(round(b[0]+dx,3),round(b[1]+dy,3))) for a,b in s.wires]
        s.labels=[(n,round(x+dx,3),round(y+dy,3),g,j) for n,x,y,g,j in s.labels]
        s.ncs=[(round(x+dx,3),round(y+dy,3)) for x,y in s.ncs]
        s.texts=[(t,round(x+dx,3),round(y+dy,3),z) for t,x,y,z in s.texts]
    def check_bodies(s):
        """General guard: no wire may pass through any part body. 2-pin parts: body = segment between its pins.
        Other parts: pin bounding box shrunk by 0.6 mm. Raises listing every violation."""
        bad=[]
        for I in s.inst:
            if I['sy'].name in ('PWR_FLAG',) or I['sy'].lib=='power': continue
            ps=[k for k in I['sy'].pins if k[0] in (I['unit'],0)]
            pts=[s.pin(I['ref'],k[1],I['unit'] if k[0]!=0 else None) for k in ps]
            if len(pts)<2: continue
            for a,b in s.wires:
                if len(pts)==2:
                    (x1,y1),(x2,y2)=pts
                    if abs(x1-x2)<.01 and abs(a[0]-x1)<.01 and abs(b[0]-x1)<.01: lo,hi=sorted((y1,y2)); l2,h2=sorted((a[1],b[1])); hit=min(hi,h2)-max(lo,l2)>.05
                    elif abs(y1-y2)<.01 and abs(a[1]-y1)<.01 and abs(b[1]-y1)<.01: lo,hi=sorted((x1,x2)); l2,h2=sorted((a[0],b[0])); hit=min(hi,h2)-max(lo,l2)>.05
                    else: hit=False
                else:
                    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; m=.6
                    x0,x1_,y0,y1_=min(xs)+m,max(xs)-m,min(ys)+m,max(ys)-m
                    if x0>=x1_ or y0>=y1_: hit=False
                    else:
                        lx,hx=sorted((a[0],b[0])); ly,hy=sorted((a[1],b[1])); hit=lx<x1_ and hx>x0 and ly<y1_ and hy>y0
                if hit: bad.append((I['ref'],a,b))
        if bad: print('NOTE wire passes through part body:',bad)
    def _tbox(s,t,x,y,size,rot90,just):
        w=len(t)*0.78*size; h=size
        if rot90: w,h=h,w
        if just=='left': x0=x
        elif just=='right': x0=x-w
        else: x0=x-w/2
        return (x0,x0+w,y-h/2,y+h/2)
    def check_overlaps(s):
        """Flag (never fix): text boxes overlapping part bodies or other text; collinear wires overlapping each other.
        Text extents are estimates (0.78*size per character)."""
        bad=[]; tb=[]
        bodies=[]
        for I in s.inst:
            if I['sy'].name=='PWR_FLAG' or I['sy'].lib=='power': continue
            ps=[k for k in I['sy'].pins if k[0] in (I['unit'],0)]
            pts=[s.pin(I['ref'],k[1],I['unit'] if k[0]!=0 else None) for k in ps]
            if len(pts)<2: continue
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            if len(pts)==2:
                hw=1.0 if I['sy'].name=='R' else 2.0
                if abs(xs[0]-xs[1])<.01: bx=(xs[0]-hw,xs[0]+hw,min(ys),max(ys))
                else: bx=(min(xs),max(xs),ys[0]-hw,ys[0]+hw)
            else:
                g=I['sy'].gbox()
                if g is None: continue
                cs=[]
                for gx in (g[0],g[1]):
                    for gy in (g[2],g[3]):
                        px=-gx if I['mir'] else gx; r=math.radians(I['rot'])
                        cs.append((I['x']+px*math.cos(r)-gy*math.sin(r),I['y']-(px*math.sin(r)+gy*math.cos(r))))
                m=.3; bx=(min(c[0] for c in cs)+m,max(c[0] for c in cs)-m,min(c[1] for c in cs)+m,max(c[1] for c in cs)-m)
                if bx[0]>=bx[1] or bx[2]>=bx[3]: continue
            bodies.append((I['ref'],bx))
        def hit(a,b): return min(a[1],b[1])-max(a[0],b[0])>.05 and min(a[3],b[3])-max(a[2],b[2])>.05
        for I in s.inst:
            if I['ref'].startswith('#') or not I['show']: continue
            r90=False; cj='center' if I['rp'][0]==0 else ('right' if I.get('jr') else 'left')
            if I['rot']==180: cj={'left':'right','right':'left'}.get(cj,cj)   # KiCad flips justification in 180-degree symbols
            tb.append((I['ref']+' ref',s._tbox(I['ref'],I['x']+I['rp'][0],I['y']+I['rp'][1],1.27,r90,cj)))
            if I.get('vang') is None:
                tb.append((I['ref']+' value',s._tbox(I['val'],I['x']+I['vp'][0],I['y']+I['vp'][1],1.27,r90,'center' if I['vp'][0]==0 else cj)))
        for n,x,y,g,j in s.labels: tb.append(('label '+n,s._tbox(n,x,y+.7,1.27,g in (90,270),j)))
        for t,x,y,z in s.texts: tb.append(('text '+t[:12],s._tbox(t,x,y,z,False,'left')))
        for i,(n,b) in enumerate(tb):
            for ref,bx in bodies:
                if hit(b,bx): bad.append('%s overlaps body of %s'%(n,ref))
            for n2,b2 in tb[i+1:]:
                if hit(b,b2): bad.append('%s overlaps %s'%(n,n2))
        W=s.wires
        for i,(a,b) in enumerate(W):
            for c,d in W[i+1:]:
                if abs(a[0]-b[0])<.01 and abs(c[0]-d[0])<.01 and abs(a[0]-c[0])<.01:
                    ov=min(max(a[1],b[1]),max(c[1],d[1]))-max(min(a[1],b[1]),min(c[1],d[1]))
                elif abs(a[1]-b[1])<.01 and abs(c[1]-d[1])<.01 and abs(a[1]-c[1])<.01:
                    ov=min(max(a[0],b[0]),max(c[0],d[0]))-max(min(a[0],b[0]),min(c[0],d[0]))
                else: continue
                if ov>.05: bad.append('wires overlap: %s-%s and %s-%s'%(a,b,c,d))
        if bad: print('NOTE layout overlaps:','; '.join(bad))
    def write(s,fn,noflags=False):
        s.check_bodies(); s.check_overlaps()
        if not getattr(s,'_centered',False): s.center(); s._centered=True
        if noflags:
            keep=s.inst; s.inst=[I for I in s.inst if I['sy'].name!='PWR_FLAG']
            try: return s._write(fn)
            finally: s.inst=keep
        return s._write(fn)
    def _write(s,fn):
        pts=s._split(); J=s.junctions(pts); root=U()
        o=['(kicad_sch (version 20211123) (generator hand)\n  (uuid %s)\n  (paper "%s")\n  (title_block (title "%s") (date "%s") (company "%s")%s)\n  (lib_symbols\n'%(root,s.paper,s.title,getattr(s,'date',''),getattr(s,'company',''),''.join(' (comment %d "%s")'%(i+1,c) for i,c in enumerate(([getattr(s,'desc','')] if isinstance(getattr(s,'desc',''),str) else getattr(s,'desc',[]))[:4])))]
        for k,sy in s.syms.items(): o.append(sy.lib_text()+'\n')
        o.append('  )\n')
        for x,y in J: o.append('  (junction (at %g %g) (diameter 0) (color 0 0 0 0) (uuid %s))\n'%(x,y,U()))
        for x,y in s.ncs: o.append('  (no_connect (at %g %g) (uuid %s))\n'%(x,y,U()))
        for a,b in s.wires: o.append('  (wire (pts (xy %g %g) (xy %g %g)) (stroke (width 0) (type default) (color 0 0 0 0)) (uuid %s))\n'%(a[0],a[1],b[0],b[1],U()))
        for n,x,y,ang,j in s.labels: o.append('  (label "%s" (at %g %g %d) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid %s))\n'%(n,x,y,ang,j,U()))
        for t,x,y,sz in s.texts: o.append('  (text "%s" (at %g %g 0) (effects (font (size %g %g)) (justify left)) (uuid %s))\n'%(t,x,y,sz,sz,U()))
        ins=[]
        for I in s.inst:
            sy=I['sy']; hide='' if I['show'] else ' hide'
            mir=' (mirror y)' if I['mir'] else ''
            o.append('  (symbol (lib_id "%s:%s") (at %g %g %d)%s (unit %d) (in_bom yes) (on_board yes) (uuid %s)\n'%(sy.lib,sy.name,I['x'],I['y'],I['rot'],mir,I['unit'],U()))
            rh=hide if I['ref'].startswith('#') else ''
            just='' if I['rp'][0]==0 else (' (justify right)' if I.get('jr') else ' (justify left)')
            o.append('    (property "Reference" "%s" (id 0) (at %g %g %d) (effects (font (size 1.27 1.27))%s%s))\n'%(I['ref'],I['x']+I['rp'][0],I['y']+I['rp'][1],(90 if I['rot'] in (90,270) else 0),just,hide if I['ref'].startswith('#') else ''))
            o.append('    (property "Value" "%s" (id 1) (at %g %g %d) (effects (font (size %s %s))%s%s))\n'%(I['val'],I['x']+I['vp'][0],I['y']+I['vp'][1],I['vang'] if I.get('vang') is not None else (90 if I['rot'] in (90,270) else 0),('0.9' if I.get('vang') is not None else '1.27'),('0.9' if I.get('vang') is not None else '1.27'),(('' if I.get('vang') is not None else just)),hide if ((I['ref'].startswith('#') and I['sy'].name in ('GND','PWR_FLAG')) or I.get('hidev')) else ''))
            o.append('    (property "Footprint" "%s" (id 2) (at %g %g 0) (effects (font (size 1.27 1.27)) hide))\n'%(I['fp'],I['x'],I['y']))
            for (u,n) in sy.pins:
                if u in (I['unit'],0): o.append('    (pin "%s" (uuid %s))\n'%(n,U()))
            o.append('  )\n')
        o.append('  (sheet_instances (path "/" (page "1")))\n  (symbol_instances\n')
        for I in s.inst:
            o.append('    (path "/%s" (reference "%s") (unit %d) (value "%s") (footprint ""))\n'%(root,I['ref'],I['unit'],I['val']))
        o.append('  )\n)\n')
        open(fn,'w').write(''.join(o))
