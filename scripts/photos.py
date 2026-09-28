# Commons-Fotos zu Münchner Denkmälern: Metadaten (Urheber, Lizenz) + Vorschaubilder
import json,os,re,urllib.request,urllib.parse,html,time,concurrent.futures as cf,subprocess
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA={'User-Agent':'denkmalkarte-muenchen/1.0 (private, non-commercial map; contact via GitHub oehmm)'}
wd=json.load(open(P+'/raw/wikidata.json'))['results']['bindings']
img={};cat={}
for b in wd:
    i=b['id']['value'][11:]
    if 'img' in b and i not in img: img[i]=urllib.parse.unquote(b['img']['value'].rsplit('/',1)[1]).replace('_',' ')
    if 'cat' in b: cat[i]=b['cat']['value']
meta_f=P+'/raw/commons_meta.json'
meta=json.load(open(meta_f)) if os.path.exists(meta_f) else {}
titles=sorted(set(img.values())-set(meta))
def clean(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',s or ''))).strip()
for k in range(0,len(titles),50):
    batch=titles[k:k+50]
    q=urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':'200',
        'iiextmetadatafilter':'Artist|LicenseShortName','titles':'|'.join('File:'+t for t in batch)})
    for a in range(4):
        try: d=json.load(urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+q,headers=UA),timeout=60));break
        except Exception as e: time.sleep(3)
    norm={n['to']:n['from'] for n in d['query'].get('normalized',[])}
    for pg in d['query']['pages'].values():
        t=pg['title'][5:]
        ii=(pg.get('imageinfo') or [{}])[0]; em=ii.get('extmetadata',{})
        meta[t]={'th':ii.get('thumburl'),'pg':ii.get('descriptionurl'),'ar':clean(em.get('Artist',{}).get('value'))[:80],'li':clean(em.get('LicenseShortName',{}).get('value'))}
    if k%1000==0: print('meta',k,len(titles),flush=True)
    time.sleep(0.3)
json.dump(meta,open(meta_f,'w'),ensure_ascii=False)
out={}
for i,t in img.items():
    m=meta.get(t)
    if m and m.get('th'): out[i]=[t,m['th'],m['ar'],m['li']]
json.dump({'f':out,'cat':cat},open(P+'/data/fotos.json','w'),ensure_ascii=False,separators=(',',':'))
print('Fotos mit Metadaten',len(out),flush=True)
# Vorschaubilder für das Artifact (externe Bilder sind dort gesperrt)
os.makedirs(P+'/raw/thumbs',exist_ok=True)
def get(item):
    i,(t,th,ar,li)=item; f=P+f'/raw/thumbs/{i}.jpg'
    if os.path.exists(f) and os.path.getsize(f)>500: return 0
    for a in range(4):
        try:
            data=urllib.request.urlopen(urllib.request.Request(th,headers=UA),timeout=60).read()
            open(f+'.tmp','wb').write(data)
            subprocess.run(['sips','-Z','200','-s','format','jpeg','-s','formatOptions','55',f+'.tmp','--out',f],capture_output=True)
            os.remove(f+'.tmp'); return 1
        except Exception as e: time.sleep(2+a*3)
    return 0
n=0
with cf.ThreadPoolExecutor(4) as ex:
    for r in ex.map(get,out.items()):
        n+=1
        if n%500==0: print('thumbs',n,len(out),flush=True)
print('fertig',flush=True)
