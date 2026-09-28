# Umland-Baudenkmäler (Gemeindenamen via Wikidata-AGS) und Bodendenkmäler -> data/umland.json, data/bodendenkmaeler.json
import json,re,urllib.request,urllib.parse,os
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exec(open(P+'/scripts/build.py').read().split('out=[];ens=[]')[0].split("en=json.load")[0])  # imports
src=open(P+'/scripts/build.py').read()
exec(src[src.index('ABBR='):src.index('out=[];ens=[]')])   # CATS, cat(), year(), title_of()
w=json.load(open(P+'/raw/einzeldenkmalO.json'))
keys=[k for k in w if not k.startswith('D-1-62-000')]
ags=sorted({'09'+k[2:10].replace('-','') for k in keys})
q='SELECT ?ags ?name WHERE { VALUES ?ags {'+' '.join('"%s"'%a for a in ags)+'} ?it wdt:P439 ?ags . ?it rdfs:label ?name FILTER(lang(?name)="de") }'
req=urllib.request.Request('https://query.wikidata.org/sparql?'+urllib.parse.urlencode({'query':q}),headers={'Accept':'application/sparql-results+json','User-Agent':'denkmalkarte-muenchen/1.0'})
G={b['ags']['value']:b['name']['value'] for b in json.load(urllib.request.urlopen(req,timeout=60))['results']['bindings']}
print('Gemeinden',len(G),'von',len(ags))
out=[]
for k in keys:
    o=w[k]; b=json.loads(o['bbox']) if isinstance(o['bbox'],str) else o['bbox']
    d=re.sub(r'\s+',' ',o.get('beschreibung','')).strip(); f=o.get('funktion','')
    t=o.get('tradobjbez') or title_of(d) or f.split(',')[0] or 'Baudenkmal'
    out.append({'i':k,'a':o.get('adresse',''),'t':t,'d':d,'f':f.split(',')[0],'c':cat(f,d[:160]),'y':year(d),'g':G.get('09'+k[2:10].replace('-',''),'Umland'),
                'x':round((b[0]+b[2])/2,6),'z':round((b[1]+b[3])/2,6),'b':[round(v,6) for v in b]})
json.dump(out,open(P+'/data/umland.json','w'),ensure_ascii=False,separators=(',',':'))
bd=json.load(open(P+'/raw/bodendenkmalO.json')); outb=[]
for k,o in bd.items():
    b=json.loads(o['bbox']) if isinstance(o['bbox'],str) else o['bbox']
    d=re.sub(r'\s+',' ',o.get('beschreibung','')).strip()
    t=re.split(r'[,;(]| mit ',d,maxsplit=1)[0].strip().rstrip('.') or 'Bodendenkmal'
    if len(t)>70: t=t[:68].rsplit(' ',1)[0]+' …'
    outb.append({'i':k,'t':t,'d':d,'b':[round(v,6) for v in b]})
json.dump(outb,open(P+'/data/bodendenkmaeler.json','w'),ensure_ascii=False,separators=(',',':'))
import collections
print(len(out),'Umland',collections.Counter(o['g'] for o in out).most_common(8)); print(len(outb),'Bodendenkmäler', [o['t'] for o in outb[:6]])
