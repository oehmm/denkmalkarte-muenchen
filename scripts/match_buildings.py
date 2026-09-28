# Ordnet jedem Denkmal OSM-Gebäudeumrisse zu -> data/umrisse.json
import json,os,glob,math,collections
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K=math.cos(math.radians(48.14)); MX=111200*K; MY=111200
def join(segs):
    segs=[[tuple((p['lon'],p['lat'])) for p in s] for s in segs if s]; out=[]
    while segs:
        r=segs.pop()
        while r[0]!=r[-1]:
            for i,s in enumerate(segs):
                if s[0]==r[-1]: r+=s[1:]; break
                if s[-1]==r[-1]: r+=s[::-1][1:]; break
                if s[-1]==r[0]: r=s+r[1:]; break
                if s[0]==r[0]: r=s[::-1]+r[1:]; break
            else: break
            segs.pop(i)
        if len(r)>=4 and r[0]==r[-1]: out.append(r)
    return out
B={}
for f in glob.glob(P+'/raw/buildings/*.json'):
    for e in json.load(open(f)):
        k=(e['t'],e['id'])
        if k in B: continue
        if e['t']=='way' and e['g'] and len(e['g'])>=4:
            r=[(p['lon'],p['lat']) for p in e['g']]
            if r[0]!=r[-1]: continue
            rings=[r]
        elif e['t']=='relation':
            rings=join([m['g'] for m in e['m'] if m['r'] in ('outer','') and m['g']])
        else: continue
        if rings: B[k]={'rings':rings,'ref':e.get('ref','')}
def area(r): return abs(sum((r[i][0]*r[i-1][1]-r[i-1][0]*r[i][1]) for i in range(len(r))))/2*MX*MY
def pip(x,y,r):
    ins=False;j=len(r)-1
    for i in range(len(r)):
        xi,yi=r[i];xj,yj=r[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: ins=not ins
        j=i
    return ins
def segdist(x,y,r):
    best=1e9
    for (ax,ay),(bx,by) in zip(r,r[1:]):
        ax_,ay_,bx_,by_,px,py=ax*MX,ay*MY,bx*MX,by*MY,x*MX,y*MY
        dx,dy=bx_-ax_,by_-ay_; L=dx*dx+dy*dy or 1e-9; t=max(0,min(1,((px-ax_)*dx+(py-ay_)*dy)/L))
        best=min(best,math.hypot(px-ax_-t*dx,py-ay_-t*dy))
    return best
G=collections.defaultdict(list); byref=collections.defaultdict(list)
for k,b in B.items():
    xs=[p[0] for r in b['rings'] for p in r]; ys=[p[1] for r in b['rings'] for p in r]
    b['bb']=(min(xs),min(ys),max(xs),max(ys)); b['a']=sum(area(r) for r in b['rings'])
    b['c']=(sum(xs)/len(xs),sum(ys)/len(ys))
    for gx in range(int(b['bb'][0]/0.002),int(b['bb'][2]/0.002)+1):
        for gy in range(int(b['bb'][1]/0.002),int(b['bb'][3]/0.002)+1): G[(gx,gy)].append(k)
    for ref in b['ref'].split(';'):
        if ref.strip(): byref[ref.strip()].append(k)
def near(x,y,rad=1):
    s=set()
    for dx in range(-rad,rad+1):
        for dy in range(-rad,rad+1): s.update(G.get((int(x/0.002)+dx,int(y/0.002)+dy),[]))
    return s
def dp(pts,eps=0.4):
    if len(pts)<4: return pts
    keep={0,len(pts)-1};st=[(0,len(pts)-1)]
    while st:
        a,b=st.pop();ax,ay=pts[a][0]*MX,pts[a][1]*MY;bx,by=pts[b][0]*MX,pts[b][1]*MY;dx,dy=bx-ax,by-ay;L=dx*dx+dy*dy or 1e-9;mi=-1;md=eps
        for i in range(a+1,b):
            px,py=pts[i][0]*MX,pts[i][1]*MY;t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L));d=math.hypot(px-ax-t*dx,py-ay-t*dy)
            if d>md: md=d;mi=i
        if mi>=0: keep.add(mi);st+=[(a,mi),(mi,b)]
    return [pts[i] for i in sorted(keep)]
d=json.load(open(P+'/data/denkmaeler.json'))['m']
um=json.load(open(P+'/data/umland.json'))
out={};how=collections.Counter()
for o in [dict(m,full='D-1-62-000-'+m['i'],key=m['i']) for m in d]+[dict(u,full=u['i'],key=u['i']) for u in um]:
    x,y=o['x'],o['z']; ks=list(byref.get(o['full'],[]))
    if ks: how['ref']+=1
    else:
        cands=near(x,y); inside=[k for k in cands if x>=B[k]['bb'][0]-1e-6 and x<=B[k]['bb'][2]+1e-6 and y>=B[k]['bb'][1]-1e-6 and y<=B[k]['bb'][3]+1e-6 and any(pip(x,y,r) for r in B[k]['rings'])]
        if inside: ks=[min(inside,key=lambda k:B[k]['a'])]; how['punkt']+=1
        else:
            dist=[(min(segdist(x,y,r) for r in B[k]['rings']),k) for k in cands]
            dist=[t for t in dist if t[0]<=12]
            if dist: ks=[min(dist)[1]]; how['nah']+=1
        naddr=len([a for a in o.get('a','').split(';') if a.strip() and not a.strip().startswith('Nähe')])
        bb=o['b']; bw=(bb[2]-bb[0])*MX; bh=(bb[3]-bb[1])*MY
        if ks and naddr>=2 and bw<250 and bh<250:
            for k in near((bb[0]+bb[2])/2,(bb[1]+bb[3])/2,2):
                c=B[k]['c']
                if k not in ks and bb[0]<=c[0]<=bb[2] and bb[1]<=c[1]<=bb[3] and B[k]['a']>=30: ks.append(k)
    if not ks: how['ohne']+=1; continue
    # sehr große Treffer (z. B. ganzes Areal) nur, wenn per Aktennummer zugeordnet
    if not byref.get(o['full']) and sum(B[k]['a'] for k in ks)>60000: how['zu_groß']+=1; continue
    out[o['key']]=[[round(v,6) for p in dp(r) for v in p] for k in ks for r in B[k]['rings']]
json.dump(out,open(P+'/data/umrisse.json','w'),separators=(',',':'))
print(len(B),'Gebäude;',dict(how),'->',len(out),'Denkmäler mit Umriss;',round(os.path.getsize(P+'/data/umrisse.json')/1e6,1),'MB')
