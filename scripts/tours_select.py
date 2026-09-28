import json,math,re
d=json.load(open('data/denkmaeler.json')); M=d['m']; A=d['A']; S=d['S']
BZ=json.load(open('data/basiskarte.json'))['bezirke']; BN=[b['n'] for b in BZ]
ai=lambda n:A.index(n); si=lambda n:S.index(n); bi=lambda n:BN.index(n)
def dist(a,b): return math.hypot((a['x']-b['x'])*74400,(a['z']-b['z'])*111200)
def score(m):
    s={'sakral':5,'schloss':5,'oeffentlich':4,'denkmal':3,'park':3,'technik':3,'gewerbe':2,'villa':2,'laendlich':3,'wohnen':1,'sonstig':1}[m['c']]
    s+=min(len(m['d']),600)/200
    if m.get('ar'): s+=1
    if m['t'] not in('Mietshaus','Wohnhaus','Villa','Wohn- und Geschäftshaus','Kleinhaus'): s+=1.5
    return s
TOURS={
 'koenigliches':dict(f=lambda m:any(a in m.get('ar',[]) for a in (ai('Leo von Klenze'),ai('Friedrich von Gärtner'))),seed=(11.5760,48.1470),r=1600,n=11,sp=80),
 'altstadtkirchen':dict(f=lambda m:m['c']=='sakral' and m['k']==bi('Altstadt-Lehel'),seed=(11.5755,48.1372),r=1100,n=11,sp=50),
 'jugendstil':dict(f=lambda m:si('Jugendstil') in m.get('s',[]) and m['k'] in (bi('Schwabing-West'),bi('Maxvorstadt'),bi('Schwabing-Freimann')),seed=(11.5790,48.1600),r=900,n=11,sp=60),
 'au':dict(f=lambda m:m['k']==bi('Au-Haidhausen') and (m['c']=='laendlich' or re.search(r'Herberg|Kleinhaus|Vorstadthaus|Tropfhaus',m['t']+m['d'][:80])),seed=(11.5880,48.1270),r=900,n=11,sp=40),
 'pasing':dict(f=lambda m:m['k']==bi('Pasing-Obermenzing') and m['c']=='villa',seed=(11.4600,48.1470),r=900,n=11,sp=70),
 'gaertnerplatz':dict(f=lambda m:m['k']==bi('Ludwigsvorstadt-Isarvorstadt') and (m.get('y') or 0)>=1860 and (m.get('y') or 0)<=1914,seed=(11.5760,48.1310),r=700,n=11,sp=60),
 'gern':dict(f=lambda m:m['k']==bi('Neuhausen-Nymphenburg') and (ai('Heilmann & Littmann') in m.get('ar',[]) or ai('Jakob Heilmann') in m.get('ar',[]) or ai('Max Littmann') in m.get('ar',[])),seed=(11.5320,48.1620),r=900,n=11,sp=50),
 'fischer':dict(f=lambda m:ai('Theodor Fischer') in m.get('ar',[]),seed=(11.5750,48.1500),r=3500,n=10,sp=100),
 'lehel':dict(f=lambda m:m['k']==bi('Altstadt-Lehel') and m['x']>11.583 and m['c']!='sakral',seed=(11.5880,48.1400),r=700,n=11,sp=60),
}
out={}
for k,t in TOURS.items():
    seed={'x':t['seed'][0],'z':t['seed'][1]}
    cand=[m for m in M if t['f'](m) and dist(m,seed)<=t['r']]
    cand.sort(key=lambda m:-score(m)); pick=[]
    for m in cand:
        if all(dist(m,p)>=t['sp'] for p in pick): pick.append(m)
        if len(pick)>=t['n']: break
    out[k]=[p['i'] for p in pick]
    print(f"\n== {k}: {len(cand)} Kandidaten -> {len(pick)}")
    for p in pick: print('  ',p['i'],p['y'],p['t'][:50],'|',p['a'][:40])
json.dump(out,open('raw/tour_picks.json','w'))
