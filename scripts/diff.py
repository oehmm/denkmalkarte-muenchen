# Vergleicht Listenstand 21.12.2024 mit 25.09.2026 -> data/aenderungen.json
import json,re,difflib,os,time,urllib.request,urllib.parse
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
old={e['id']:e for e in json.load(open(P+'/raw/entries_2024-12-21.json'))}
new={e['id']:e for e in json.load(open(P+'/raw/entries.json'))}
norm=lambda t:re.sub(r'\s+',' ',t.replace('\n',' ')).strip()
ABBR=r'(?<!\bSt)(?<!\bStr)(?<!\bNr)(?<!\bHl)(?<!\behem)(?<!\bbez)(?<!\bca)'
def split(t):
    m=re.search(ABBR+r'\.\s+(?=[A-ZÄÖÜ„"(])',t)
    return (t[:m.start()],t[m.end():]) if m else ('',t)
def addrset(a): return {x.strip() for x in a.split(';') if x.strip()}
def wdiff(a,b):
    A=re.findall(r'\S+\s*',a); B=re.findall(r'\S+\s*',b); out=[]
    for op,i1,i2,j1,j2 in difflib.SequenceMatcher(None,A,B,autojunk=False).get_opcodes():
        if op=='equal': out.append(['=',''.join(A[i1:i2])])
        else:
            if i2>i1: out.append(['-',''.join(A[i1:i2])])
            if j2>j1: out.append(['+',''.join(B[j1:j2])])
    return out
res={'alt':'21.12.2024','neu':'25.09.2026','neu_ids':[],'geaendert':{},'gestrichen':[]}
for k in new:
    if k not in old: res['neu_ids'].append(k[11:] if k.startswith('D') else k); continue
    a,b=norm(old[k]['text']),norm(new[k]['text'])
    if a==b: continue
    if k.startswith('E'):
        res['geaendert'][k]={'k':'t','d':wdiff(a,b)}; continue
    aa,ad=split(a); ba,bd=split(b)
    kinds=[]
    if addrset(aa)!=addrset(ba): kinds.append('a')
    if ad!=bd: kinds.append('t')
    if not kinds: continue   # nur Reihenfolge der Adressen geändert
    res['geaendert'][k[11:]]={'k':''.join(kinds),'d':wdiff(ad,bd) if 't' in kinds else [],
        'aa':sorted(addrset(aa)-addrset(ba)),'an':sorted(addrset(ba)-addrset(aa))}
# gestrichene Denkmäler: Adresse geokodieren (Nominatim, 1 Anfrage/s)
cache_f=P+'/raw/geocode_cache.json'
cache=json.load(open(cache_f)) if os.path.exists(cache_f) else {}
for k in sorted(old):
    if k in new or not k.startswith('D'): continue
    a,d=split(norm(old[k]['text']))
    first=[x for x in a.split(';') if x.strip() and not x.strip().startswith('Nähe')][:1] or [a]
    q=first[0].strip()+', München'
    if q not in cache:
        url='https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=de&q='+urllib.parse.quote(q)
        req=urllib.request.Request(url,headers={'User-Agent':'denkmalkarte-muenchen/1.0 (private project)'})
        try: cache[q]=json.load(urllib.request.urlopen(req,timeout=30))
        except Exception as e: cache[q]=[]; print('geo fail',q,e)
        time.sleep(1.1)
    hit=cache[q][0] if cache[q] else None
    t=re.split(r',|;',d,maxsplit=1)[0].strip()
    res['gestrichen'].append({'i':k[11:],'a':a,'t':t,'d':d,'x':round(float(hit['lon']),6) if hit else None,'z':round(float(hit['lat']),6) if hit else None})
json.dump(cache,open(cache_f,'w'),ensure_ascii=False)
json.dump(res,open(P+'/data/aenderungen.json','w'),ensure_ascii=False,separators=(',',':'))
from collections import Counter
print('neu',len(res['neu_ids']),'geändert',len(res['geaendert']),Counter(v['k'] for v in res['geaendert'].values()),'gestrichen',len(res['gestrichen']),'ohne Koord.',sum(1 for g in res['gestrichen'] if g['x'] is None))
