#!/usr/bin/env python3
"""Append independent, accessible encyclopedia topics to the resumable catalog."""
import concurrent.futures,datetime,hashlib,json,urllib.parse
from catalog import ROOT,state,duplicate,risk_flags,emit
from pipeline import fetch,plain
base=ROOT/'.local/lore-200';data=json.loads((base/'catalog.json').read_text());current=state(1);known={s['url'] for x in data['items'] for s in x['sources']};cache=ROOT/'.local/source-cache'
pairs=[]
for file in ['lore_topics.txt','lore_extra_topics.txt']:
 for line in (ROOT/'scripts/editorial'/file).read_text().splitlines():
  city,names=line.split('|');pairs.extend((city,n) for n in names.split(','))
def collect(pair):
 city,name=pair;url='https://zh.wikipedia.org/wiki/'+urllib.parse.quote(name)
 if url in known:return None
 cached=cache/(hashlib.sha256(url.encode()).hexdigest()+'.txt')
 try:
  if cached.exists():text=cached.read_text()
  else:
   text=plain(fetch(url))
   if len(text)<1500 or '维基百科目前还没有' in text:raise ValueError('缺少来源')
   cached.write_text(text)
  source={'url':url,'title':name,'publisher':'维基百科（百科参考资料）','date':'','accessed_at':datetime.date.today().isoformat(),'role':'事实参考；通过注释追溯原始资料'}
  x={'id':hashlib.sha256(url.encode()).hexdigest()[:12],'title':name,'city':city,'story_type':'nonfiction','description':'整理'+name+'的沿革、空间与文化特点，以来源能够证明的具体事实为基础；不虚构人物、年代和传说。文章角度应突出这一文化实体的独特性。','sources':[source],'selected':True,'provider':'qwen','review_status':'approved','risk_reviewed':True,'duplicate_override':False,'notes':'站长授权城市拾遗累计200篇；每篇不同文化实体；发表日期不能核实则留空；生成草稿。'}
  x['risk_flags']=risk_flags(x);return x
 except Exception:return None
new=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for x in pool.map(collect,pairs):
  if not x:continue
  x['duplicate']=duplicate(x,current['articles'],data['items']+new)
  if x['duplicate']['level']=='clear':new.append(x)
# Main runner reads a snapshot; this file will be consumed on the next resume.
data['items']+=new;tmp=base/'catalog.extend.tmp';tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.replace(base/'catalog.json')
directory=__import__('pathlib').Path(json.loads((ROOT/'catalogs/site-1/latest.json').read_text())['directory']);emit(directory,data)
print(json.dumps({'added':len(new),'total_topics':len(data['items'])},ensure_ascii=False))
