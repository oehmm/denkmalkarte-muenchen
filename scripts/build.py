import json,re,collections
en=json.load(open('entries.json'));W=json.load(open('einzeldenkmalO.json'));EN=json.load(open('bauensembleO.json'))
ABBR=r'(?<!\bSt)(?<!\bStr)(?<!\bNr)(?<!\bHl)(?<!\behem)(?<!\bbez)(?<!\bca)'
def split_addr(t):
    m=re.search(ABBR+r'\.\s+(?=[A-ZÄÖÜ„"(])',t)
    if not m: return '',t
    return t[:m.start()].strip(),t[m.end():].strip()
CATS=[
 ('sakral',r'kirche|kapelle|kloster|pfarrhaus|synagoge|moschee|wegkreuz|bildstock|marterl|kruzifix|mesner|stift\b|wallfahrt|kalvarienberg|kreuzweg'),
 ('schloss',r'schloss|palais|residenz|schlösschen|jagdschloss|herrenhaus|hofmark'),
 ('denkmal',r'denkmal|brunnen|skulptur|plastik|figur|statue|relief|grabmal|gedenk|säule|obelisk|bildnis|büste|mahnmal|kunstwerk'),
 ('villa',r'villa|landhaus|landsitz'),
 ('park',r'friedhof|garten|park|allee|grünanlage|anlage \(gartenkunst'),
 ('technik',r'brücke|bahnhof|wasserturm|kraftwerk|wehr|tunnel|pumpwerk|stellwerk|umspann|hafen|bahn|gleis|trafo|kanal|mühle|turm|werk\b|fabrik|brauerei|halle|gasometer|lokschuppen|flughafen'),
 ('oeffentlich',r'schule|rathaus|verwaltung|museum|theater|universität|hochschule|bibliothek|krankenhaus|klinik|kaserne|gericht|amt|ministerium|akademie|bad\b|badeanstalt|feuerwehr|polizei|post|institut|gymnasium|kindergarten|heim|stadion|sport|ausstellung|oper|konzert|kino|galerie|bibliothek|observatorium|sternwarte'),
 ('gewerbe',r'gasthaus|gaststätte|wirtshaus|hotel|geschäftshaus|kaufhaus|bank|laden|café|bräu|werkstatt|atelier|lagerhaus|stall|stadel|remise'),
 ('laendlich',r'bauernhaus|bauernhof|hof\b|austrag|tropfhaus|kleinhaus|söldnerhaus|getreidekasten|troadkasten'),
 ('wohnen',r'wohn|mietshaus|miethaus|reihenhaus|doppelhaus|vorstadthaus|bürgerhaus|handwerkerhaus|einfamilienhaus|mehrfamilienhaus|siedlung|haus\b'),
]
def cat(f,title):
    title=re.split(r',|;',title,maxsplit=1)[0]
    s=(f+' | '+title).lower()
    # function field first
    for k,rx in CATS:
        if re.search(rx,title.lower()): return k
    for k,rx in CATS:
        if f and re.search(rx,f.lower()): return k
    return 'sonstig'
def year(t):
    for m in re.finditer(r'(?<![\d/.-])(1[0-9]\d\d|20[0-2]\d)(?![\d])',t):
        y=int(m.group(1))
        if 1000<=y<=2026: return y
    return None
def title_of(desc):
    s=re.split(r',|;| – ',desc,maxsplit=1)[0].strip()
    if len(s)>90: s=s[:88].rsplit(' ',1)[0]+' …'
    return s
out=[];ens=[]
for e in en:
    t=e['text'].replace('\n\n',' ').replace('\n',' ')
    t=re.sub(r'\s+',' ',t)
    t=re.sub(r'(\w)(und|oder|bzw\.) ',r'\1\2 ',t)
    if e['id'].startswith('D'):
        w=W[e['id']]; b=json.loads(w['bbox']) if isinstance(w['bbox'],str) else w['bbox']
        addr,desc=split_addr(t)
        if not addr: addr=w.get('adresse','')
        ti=w.get('tradobjbez') or title_of(desc)
        f=w.get('funktion','')
        out.append({'i':e['id'][11:],'a':addr,'t':ti,'d':desc,'c':cat(f,desc[:160]),'y':year(desc),
          'x':round((b[0]+b[2])/2,6),'z':round((b[1]+b[3])/2,6),'b':[round(v,6) for v in b],'f':f.split(',')[0]})
    else:
        w=EN.get(e['id']);
        if not w: continue
        b=json.loads(w['bbox']) if isinstance(w['bbox'],str) else w['bbox']
        m=re.match(r'(Ensemble [^.]*?(?:\.[^.\s][^.]*?)*)\.\s',t)
        ti=m.group(1) if m else t[:60]
        ens.append({'i':e['id'][11:],'t':ti,'d':t[len(ti)+1:].strip(),'b':[round(v,6) for v in b]})
print(collections.Counter(o['c'] for o in out))
print(sum(1 for o in out if o['y'] is None),'no year')
for o in out[::900]: print(o['i'],'|',o['a'],'|',o['t'],'|',o['c'],o['y'],o['f'])
print([x['t'] for x in ens[:8]])
json.dump({'m':out,'e':ens},open('dm.json','w'),ensure_ascii=False,separators=(',',':'))
