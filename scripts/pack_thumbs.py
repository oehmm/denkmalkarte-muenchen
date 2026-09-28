# Bündelt die Commons-Vorschaubilder für das Artifact in Blöcke (je 100 Aktennummern),
# weil Artifacts keine externen Bilder laden dürfen. -> site/thumbs/index.json + sN.bin
import os,json,glob
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out=P+'/site/thumbs'; os.makedirs(out,exist_ok=True)
for f in glob.glob(out+'/*'): os.remove(f)
shards={}
for f in glob.glob(P+'/raw/thumbs/*.jpg'):
    i=os.path.basename(f)[:-4]
    if os.path.getsize(f)<500: continue
    shards.setdefault(int(i)//100,[]).append((i,open(f,'rb').read()))
idx={};total=0
for s,items in sorted(shards.items()):
    buf=bytearray()
    for i,data in sorted(items): idx[i]=[s,len(buf),len(data)]; buf+=data
    open(f'{out}/s{s}.bin','wb').write(buf); total+=len(buf)
json.dump(idx,open(out+'/index.json','w'),separators=(',',':'))
print(len(idx),'Bilder in',len(shards),'Blöcken,',round(total/1e6,1),'MB')
