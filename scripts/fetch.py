import urllib.request, re, json, concurrent.futures as cf, os
U="https://geoservices.bayern.de/od/wms/gdi/v1/denkmal?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS={L}&QUERY_LAYERS={L}&SRS=EPSG:4326&BBOX={b}&WIDTH=3&HEIGHT=3&X=1&Y=1&INFO_FORMAT=application/vnd.ogc.gml&FEATURE_COUNT=5000&STYLES="
feat=re.compile(r'<(\w+)_feature>(.*?)</\1_feature>',re.S)
def get(L,x0,y0,x1,y1,depth=0):
    b=f"{x0:.5f},{y0:.5f},{x1:.5f},{y1:.5f}"
    for t in range(4):
        try: s=urllib.request.urlopen(U.format(L=L,b=b),timeout=90).read().decode('utf-8','replace');break
        except Exception as e: s=None
    if s is None: print('FAIL',b); return []
    fs=feat.findall(s)
    if len(fs)>=4900 and depth<6:
        mx=(x0+x1)/2;my=(y0+y1)/2;out=[]
        for q in [(x0,y0,mx,my),(mx,y0,x1,my),(x0,my,mx,y1),(mx,my,x1,y1)]: out+=get(L,*q,depth+1)
        return out
    res=[]
    for _,f in fs:
        d={k:v.strip() for k,v in re.findall(r'<(\w+)>([^<]*)</\1>',f)}
        c=re.search(r'<gml:coordinates>([^<]*)',f).group(1).split()
        d['bbox']=[float(v) for p in c for v in p.split(',')]
        res.append(d)
    return res
import sys
L=sys.argv[1]; st=float(sys.argv[2])
jobs=[]
y=48.05
while y<48.25:
    x=11.36
    while x<11.73: jobs.append((x,y,x+st,y+st)); x+=st
    y+=st
allf={}
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(lambda j:get(L,*j),jobs):
        for d in r: allf.setdefault(d.get('aktennummer'),d)
print(L,len(jobs),len(allf))
json.dump(allf,open(f'{L}.json','w'),ensure_ascii=False)
