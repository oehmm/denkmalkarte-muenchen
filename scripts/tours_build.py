# Baut data/rundgaenge.json: Stationen, Reihenfolge, Fußweg-Geometrie (Dijkstra auf OSM-Wegen)
import json,math,re,heapq,os,collections
exec(open('scripts/tours_select.py').read().split('out={}')[0])   # Filter + score + TOURS
MI={m['i']:m for m in M}
META={
 'koenigliches':dict(t='Klenze & Gärtner: das königliche München',mode='walk',must=['3559','3560','4933','4120','2149','4106','4110'],drop=['4113','5611','4104'],
   intro='Unter König Ludwig I. (1825–1848) bauten Leo von Klenze und Friedrich von Gärtner München zur Residenzstadt aus. Der Weg führt vom Königsplatz mit Propyläen und Glyptothek über die Brienner Straße zum Odeonsplatz und dann die Ludwigstraße hinauf bis zum Siegestor. Klenze steht für den strengen Klassizismus, Gärtner für den Rundbogenstil.'),
 'altstadtkirchen':dict(t='Kirchen der Altstadt',mode='walk',must=[],drop=[],
   intro='Auf engem Raum liegen in der Altstadt Kirchen aus fünf Jahrhunderten: von der spätgotischen Frauenkirche über St. Peter, die älteste Pfarrkirche der Stadt, bis zur Jesuitenkirche St. Michael und zur spätbarocken Asamkirche, die die Brüder Asam neben ihrem Wohnhaus errichteten.'),
 'jugendstil':dict(t='Jugendstil in Schwabing und der Maxvorstadt',mode='walk',must=[],drop=[],
   intro='Der Jugendstil trägt seinen Namen nach der Münchner Zeitschrift „Jugend“, die ab 1896 erschien. Um 1900 war Schwabing das Künstlerviertel der Stadt. Die Mietshäuser dieser Jahre zeigen geschwungene Giebel, Pflanzenornamente und farbige Putzfassaden.'),
 'au':dict(t='Herbergen und Kleinhäuser in der Au',mode='walk',must=['4229'],drop=[],
   intro='Die Au am Isarufer war eine Vorstadt der Handwerker, Flößer und Tagelöhner und kam 1854 zu München. Erhalten sind niedrige Klein- und Vorstadthäuser, deren Wohnungen oft einzelnen Eigentümern gehörten. Mittelpunkt ist die Mariahilfkirche, eine der frühesten neugotischen Kirchen Deutschlands; auf dem Platz davor findet die Auer Dult statt.'),
 'pasing':dict(t='Villenkolonien in Pasing',mode='walk',must=[],drop=[],
   intro='Ab 1892 legte der Architekt August Exter in Pasing, damals noch eine eigene Gemeinde, zwei Villenkolonien an. Freistehende Villen und Doppelhäuser mit Gärten entstanden hier für das Bürgertum, das der dichten Stadt entkommen wollte. Pasing wurde erst 1938 eingemeindet.'),
 'gaertnerplatz':dict(t='Gärtnerplatz, Glockenbach & Isar',mode='walk',must=[],drop=[],
   intro='Das Gärtnerplatzviertel wurde in den 1860er Jahren als geschlossenes Stadtquartier angelegt, mit dem Theater am runden Platz als Mittelpunkt. Der Weg verbindet die Mietshäuser der Gründerzeit mit den Isarbrücken um 1900, St. Maximilian und dem Deutschen Museum auf der Museumsinsel.'),
 'gern':dict(t='Gern: die Kolonie von Heilmann & Littmann',mode='walk',must=[],drop=[],
   intro='Ab 1892 bebaute die Baufirma Heilmann & Littmann in Gern ein ganzes Viertel mit Villen, Doppel- und Reihenhäusern. Die Denkmalliste nennt die Kolonie den Beginn des Münchner Reihenhausbaus. Die Häuser verbinden malerische Giebel und Türmchen mit wirtschaftlichen Grundrissen.'),
 'fischer':dict(t='Theodor Fischer: Schulen, Kirchen, Brücken',mode='bike',must=[],drop=[],
   intro='Theodor Fischer leitete ab 1893 das Münchner Stadterweiterungsbüro und prägte die wachsende Stadt wie kein zweiter Architekt: mit Schulhäusern, Kirchen, Brücken und Wohnbauten. Seine Bauten liegen verstreut, deshalb ist diese Tour für das Fahrrad gedacht.'),
 'lehel':dict(t='Lehel, Maximilianstraße & Praterinsel',mode='walk',must=[],drop=[],
   intro='König Maximilian II. ließ ab 1852 die Maximilianstraße in einem eigenen Stil anlegen, dem Maximilianstil. Das Lehel dahinter entwickelte sich zum bürgerlichen Wohnviertel. Der Weg führt über das Forum der Maximilianstraße und das Bayerische Nationalmuseum zur Praterinsel mitten in der Isar.'),
}
# ---- graph ----
def load(f):
    p='raw/osm/'+f
    try: return json.load(open(p))['elements']
    except Exception: print('übersprungen:',f); return []
K=math.cos(math.radians(48.14))
adj=collections.defaultdict(list); nodes={}
def key(p): return (round(p['lon'],7),round(p['lat'],7))
cnt=0
for e in load('roads.json')+load('paths.json'):
    g=e.get('geometry'); 
    if not g: continue
    hw=e.get('tags',{}).get('highway','')
    if hw in ('motorway','motorway_link','trunk','trunk_link'): continue
    pen=1.0 if hw in('footway','path','pedestrian','living_street','steps','track','cycleway') else (1.15 if hw in('residential','service','unclassified') else 1.35)
    for a,b in zip(g,g[1:]):
        ka,kb=key(a),key(b); d=math.hypot((ka[0]-kb[0])*K*111200,(ka[1]-kb[1])*111200)
        adj[ka].append((kb,d,d*pen)); adj[kb].append((ka,d,d*pen)); cnt+=1
print('edges',cnt,'nodes',len(adj))
NK=list(adj.keys())
grid=collections.defaultdict(list)
for k in NK: grid[(int(k[0]*400),int(k[1]*600))].append(k)
def nearest(x,y):
    best=None;bd=1e9
    for dx in(-1,0,1):
        for dy in(-1,0,1):
            for k in grid[(int(x*400)+dx,int(y*600)+dy)]:
                d=math.hypot((k[0]-x)*K*111200,(k[1]-y)*111200)
                if d<bd: bd=d;best=k
    return best
def route(s,t):
    dist={s:0};prev={};h=[(0,s)];tx,ty=t
    while h:
        c,u=heapq.heappop(h)
        if u==t: break
        if c>dist.get(u,1e18): continue
        for v,dl,w in adj[u]:
            nc=c+w
            if nc<dist.get(v,1e18): dist[v]=nc;prev[v]=u;heapq.heappush(h,(nc,v))
    if t not in prev and s!=t: return None,0
    path=[t]
    while path[-1]!=s: path.append(prev[path[-1]])
    path=path[::-1]; L=sum(math.hypot((a[0]-b[0])*K*111200,(a[1]-b[1])*111200) for a,b in zip(path,path[1:]))
    return path,L
def dp(pts,eps=3/111200):
    if len(pts)<3: return pts
    keep=[0,len(pts)-1];st=[(0,len(pts)-1)]
    while st:
        a,b=st.pop();ax,ay=pts[a][0]*K,pts[a][1];bx,by=pts[b][0]*K,pts[b][1];dx,dy=bx-ax,by-ay;L2=dx*dx+dy*dy or 1e-18;mi=-1;md=eps
        for i in range(a+1,b):
            px,py=pts[i][0]*K,pts[i][1];t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2));d=math.hypot(px-ax-t*dx,py-ay-t*dy)
            if d>md: md=d;mi=i
        if mi>=0: keep.append(mi);st+=[(a,mi),(mi,b)]
    return [pts[i] for i in sorted(keep)]
def dm(a,b): return math.hypot((a['x']-b['x'])*74400,(a['z']-b['z'])*111200)
def order(stops):
    # open path: try each start, nearest neighbour, then 2-opt
    best=None
    for s in range(len(stops)):
        rest=stops[:s]+stops[s+1:];p=[stops[s]]
        while rest: n=min(rest,key=lambda m:dm(p[-1],m));p.append(n);rest.remove(n)
        imp=True
        while imp:
            imp=False
            for i in range(1,len(p)-1):
                for j in range(i+1,len(p)):
                    a,b=p[i-1],p[i];c=p[j];d=p[j+1] if j+1<len(p) else None
                    old=dm(a,b)+(dm(c,d) if d else 0);new=dm(a,c)+(dm(b,d) if d else 0)
                    if new<old-1: p[i:j+1]=p[i:j+1][::-1];imp=True
        L=sum(dm(a,b) for a,b in zip(p,p[1:]))
        if best is None or L<best[0]: best=(L,p)
    return best[1]
out=[]
for k,t in TOURS.items():
    meta=META[k]; seed={'x':t['seed'][0],'z':t['seed'][1]}
    cand=[m for m in M if t['f'](m) and dist(m,seed)<=t['r'] and m['i'] not in meta['drop']]
    cand.sort(key=lambda m:-score(m))
    pick=[MI[i] for i in meta['must']]
    for m in cand:
        if len(pick)>=t['n']: break
        if all(dist(m,p)>=t['sp'] for p in pick): pick.append(m)
    pick=order(pick)
    geom=[];L=0
    for a,b in zip(pick,pick[1:]):
        na,nb=nearest(a['x'],a['z']),nearest(b['x'],b['z'])
        p,l=route(na,nb) if na and nb else (None,0)
        if not p: p=[(a['x'],a['z']),(b['x'],b['z'])];l=dm(a,b)
        seg=dp([(a['x'],a['z'])]+p+[(b['x'],b['z'])])
        geom.append([v for x,y in seg for v in (round(x,5),round(y,5))]);L+=l
    speed=4.5 if meta['mode']=='walk' else 14
    mins=L/1000/speed*60+len(pick)*(4 if meta['mode']=='walk' else 5)
    out.append({'id':k,'t':meta['t'],'mode':meta['mode'],'intro':meta['intro'],'stops':[p['i'] for p in pick],'geom':geom,'km':round(L/1000,1),'min':int(round(mins/5)*5)})
    print(f"{k}: {len(pick)} Stationen, {L/1000:.1f} km, ~{mins:.0f} min |", ' → '.join(p['t'][:18] for p in pick))
json.dump(out,open('data/rundgaenge.json','w'),ensure_ascii=False,separators=(',',':'))
