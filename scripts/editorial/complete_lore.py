#!/usr/bin/env python3
"""Resume 200 distinct, source-grounded City Lore drafts; never auto-publish."""
import concurrent.futures,datetime,fcntl,hashlib,json,re,subprocess,sys,time,urllib.parse
from pathlib import Path
from catalog import ROOT,state,emit,duplicate,risk_flags,topic_key
from pipeline import fetch,plain
BASE=ROOT/'.local/lore-200'

def main():
 BASE.mkdir(parents=True,exist_ok=True)
 lock=(BASE/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 pf=BASE/'progress.json';p=json.loads(pf.read_text()) if pf.exists() else {'site_id':1,'target':200,'started_at':datetime.datetime.now().isoformat(),'status':'收集来源','batches':[]}
 def save():
  p['updated_at']=datetime.datetime.now().isoformat();tmp=BASE/'progress.tmp';tmp.write_text(json.dumps(p,ensure_ascii=False,indent=2));tmp.replace(pf)
 save();catalog_file=BASE/'catalog.json'
 if not catalog_file.exists():
  topics=[]
  for line in (ROOT/'scripts/editorial/lore_topics.txt').read_text().splitlines():
   city,names=line.split('|');topics.extend((city,name) for name in names.split(','))
  old=state(1);cache=ROOT/'.local/source-cache';cache.mkdir(exist_ok=True);errors=[]
  def collect(pair):
   city,name=pair;url='https://zh.wikipedia.org/wiki/'+urllib.parse.quote(name)
   try:
    raw=fetch(url);text=plain(raw)
    if '维基百科目前还没有' in text or len(text)<1500:raise ValueError('来源页面不存在或内容不足')
    # Keep the encyclopedia's article body rather than navigation/language lists.
    for marker in ['出自维基百科，自由的百科全书','来自维基百科，自由的百科全书']:
     if marker in text:text=text.split(marker,1)[1];break
    if '不包含在其他语言中' in text[:1500]:raise ValueError('非正文页面')
    cached=cache/(hashlib.sha256(url.encode()).hexdigest()+'.txt');cached.write_text(text)
    source={'url':url,'title':name,'publisher':'维基百科（百科参考资料）','date':'','accessed_at':datetime.date.today().isoformat(),'role':'事实参考；可通过页面注释追溯原始资料'}
    item={'id':hashlib.sha256(url.encode()).hexdigest()[:12],'title':name+'：'+city+'的历史与地方记忆','city':city,'story_type':'nonfiction','description':'围绕'+name+'的沿革、空间特征和文化意义整理城市掌故。仅使用来源明确支持的事实，不虚构年代、人物经历或传说；区分史实与分析。','sources':[source],'selected':True,'provider':'','review_status':'approved','risk_reviewed':True,'duplicate_override':False,'notes':'站长授权城市拾遗累计200篇。来源访问日期不是发表日期，不编造来源日期；生成文章仍为草稿。每个选题对应不同文化实体。'}
    item['duplicate']=duplicate(item,old['articles']);item['risk_flags']=risk_flags(item)
    if item['duplicate']['level']!='clear':raise ValueError('与已有文章相近')
    return item,None
   except Exception as e:return None,{'topic':name,'error':type(e).__name__,'detail':str(e)[:100]}
  items=[]
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
   for item,error in pool.map(collect,topics):
    if item:items.append(item)
    if error:errors.append(error)
    p['sources_ready']=len(items);p['sources_checked']=len(items)+len(errors);save()
  # Exact-title/page URL duplicates are disallowed even within the collected set.
  unique=[];seen=set()
  for item in items:
   key=topic_key(item)
   if key in seen:continue
   item['duplicate']=duplicate(item,old['articles'],unique)
   if item['duplicate']['level']!='clear':continue
   seen.add(key);item['provider']='qwen' if len(unique)%2==0 else 'glm';unique.append(item)
  data={'schema_version':1,'site_id':1,'site_name':old['site']['name'],'created_at':datetime.datetime.now().isoformat(),'preferences':{'theme':old['site']['content_topic']},'items':unique,'source_errors':errors,'workflow':'owner-authorized-source-grounded-drafts'}
  catalog_file.write_text(json.dumps(data,ensure_ascii=False,indent=2));directory=ROOT/'catalogs/site-1'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');emit(directory,data);(ROOT/'catalogs/site-1/latest.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False));p['catalog_directory']=str(directory);p['usable_topics']=len(unique);save()
 data=json.loads(catalog_file.read_text());p['status']='生成文章';save()
 while True:
  data=json.loads(catalog_file.read_text())
  articles=state(1)['articles'];valid=[a for a in articles if int(a['site_id'])==1 and a['id']!=1];p['effective_articles']=len(valid);save()
  if len(valid)>=200:break
  done={json.loads(a.get('metadata') or '{}').get('catalog_id') for a in valid}
  exhausted={x for b in p['batches'] if b['status']=='完成' for x in b.get('item_ids',[])}
  batch=next((b for b in p['batches'] if b['status']!='完成'),None)
  if not batch:
   available=[x for x in data['items'] if x['id'] not in done|exhausted and duplicate(x,articles)['level']=='clear']
   selected=available[:min(10,200-len(valid))]
   if not selected:raise RuntimeError('来源选题不足，请补充 lore_topics.txt；已生成文章保留')
   for i,x in enumerate(selected):x['provider']='qwen' if i%2==0 else 'glm'
   n=len(p['batches'])+1;path=BASE/f'batch-{n}.json';path.write_text(json.dumps({**data,'items':selected},ensure_ascii=False,indent=2))
   batch={'number':n,'size':len(selected),'item_ids':[x['id'] for x in selected],'catalog_file':str(path),'status':'生成中','attempts':0,'started_at':datetime.datetime.now().isoformat()};p['batches'].append(batch)
  batch['attempts']+=1;save()
  subprocess.run([sys.executable,str(ROOT/'scripts/editorial/catalog_drafts.py'),'--site-id','1','--provider','qwen','--catalog',batch['catalog_file'],'--execute','--skip-blocked','--limit','10','--daily-limit','200','--source-text-limit','6000'],cwd=ROOT)
  valid=[a for a in state(1)['articles'] if int(a['site_id'])==1 and a['id']!=1];done={json.loads(a.get('metadata') or '{}').get('catalog_id') for a in valid};batch['generated']=len(done&set(batch['item_ids']));p['effective_articles']=len(valid)
  if batch['generated']==batch['size'] or batch['attempts']>=3:batch['status']='完成';batch['finished_at']=datetime.datetime.now().isoformat()
  save();print('PROGRESS '+str(len(valid))+'/200',flush=True)
 p['status']='完成';p['finished_at']=datetime.datetime.now().isoformat();p['seconds']=round((datetime.datetime.fromisoformat(p['finished_at'])-datetime.datetime.fromisoformat(p['started_at'])).total_seconds(),2);save()
 print('CITY LORE 200 DRAFTS COMPLETE',flush=True)
if __name__=='__main__':main()
