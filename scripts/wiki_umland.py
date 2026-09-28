import json,os,time,urllib.request,urllib.parse
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA={'User-Agent':'denkmalkarte-muenchen/1.0 (github.com/oehmm/denkmalkarte-muenchen)','Accept':'application/sparql-results+json','Content-Type':'application/x-www-form-urlencoded'}
S=json.load(open(P+'/raw/wiki_stage1.json')); W,P84,L=S['W'],{k:set(v) for k,v in S['P84'].items()},S['L']
ids=sorted(o['i'] for o in json.load(open(P+'/data/umland.json')))
v=lambda b,k:b[k]['value'] if k in b else None
for k in range(0,len(ids),60):
    q='SELECT ?item ?id ?de ?en ?arch ?archLabel WHERE { VALUES ?id {'+' '.join(f'"{i}"' for i in ids[k:k+60])+'''} ?item wdt:P4244 ?id .
      OPTIONAL{ ?de schema:about ?item ; schema:isPartOf <https://de.wikipedia.org/> }
      OPTIONAL{ ?en schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
      OPTIONAL{ ?item wdt:P84 ?arch }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". } }'''
    for a in range(5):
        try: rows=json.load(urllib.request.urlopen(urllib.request.Request('https://query.wikidata.org/sparql',data=urllib.parse.urlencode({'query':q}).encode(),headers=UA),timeout=120))['results']['bindings']; break
        except Exception as e: print('retry',e); time.sleep(5+a*5); rows=[]
    for b in rows:
        i=v(b,'id'); w=W.setdefault(i,{'wd':v(b,'item').rsplit('/',1)[1]})
        if v(b,'de'): w['de']=urllib.parse.unquote(v(b,'de').rsplit('/wiki/',1)[1]).replace('_',' ')
        if v(b,'en'): w['en']=urllib.parse.unquote(v(b,'en').rsplit('/wiki/',1)[1]).replace('_',' ')
        if v(b,'arch'): q2=v(b,'arch').rsplit('/',1)[1]; P84.setdefault(i,set()).add(q2); L[q2]=v(b,'archLabel')
    time.sleep(1)
print('Items gesamt',len(W),'Umland mit Item',sum(1 for i in ids if i in W),'davon de-Artikel',sum(1 for i in ids if 'de' in W.get(i,{})))
json.dump({'W':W,'P84':{k:sorted(s) for k,s in P84.items()},'L':L},open(P+'/raw/wiki_stage1.json','w'),ensure_ascii=False)
