# Wikipedia-Links + Auszüge für Denkmäler, Architekten-Porträts (Wikidata) -> data/wiki.json, data/architekten.json
import json,os,re,time,urllib.request,urllib.parse,collections,unicodedata,html
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA={'User-Agent':'denkmalkarte-muenchen/1.0 (private map; github.com/oehmm/denkmalkarte-muenchen)','Accept':'application/sparql-results+json'}
def sparql(q):
    for a in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request('https://query.wikidata.org/sparql?'+urllib.parse.urlencode({'query':q}),headers=UA),timeout=120))['results']['bindings']
        except Exception as e: print('retry sparql',e,flush=True); time.sleep(5+a*5)
    return []
def api(host,params):
    for a in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(f'https://{host}/w/api.php?'+urllib.parse.urlencode({**params,'format':'json'}),headers=UA),timeout=60))
        except Exception as e: print('retry api',e,flush=True); time.sleep(3+a*4)
    return {}
v=lambda b,k:b[k]['value'] if k in b else None
# 1) Denkmäler: Wikidata-Item, de/en-Wikipedia, Architekten (P84)
rows=sparql('''SELECT ?item ?id ?de ?en ?arch ?archLabel WHERE {
  ?item wdt:P4244 ?id . FILTER(STRSTARTS(?id,"D-1-") || STRSTARTS(?id,"E-1-"))
  ?item wdt:P625 ?c . ?item wdt:P131* wd:Q1726 .
  OPTIONAL{ ?de schema:about ?item ; schema:isPartOf <https://de.wikipedia.org/> }
  OPTIONAL{ ?en schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  OPTIONAL{ ?item wdt:P84 ?arch }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". } }''')
um=json.load(open(P+'/data/umland.json')); umids={o['i'] for o in um}
rows2=sparql('SELECT ?item ?id ?de ?en ?arch ?archLabel WHERE { VALUES ?id {'+' '.join(f'"{i}"' for i in umids)+'''} ?item wdt:P4244 ?id .
  OPTIONAL{ ?de schema:about ?item ; schema:isPartOf <https://de.wikipedia.org/> }
  OPTIONAL{ ?en schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  OPTIONAL{ ?item wdt:P84 ?arch }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". } }''')
W={}; P84=collections.defaultdict(set); archLabel={}
for b in rows+rows2:
    i=v(b,'id'); w=W.setdefault(i,{'wd':v(b,'item').rsplit('/',1)[1]})
    if v(b,'de'): w['de']=urllib.parse.unquote(v(b,'de').rsplit('/wiki/',1)[1]).replace('_',' ')
    if v(b,'en'): w['en']=urllib.parse.unquote(v(b,'en').rsplit('/wiki/',1)[1]).replace('_',' ')
    if v(b,'arch'): q=v(b,'arch').rsplit('/',1)[1]; P84[i].add(q); archLabel[q]=v(b,'archLabel')
print('Wikidata-Items',len(W),'mit de-Artikel',sum('de' in w for w in W.values()),'mit en',sum('en' in w for w in W.values()),'mit Architekt (P84)',len(P84),flush=True)
json.dump({'W':W,'P84':{k:sorted(s) for k,s in P84.items()},'L':archLabel},open(P+'/raw/wiki_stage1.json','w'),ensure_ascii=False)
