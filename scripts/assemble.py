# Baut zwei Varianten aus src.html:
#   site/  -> Artifact (claude.ai) + lokale Vorschau über serve.py (inkl. eingebetteter Commons-Vorschaubilder)
#   docs/  -> GitHub Pages / Handy-App (PWA, Fotos direkt von Commons, GPS)
import os,shutil,urllib.request,time
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
css=urllib.request.urlopen('https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css').read().decode()
s=open(P+'/src.html').read().replace('/*LEAFLET_CSS*/',css)
DATA=('denkmaeler.json','basiskarte.json','aenderungen.json','rundgaenge.json','umland.json','bodendenkmaeler.json','fotos.json')
os.makedirs(P+'/site',exist_ok=True)
open(P+'/site/denkmalkarte.html','w').write(s)
head='<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta charset="utf-8">\n'
open(P+'/site/index.html','w').write(head+s)
for f in DATA:
    if os.path.exists(P+'/data/'+f): shutil.copy(P+'/data/'+f,P+'/site/'+f)
# GitHub Pages
D=P+'/docs'; os.makedirs(D,exist_ok=True)
pwa_head=head+'''<meta name="theme-color" content="#1E272B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Denkmalkarte">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
'''
reg='''<script>if('serviceWorker' in navigator&&location.protocol==='https:'){addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));}</script>
'''
open(D+'/index.html','w').write('<!doctype html>\n<html lang="de">\n<head>\n'+pwa_head+'</head>\n<body>\n'+s+'\n'+reg+'</body>\n</html>\n')
for f in DATA:
    if os.path.exists(P+'/data/'+f): shutil.copy(P+'/data/'+f,D+'/'+f)
for f in ('manifest.webmanifest','icon.svg','icon-192.png','icon-512.png','apple-touch-icon.png'):
    shutil.copy(P+'/pwa/'+f,D+'/'+f)
open(D+'/sw.js','w').write(open(P+'/pwa/sw.js').read().replace('__VERSION__',time.strftime('%Y%m%d%H%M%S')))
open(D+'/.nojekyll','w').write('')
print('ok')
