# Stufe 2: Wikipedia-Auszüge, Architekten-Zuordnung und -Details
import json,os,re,time,urllib.request,urllib.parse,collections,unicodedata
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA={'User-Agent':'denkmalkarte-muenchen/1.0 (github.com/oehmm/denkmalkarte-muenchen)'}
def api(host,params):
    for a in range(8):
        try:
            time.sleep(1.0)
            return json.load(urllib.request.urlopen(urllib.request.Request(f'https://{host}/w/api.php?'+urllib.parse.urlencode({**params,'format':'json','maxlag':5}),headers=UA),timeout=60))
        except urllib.error.HTTPError as e:
            wait=int(e.headers.get('Retry-After') or 0) or 20*(a+1); print('warte',wait,'s',host,e.code,flush=True); time.sleep(wait)
        except Exception as e: print('retry',host,e,flush=True); time.sleep(5+a*5)
    return {}
S=json.load(open(P+'/raw/wiki_stage1.json')); W,P84,LAB=S['W'],S['P84'],S['L']
def extracts(titles):
    out={}
    for k in range(0,len(titles),20):
        d=api('de.wikipedia.org',{'action':'query','prop':'extracts','exintro':1,'explaintext':1,'exsentences':3,'redirects':1,'titles':'|'.join(titles[k:k+20])})
        red={r['to']:r['from'] for r in d.get('query',{}).get('redirects',[])}
        nor={r['to']:r['from'] for r in d.get('query',{}).get('normalized',[])}
        for pg in d.get('query',{}).get('pages',{}).values():
            t=pg.get('title'); t0=nor.get(red.get(t,t),red.get(t,t))
            x=re.sub(r'\s+',' ',pg.get('extract','') or '').strip()
            if x: out[t0]=x[:600]
        time.sleep(0.3)
    return out
# --- Denkmäler: Auszüge
titles=sorted({w['de'] for w in W.values() if 'de' in w})
if os.path.exists(P+'/data/wiki.json'):
    old=json.load(open(P+'/data/wiki.json')); EX={v[1]:v[2] for v in old.values() if v[1] and v[2]}
else: EX=extracts(titles)
print('Denkmal-Auszüge',len(EX),'von',len(titles),flush=True)
wiki={}
for i,w in W.items():
    key=i[11:] if i.startswith('D-1-62-000-') else i
    wiki[key]=[w['wd'],w.get('de'),EX.get(w.get('de')) if w.get('de') else None,w.get('en')]
json.dump(wiki,open(P+'/data/wiki.json','w'),ensure_ascii=False,separators=(',',':'))
# --- Architekten zuordnen
dm=json.load(open(P+'/data/denkmaeler.json')); AR=dm['A']
cnt=collections.Counter(a for m in dm['m'] for a in m.get('ar',[]))
def norm(s): s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower(); s=re.sub(r'\b(von|van|de|der|zu|freiherr|frhr)\b','',s); return re.sub(r'[^a-z ]','',s).split()
def same(a,b):
    A,B=norm(a),norm(b)
    return bool(A) and bool(B) and A[-1]==B[-1] and A[0]==B[0]
match={}
for m in dm['m']:
    qs=P84.get('D-1-62-000-'+m['i'],[])
    for ai in m.get('ar',[]):
        for q in qs:
            if LAB.get(q) and same(AR[ai],LAB[q]): match[ai]=q
print('über Denkmal-Architekt zugeordnet',len(match),flush=True)
OK=re.compile(r'architekt|baumeister|bildhauer|maler|ingenieur|gartenkünstler|landschaftsarchitekt|stuck|künstler|bauunternehmer|baubeamt|zimmermeister|erzgießer|glasmaler|kunsthandwerk',re.I)
todo=[ai for ai,c in cnt.most_common() if ai not in match and c>=2]
cache_f=P+'/raw/arch_search.json'; CACHE=json.load(open(cache_f)) if os.path.exists(cache_f) else {}
print('Namenssuche für',len(todo),flush=True)
VAR=[('Karl ','Carl '),('Carl ','Karl '),('Konrad ','Conrad '),('Conrad ','Konrad '),('Friedrich ','Fritz '),('Joseph ','Josef '),('Josef ','Joseph '),('Johann ','Johannes '),('ä','ae'),('ö','oe'),('ü','ue')]
def variants(n): return [n]+[n.replace(a,b) for a,b in VAR if a in n]
for n,ai in enumerate(todo):
    for name in variants(AR[ai]):
        if ai in match: break
        if name in CACHE: d=CACHE[name]
        else:
            d=api('www.wikidata.org',{'action':'wbsearchentities','search':name,'language':'de','uselang':'de','type':'item','limit':6})
            if d: CACHE[name]={'search':d.get('search',[])}
            if n%25==0: json.dump(CACHE,open(cache_f,'w'),ensure_ascii=False)
        hits=[c for c in d.get('search',[]) if same(name,c.get('label',''))]
        if len(hits)>1 and sum(1 for c in hits if OK.search(c.get('description','') or ''))>1: continue   # mehrdeutiger Name
        for c in d.get('search',[]):
            desc=c.get('description','') or ''
            if same(name,c.get('label','')) and OK.search(desc):
                m=re.search(r'\b(1[4-9]\d\d)\b',desc)
                if m and int(m.group(1))>1990: continue
                match[ai]=c['id']; break
    if n%100==0: print(' ',n,len(todo),len(match),flush=True)
json.dump(CACHE,open(cache_f,'w'),ensure_ascii=False)
print('Architekten zugeordnet',len(match),flush=True)
# --- Details holen
qs=sorted(set(match.values())); ENT={}
for k in range(0,len(qs),50):
    d=api('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(qs[k:k+50]),'props':'labels|descriptions|claims|sitelinks','languages':'de|en','sitefilter':'dewiki'})
    ENT.update(d.get('entities',{})); time.sleep(0.3)
def claim(e,p):
    for c in e.get('claims',{}).get(p,[]):
        dv=c.get('mainsnak',{}).get('datavalue',{}).get('value')
        if dv is not None: return dv
def year(t): 
    m=re.match(r'[+-](\d{4})',(t or {}).get('time','') if isinstance(t,dict) else ''); return int(m.group(1)) if m else None
places=set()
for e in ENT.values():
    for p in ('P19','P20'):
        v=claim(e,p); 
        if v: places.add(v['id'])
PL={}
pl=sorted(places)
for k in range(0,len(pl),50):
    d=api('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(pl[k:k+50]),'props':'labels','languages':'de|en'})
    for q,e in d.get('entities',{}).items(): PL[q]=(e.get('labels',{}).get('de') or e.get('labels',{}).get('en') or {}).get('value')
    time.sleep(0.3)
wp_titles=sorted({e['sitelinks']['dewiki']['title'] for e in ENT.values() if e.get('sitelinks',{}).get('dewiki')})
AX=extracts(wp_titles); print('Architekten-Auszüge',len(AX),flush=True)
arch={}
for ai,q in match.items():
    e=ENT.get(q)
    if not e: continue
    img=claim(e,'P18'); wp=e.get('sitelinks',{}).get('dewiki',{}).get('title')
    b,dth=year(claim(e,'P569')),year(claim(e,'P570'))
    if b and b>1990: continue
    bp,dp=claim(e,'P19'),claim(e,'P20')
    arch[AR[ai]]={'q':q,'d':(e.get('descriptions',{}).get('de') or e.get('descriptions',{}).get('en') or {}).get('value'),
        'b':b,'dy':dth,'bp':PL.get(bp['id']) if bp else None,'dp':PL.get(dp['id']) if dp else None,
        'img':img,'wp':wp,'x':AX.get(wp) if wp else None}
# Plausibilität: bei mindestens der Hälfte der Denkmäler muss eine im Text genannte Jahreszahl
# in die Schaffenszeit fallen (18 Jahre nach Geburt bis Tod bzw. +90)
texts=collections.defaultdict(list)
for m in dm['m']:
    ys=[int(x) for x in re.findall(r'(?<!\d)(1[2-9]\d\d|20[0-2]\d)(?!\d)',m['d'])]
    for ai in m.get('ar',[]): texts[AR[ai]].append(ys)
drop=[]
for n,a in list(arch.items()):
    if not a['b'] or not texts.get(n): continue
    lo,hi=a['b']+18,(a['dy'] or a['b']+90)
    ok=sum(1 for ys in texts[n] if any(lo<=y<=hi for y in ys))
    if ok*2<len(texts[n]): drop.append((n,a['b'],f"{ok}/{len(texts[n])}")); del arch[n]
print('verworfen (Lebensdaten passen nicht):',drop,flush=True)
json.dump(arch,open(P+'/data/architekten.json','w'),ensure_ascii=False,separators=(',',':'))
top=[AR[ai] for ai,_ in cnt.most_common(40)]
print('Details',len(arch),'mit Porträt',sum(1 for a in arch.values() if a['img']),'mit Wikipedia',sum(1 for a in arch.values() if a['wp']))
print('Top-40 abgedeckt',sum(1 for n in top if n in arch),[n for n in top if n not in arch])
