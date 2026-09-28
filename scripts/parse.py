import re, json
lines=open('d.txt',encoding='utf-8').read().split('\n')
clean=[]
for l in lines:
    if '© Bayerisches Landesamt' in l or '\f' in l and 'Seite' in l: continue
    clean.append(l.replace('\f',''))
entries=[];cur=None
idre=re.compile(r'^\s*([DE]-1-62-000-\d+)\s+(.*)$')
for l in clean:
    m=idre.match(l)
    if m:
        cur={'id':m.group(1),'lines':[m.group(2).strip()]};entries.append(cur);continue
    if cur is None: continue
    s=l.strip()
    if s: cur['lines'].append(s)
    elif cur['lines'] and cur['lines'][-1]!='': cur['lines'].append('')
out=[]
for e in entries:
    ls=[x for x in e['lines']]
    status=[]
    while ls and (ls[-1]=='' or re.fullmatch(r'nachqualifiziert|nicht nachqualifiziert|[a-zäöü ]{3,40}',ls[-1])):
        if ls[-1]: status.append(ls[-1])
        ls.pop()
    text=' '.join(x if x else '\n' for x in ls)
    text=re.sub(r'(\w)- (\w+)',lambda m:m.group(1)+'- '+m.group(2) if m.group(2) in ('und','oder','bzw','sowie','bis') else (m.group(1)+'-'+m.group(2) if m.group(2)[0].isupper() else m.group(1)+m.group(2)),text)
    text=re.sub(r'[ \t]+',' ',text).replace(' \n ','\n\n').strip()
    out.append({'id':e['id'],'text':text,'status':status})
json.dump(out,open('entries.json','w'),ensure_ascii=False)
import collections
print(len(out),collections.Counter(tuple(o['status']) for o in out).most_common(8))
for o in out[80:84]+out[3000:3003]: print(o)
