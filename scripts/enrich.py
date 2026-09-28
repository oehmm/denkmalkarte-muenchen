# Ergänzt denkmaeler.json um Architekten ('ar') und Baustile ('s')
import json,re,collections,os
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(open(P+'/data/denkmaeler.json'))
PART={'von','van','de','der','zu','du'}
TOK=r'(?:[A-ZÄÖÜ][\wäöüß\-]*\.?|von|van|de|der|zu|du)'
RX=re.compile(r'\b(?:von|Architekt(?:en)?|Baumeister|Bildhauer|Entwurf|Entwürfen|Plänen|Gebrüder(?:n)?)\s+('+TOK+r'(?:\s+'+TOK+r')*(?:\s+(?:und|&)\s+'+TOK+r'(?:\s+'+TOK+r')*)*)')
BAD=re.compile(r'(straße|platz|haus|kirche|bau|hof|garten|park|münchen|bayern|nr\.?|süden|norden|osten|westen|anfang|mitte|ende|jahrhundert|stadt|staat|gemeinde|firma|verein|landeshauptstadt)$',re.I)
FIRMS={'heilmann und littmann':'Heilmann & Littmann','heilmann & littmann':'Heilmann & Littmann'}
def names(t):
    out=[]
    for m in RX.finditer(t):
        s=re.split(r'\.\s',m.group(1).strip())[0]
        pre=t[max(0,m.start()-12):m.start()+len('Gebrüdern')+1]
        if s.lower() in FIRMS: out.append(FIRMS[s.lower()]); continue
        for part in re.split(r'\s+(?:und|&)\s+',s):
            toks=part.split()
            while toks and toks[0] in PART: toks=toks[1:]
            while toks and toks[-1] in PART: toks=toks[:-1]
            if 'Gebrüder' in m.group(0)[:10] and len(toks)==1: out.append('Gebrüder '+toks[0]); continue
            toks=[x.rstrip('.') if len(x)>2 else x for x in toks]
            while toks and toks[0] in ('Baumeister','Architekt','Bildhauer','Kruzifix','Hofbaumeister','Stadtbaurat','Oberbaurat','Professor','Prof.','Dr.','Bissing','Maler'): toks=toks[1:]
            for j,x in enumerate(toks):
                if j>0 and toks[j-1] in ('zu',) and x[0].isupper() and len(toks)-j==1 and x.endswith(('ungen','en')): toks=toks[:j-1]; break
            while toks and toks[0] in PART: toks=toks[1:]
            core=[x for x in toks if x not in PART]
            if len(core)<2 or len(toks)>5: continue
            if any(BAD.search(x) for x in core): continue
            if toks[0].endswith('.') and len(toks[0])>3: continue  # "Ehem." etc.
            out.append(' '.join(toks))
    return list(dict.fromkeys(out))
STY=[
 ('Gotik',r'\b(spät|früh)?gotisch|\bGotik'),
 ('Renaissance',r'(?<![Nn]eu)(?<!-)\brenaissance|\bRenaissance(?!-)'),
 ('Barock',r'(?<![Nn]eu)(?<!-)\b(spät|früh|hoch)?barock|(?<!Neu)(?<!neu)\bBarock'),
 ('Rokoko',r'rokoko'),
 ('Klassizismus',r'(?<![Nn]eu)(?<!neo)(?<!-)\b(spät|früh)?klassizisti|\bKlassizismus'),
 ('Biedermeier',r'biedermeier'),
 ('Romantischer Historismus / Maximilianstil',r'maximilianstil|romantisch-historis'),
 ('Rundbogenstil',r'rundbogenstil'),
 ('Neuromanik',r'neuromanisch|neoromanisch|Neuromanik'),
 ('Neugotik',r'neugotisch|neogotisch|Neugotik'),
 ('Neurenaissance',r'neurenaissance|neorenaissance|Neurenaissance'),
 ('Neubarock',r'neubarock|neobarock|Neubarock'),
 ('Neurokoko',r'neurokoko'),
 ('Neuklassizismus',r'neuklassizisti|neoklassizisti|Neuklassizismus|Neoklassizismus'),
 ('Historismus',r'historisti|historisier|Historismus'),
 ('Jugendstil',r'jugendstil'),
 ('Reformstil',r'reformstil|reformarchitektur|Reformbau'),
 ('Heimatstil',r'heimatstil|heimatschutz'),
 ('Art déco',r'art d[ée]co'),
 ('Expressionismus',r'expressionisti'),
 ('Neue Sachlichkeit / Moderne',r'neue[nr]? sachlichkeit|neuen bauens|bauhaus|klassischen moderne'),
 ('Nachkriegsmoderne',r'nachkriegsmoderne|nachkriegsarchitektur|stil der 1950er|stil der fünfziger'),
]
STYRX=[(n,re.compile(r,re.I)) for n,r in STY]
A=collections.Counter(); S=collections.Counter()
for m in d['m']+d['e']:
    m['_ar']=names(m['d']); A.update(m['_ar'])
    st=[n for n,r in STYRX if r.search(m['d'])]
    y=m.get('y')
    if y:  # historische Stilnamen bei Bauten des Historismus = Neo-Stil
        for old,new,lim in (('Barock','Neubarock',1830),('Renaissance','Neurenaissance',1820),('Gotik','Neugotik',1800),('Rokoko','Neurokoko',1830),('Klassizismus','Neuklassizismus',1880)):
            if old in st and y>=lim: st=[new if x==old else x for x in st]
    m['_s']=list(dict.fromkeys(st)); S.update(m['_s'])
AL=[a for a,_ in A.most_common()]; AI={a:i for i,a in enumerate(AL)}
SL=[n for n,_ in STY if S[n]>=3]; SI={n:i for i,n in enumerate(SL)}
for m in d['m']+d['e']:
    ar=m.pop('_ar'); s=m.pop('_s')
    if ar: m['ar']=[AI[a] for a in ar]
    elif 'ar' in m: del m['ar']
    s=[x for x in s if x in SI]
    if s: m['s']=[SI[x] for x in s]
    elif 's' in m: del m['s']
d['A']=AL; d['S']=SL
json.dump(d,open(P+'/data/denkmaeler.json','w'),separators=(',',':'),ensure_ascii=False)
print(len(AL),'Architekten/Künstler;', sum(1 for m in d['m'] if 'ar' in m),'Denkmäler mit Namen')
print(A.most_common(25)); print(S.most_common())
print([a for a in AL if len(a.split())>3][:30])
