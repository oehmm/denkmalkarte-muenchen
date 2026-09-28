# Schneller: nur Gebäude in kleinen Boxen um die Denkmäler (je 80 Denkmäler pro Anfrage, 2 parallel)
import json,os,time,urllib.request,urllib.parse,math,concurrent.futures as cf
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(open(P+'/data/denkmaeler.json'))['m']; um=json.load(open(P+'/data/umland.json'))
objs=sorted(d+um,key=lambda o:(round(o['z'],2),o['x']))
K=math.cos(math.radians(48.14))
def box(o):
    b=o['b']; w=(b[2]-b[0])*111200*K; h=(b[3]-b[1])*111200
    if w>250 or h>250: b=[o['x'],o['z'],o['x'],o['z']]
    px=25/(111200*K); py=25/111200
    return (round(b[1]-py,6),round(b[0]-px,6),round(b[3]+py,6),round(b[2]+px,6))
batches=[objs[i:i+80] for i in range(0,len(objs),80)]
os.makedirs(P+'/raw/buildings',exist_ok=True)
EPS=['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']
def run(n):
    f=f'{P}/raw/buildings/b{n}.json'
    if os.path.exists(f): return 'cached'
    q='[out:json][timeout:120];('+''.join('way["building"]('+','.join(map(str,box(o)))+');' for o in batches[n])+');out geom tags;'
    for a in range(8):
        try:
            req=urllib.request.Request(EPS[0 if a<5 else 1],data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'denkmalkarte-muenchen/1.0'})
            res=json.load(urllib.request.urlopen(req,timeout=150))
            if 'remark' in res and 'error' in res['remark']: raise Exception(res['remark'][:60])
            els=[{'t':x['type'],'id':x['id'],'g':x.get('geometry'),'m':[{'r':m.get('role'),'g':m.get('geometry')} for m in x.get('members',[]) if m.get('type')=='way'],
                  'ref':x.get('tags',{}).get('ref:BLfD','')} for x in res['elements']]
            json.dump(els,open(f,'w')); return len(els)
        except Exception as ex:
            time.sleep(5+a*5)
    return 'FAIL'
def rels():
    f=P+'/raw/buildings/rel.json'
    if os.path.exists(f): return
    q='[out:json][timeout:300];rel["building"](48.05,11.35,48.26,11.74);out geom tags;'
    for a in range(6):
        try:
            res=json.load(urllib.request.urlopen(urllib.request.Request(EPS[a%2],data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'denkmalkarte-muenchen/1.0'}),timeout=330))
            json.dump([{'t':'relation','id':x['id'],'g':None,'m':[{'r':m.get('role'),'g':m.get('geometry')} for m in x.get('members',[]) if m.get('type')=='way'],'ref':x.get('tags',{}).get('ref:BLfD','')} for x in res['elements']],open(f,'w'))
            print('relationen',len(res['elements']),flush=True); return
        except Exception as ex: print('retry rel',str(ex)[:60],flush=True); time.sleep(10)
print(len(batches),'Anfragen',flush=True)
done=0
with cf.ThreadPoolExecutor(2) as ex:
    for r in ex.map(run,range(len(batches))):
        done+=1
        if done%10==0: print(done,len(batches),r,flush=True)
rels()
print('fertig',flush=True)
