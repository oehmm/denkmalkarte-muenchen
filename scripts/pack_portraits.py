# Architekten-Porträts für das Artifact bündeln (externe Bilder sind dort gesperrt) -> site/thumbs/arch.jpg + arch.json
import json,os,urllib.request,urllib.parse,subprocess,time,concurrent.futures as cf
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A=json.load(open(P+'/data/architekten.json')); os.makedirs(P+'/raw/portraits',exist_ok=True); os.makedirs(P+'/site/thumbs',exist_ok=True)
UA={'User-Agent':'denkmalkarte-muenchen/1.0 (github.com/oehmm/denkmalkarte-muenchen)'}
def get(item):
    name,a=item; f=P+'/raw/portraits/'+a['q']+'.jpg'
    if os.path.exists(f): return name,f
    url='https://commons.wikimedia.org/wiki/Special:FilePath/'+urllib.parse.quote(a['img'])+'?width=160'
    for k in range(4):
        try:
            open(f+'.tmp','wb').write(urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60).read())
            subprocess.run(['sips','-Z','120','-s','format','jpeg','-s','formatOptions','55',f+'.tmp','--out',f],capture_output=True); os.remove(f+'.tmp'); return name,f
        except Exception: time.sleep(2+k*3)
    return name,None
buf=bytearray(); idx={}
with cf.ThreadPoolExecutor(4) as ex:
    for name,f in ex.map(get,[(n,a) for n,a in A.items() if a.get('img')]):
        if f and os.path.exists(f): d=open(f,'rb').read(); idx[name]=[len(buf),len(d)]; buf+=d
open(P+'/site/thumbs/arch.jpg','wb').write(buf); json.dump(idx,open(P+'/site/thumbs/arch.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(idx),'Porträts,',round(len(buf)/1e6,2),'MB')
