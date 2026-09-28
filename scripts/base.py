import json,math,collections
def load(n): return json.load(open(f'osm/{n}.json'))['elements']
def dp(pts,eps):
    if len(pts)<3: return pts
    keep=[False]*len(pts); keep[0]=keep[-1]=True; st=[(0,len(pts)-1)]
    while st:
        a,b=st.pop(); ax,ay=pts[a]; bx,by=pts[b]; dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy; mi=-1; md=eps*eps
        for i in range(a+1,b):
            px,py=pts[i]
            if L==0: d=(px-ax)**2+(py-ay)**2
            else:
                t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L)); d=(px-ax-t*dx)**2+(py-ay-t*dy)**2
            if d>md: md=d; mi=i
        if mi>=0: keep[mi]=True; st+=[(a,mi),(mi,b)]
    return [p for p,k in zip(pts,keep) if k]
K=math.cos(math.radians(48.14))
def proj(g): return [(p['lon']*K,p['lat']) for p in g]   # scaled so eps is isotropic
def unproj(pts): return [v for x,y in pts for v in (round(x/K,5),round(y,5))]
def simp(g,eps_m): return unproj(dp(proj(g),eps_m/111000))
def area(g):
    p=proj(g); return abs(sum(p[i][0]*p[i-1][1]-p[i-1][0]*p[i][1] for i in range(len(p))))/2*111000**2
def rings(members,role='outer'):
    segs=[m['geometry'] for m in members if m.get('type')=='way' and m.get('role',role) in (role,'') and 'geometry' in m]
    segs=[[(p['lon'],p['lat']) for p in s] for s in segs]; out=[]
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
        out.append([{'lon':x,'lat':y} for x,y in r])
    return out
def polys(elems,eps,minA):
    P=[]
    for e in elems:
        if e['type']=='way' and 'geometry' in e and e['geometry'][0]==e['geometry'][-1]: rs=[e['geometry']]; holes=[]
        elif e['type']=='relation': rs=rings(e['members'],'outer'); holes=rings(e['members'],'inner')
        else: continue
        for r in rs:
            if len(r)<4 or area(r)<minA: continue
            poly=[simp(r,eps)]
            for h in holes:
                if len(h)>3 and area(h)>minA and h[0]['lon']>=min(p['lon'] for p in r) and h[0]['lon']<=max(p['lon'] for p in r) and h[0]['lat']>=min(p['lat'] for p in r) and h[0]['lat']<=max(p['lat'] for p in r):
                    poly.append(simp(h,eps))
            if len(poly[0])>=6: P.append(poly)
    return P
out={}
out['green']=polys([e for e in load('green')],4,1500)
wat=load('water')
out['water']=polys([e for e in wat if e['tags'].get('natural')=='water'],3,400)
out['rivers']=[simp(e['geometry'],3) for e in wat if e['type']=='way' and e['tags'].get('waterway') in('river','canal') and 'geometry' in e]
out['rail']=[simp(e['geometry'],4) for e in load('rail') if 'geometry' in e and e['tags'].get('railway')=='rail']
CL={'motorway':'major','trunk':'major','primary':'major','motorway_link':'major','trunk_link':'major','primary_link':'major','secondary':'secondary','tertiary':'tertiary'}
roads=collections.defaultdict(list); labels=[]
RANK={'major':3,'secondary':2,'tertiary':2,'minor':1}
seen=set()
for e in load('roads'):
    g=e.get('geometry'); 
    if not g: continue
    c=CL.get(e['tags']['highway'],'minor')
    roads[c].append(simp(g,2.5 if c=='minor' else 3))
    n=e['tags'].get('name')
    if n and e['tags']['highway'] not in('motorway','motorway_link','trunk_link','primary_link'):
        p=proj(g); seg=[math.dist(p[i],p[i+1])*111000 for i in range(len(p)-1)]; Lt=sum(seg)
        if Lt<90: continue
        # midpoint along length
        acc=0
        for i,s in enumerate(seg):
            if acc+s>=Lt/2: break
            acc+=s
        t=(Lt/2-acc)/s if s else 0
        x=p[i][0]+(p[i+1][0]-p[i][0])*t; y=p[i][1]+(p[i+1][1]-p[i][1])*t
        ang=-math.degrees(math.atan2(p[i+1][1]-p[i][1],p[i+1][0]-p[i][0]))
        if ang>90: ang-=180
        if ang<-90: ang+=180
        key=(n,round(x/K/0.004),round(y/0.003))
        if key in seen: continue
        seen.add(key)
        labels.append([round(x/K,5),round(y,5),round(ang),n,RANK[c]-1 if Lt>150 else 0])
labels.sort(key=lambda l:-l[4])
out['roads']=roads; out['labels']=labels
adm=load('admin2')
city=[e for e in adm if e['tags'].get('name')=='München' and e['tags'].get('admin_level')=='6'][0]
out['city']=[simp(m['geometry'],6) for m in city['members'] if m['type']=='way' and 'geometry' in m and m.get('role')=='outer']
bez=[];BZ=[]
for e in sorted([e for e in adm if e['tags'].get('admin_level')=='9'],key=lambda e:int(e['tags']['ref'])):
    rs=rings(e['members'],'outer'); 
    rr=[simp(r,6) for r in rs if len(r)>3]
    xs=[p['lon'] for r in rs for p in r]; ys=[p['lat'] for r in rs for p in r]
    big=max(rs,key=len); 
    # label pos: polygon centroid of largest ring
    P=[(p['lon'],p['lat']) for p in big]; A=cx=cy=0
    for i in range(len(P)):
        x0,y0=P[i-1];x1,y1=P[i];c=x0*y1-x1*y0;A+=c;cx+=(x0+x1)*c;cy+=(y0+y1)*c
    bez.append({'n':e['tags']['name'],'ref':int(e['tags']['ref']),'c':[round(cx/(3*A),5),round(cy/(3*A),5)],'r':rr})
    BZ.append([[(p['lon'],p['lat']) for p in r] for r in rs])
out['bezirke']=bez
json.dump(out,open('basiskarte.json','w'),separators=(',',':'),ensure_ascii=False)
# assign districts
def pip(x,y,r):
    ins=False;j=len(r)-1
    for i in range(len(r)):
        xi,yi=r[i];xj,yj=r[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: ins=not ins
        j=i
    return ins
dm=json.load(open('dm.json')); miss=0
for m in dm['m']:
    m['k']=None
    for k,rs in enumerate(BZ):
        if sum(pip(m['x'],m['z'],r) for r in rs)%2: m['k']=k;break
    if m['k'] is None: miss+=1
print('no district',miss, collections.Counter(bez[m['k']]['n'] for m in dm['m'] if m['k'] is not None).most_common(5))
json.dump(dm,open('denkmaeler.json','w'),separators=(',',':'),ensure_ascii=False)
for k,v in out.items(): print(k, len(v) if not isinstance(v,dict) else {a:len(b) for a,b in v.items()})
