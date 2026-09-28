# Lädt OSM-Gebäudegrundrisse in Kacheln, in denen Denkmäler liegen (mit Zwischenspeicher je Kachel)
import json,os,time,urllib.request,urllib.parse,math
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(open(P+'/data/denkmaeler.json'))['m']
um=json.load(open(P+'/data/umland.json')) if os.path.exists(P+'/data/umland.json') else []
DY,DX=0.01,0.015
tiles=sorted({(math.floor(o['z']/DY),math.floor(o['x']/DX)) for o in d+um})
print(len(tiles),'Kacheln',flush=True)
EPS=['https://overpass-api.de/api/interpreter','https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']
for n,(ty,tx) in enumerate(tiles):
    f=f'{P}/raw/buildings/{ty}_{tx}.json'
    if os.path.exists(f): continue
    s,w,nn,e=ty*DY-0.0005,tx*DX-0.0005,(ty+1)*DY+0.0005,(tx+1)*DX+0.0005
    q=f'[out:json][timeout:120];(way["building"]({s},{w},{nn},{e});rel["building"]({s},{w},{nn},{e});way["ref:BLfD"]({s},{w},{nn},{e}););out geom tags;'
    for a in range(8):
        try:
            req=urllib.request.Request(EPS[a%3],data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'denkmalkarte-muenchen/1.0'})
            res=json.load(urllib.request.urlopen(req,timeout=150))
            if 'remark' in res and 'runtime error' in res['remark']: raise Exception(res['remark'][:60])
            els=[{'t':x['type'],'id':x['id'],'g':x.get('geometry'),'m':[{'r':m.get('role'),'g':m.get('geometry')} for m in x.get('members',[]) if m.get('type')=='way'],
                  'ref':x.get('tags',{}).get('ref:BLfD','')} for x in res['elements']]
            json.dump(els,open(f,'w')); break
        except Exception as ex:
            print('retry',ty,tx,str(ex)[:60],flush=True); time.sleep(6+a*4)
    if n%20==0: print(n,len(tiles),flush=True)
print('fertig',flush=True)
