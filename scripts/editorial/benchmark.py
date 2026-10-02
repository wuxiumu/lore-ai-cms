#!/usr/bin/env python3
"""User-authorized 5/10 article benchmark with durable progress and measured usage."""
import datetime,json,subprocess,sys,time,fcntl
from pathlib import Path
from catalog import ROOT,state,emit,duplicate
from pipeline import store

def run():
 directory=ROOT/'.local/benchmark-200';directory.mkdir(exist_ok=True)
 lock=(directory/'run.lock').open('w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Benchmark is already running; no model called.')
 if (directory/'progress.json').exists():raise SystemExit('Existing benchmark progress retained; use its snapshots for recovery. No new run started.')
 prefs=json.loads((ROOT/'catalogs/site-2/preferences.json').read_text());prefs.update(story_types=['fiction'],feeds=[],sources=[])
 for sid in [8,9,10]:prefs['sources']+=json.loads((ROOT/'catalogs'/f'site-{sid}'/'preferences.json').read_text())['sources']
 prefs['theme']='大城市原创虚构鬼故事。每篇800—1200字，悬念与城市氛围，避免所有已写剧情和标题。背景资料仅作场景，不作为灵异事件证据。'
 pref_file=directory/'preferences.json';pref_file.write_text(json.dumps(prefs,ensure_ascii=False,indent=2));records=[]
 before=state(2);ids={a['id'] for a in before['articles']};daily=store({'action':'state','site_id':2})['today']+15
 for size in [5,10]:
  start=time.monotonic();record={'size':size,'started_at':datetime.datetime.now().isoformat(),'status':'生成目录'};records.append(record)
  def save():
   (directory/'progress.json').write_text(json.dumps({'target':200,'baseline_site_articles':sum(int(a['site_id'])==2 for a in before['articles']),'batches':records},ensure_ascii=False,indent=2))
  save();print(f'BATCH {size}: start catalog',flush=True)
  subprocess.run([sys.executable,str(ROOT/'project.py'),'catalog-model','--site-id','2','--provider','qwen','--limit',str(size),'--preferences',str(pref_file),'--execute'],cwd=ROOT,check=True)
  record['catalog_seconds']=round(time.monotonic()-start,2)
  catdir=Path(json.loads((ROOT/'catalogs/site-2/latest.json').read_text())['directory']);data=json.loads((catdir/'catalog.json').read_text());new=data['items'][-size:];snapshot={**data,'items':new}
  articles=state(2)['articles']
  for i,x in enumerate(new):
   d=duplicate(x,articles,data['items'])
   if d['level']!='clear':raise RuntimeError('Benchmark topic overlaps; stopped before article calls: '+x['title'])
   x.update(selected=True,provider='qwen' if i%2==0 else 'glm',review_status='approved',risk_reviewed=True,notes='站长授权200篇扩充前的5篇/10篇计时试跑；原创虚构，仅资料背景；生成后待站长审稿。')
  emit(catdir,data);snap=directory/f'batch-{size}.json';snap.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2));record['status']='生成正文';save();article_start=time.monotonic()
  for provider in ['qwen','glm']:
   subprocess.run([sys.executable,str(ROOT/'project.py'),'generate','--provider',provider,'--catalog',str(snap),'--execute','--limit',str(size),'--daily-limit',str(daily)],cwd=ROOT,check=True)
  result=[];usage=[data['generation']['usage']]
  current=state(2)
  for article in current['articles']:
   meta=json.loads(article.get('metadata') or '{}')
   if meta.get('catalog_id') not in {x['id'] for x in new}:continue
   result.append({'id':article['id'],'title':article['title'],'status':article['status'],'review':meta.get('review'),'model':meta['generation']['model_returned'],'provider':meta['generation']['provider']});usage+=meta['generation']['calls']
  record.update(status='完成',article_seconds=round(time.monotonic()-article_start,2),wall_seconds=round(time.monotonic()-start,2),articles=result,catalog_file=str(snap),usage=usage,input_tokens=sum(u['input_tokens'] or 0 for u in usage),output_tokens=sum(u['output_tokens'] or 0 for u in usage),total_tokens=sum(u['total_tokens'] or 0 for u in usage))
  if len(result)!=size:raise RuntimeError('Incomplete batch')
  save();print('BATCH COMPLETE '+json.dumps({k:v for k,v in record.items() if k not in ['articles','usage']},ensure_ascii=False),flush=True)
 print('BENCHMARK COMPLETE',flush=True)
if __name__=='__main__':run()
