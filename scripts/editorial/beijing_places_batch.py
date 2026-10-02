#!/usr/bin/env python3
"""Prepare a 50-place catalog first, then resume Beijing fictional-story generation."""
import argparse,collections,datetime,fcntl,hashlib,json,subprocess,sys
from catalog import ROOT,state,emit,duplicate,risk_flags,topic_key
p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');args=p.parse_args()
base=ROOT/'.local/beijing-places-50';base.mkdir(exist_ok=True);lock=(base/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
file=base/'catalog.json';current=state(8)
if not file.exists():
 raw=json.loads((ROOT/'scripts/editorial/beijing_places_50.json').read_text());assert len(raw)==50;items=[]
 for i,(category,place,title,description) in enumerate(raw):
  x={'id':hashlib.sha256(('beijing-places-50-v1:'+title).encode()).hexdigest()[:12],'title':title,'city':'北京','background_category':category,'background_place':place,'story_type':'fiction','description':description,'sources':[],'selected':True,'provider':'qwen' if i%2==0 else 'glm','review_status':'approved','risk_reviewed':True,'duplicate_override':False,'notes':'站长授权先目录后执行，北京知名地点背景50篇原创民间风格鬼怪小故事；地方为背景，真实院落、店铺、具体设施不可捏造。亲情、邻里、怀旧，有悬念，有生活细节，结尾有余味。禁止军事、政治、军政机关、时政、历史政治人物、军工内容；不得写真实个人机构事故犯罪及灵异传闻。若没有可核验传说出处，明确原创虚构，不称真实流传故事。不得擅入闭园、宿舍或封闭设施，不编造开放时间和交通信息。'}
  x['duplicate']=duplicate(x,current['articles'],items);x['risk_flags']=risk_flags(x)
  if x['duplicate']['level']!='clear':raise RuntimeError('Unresolved duplicate '+title)
  items.append(x)
 data={'schema_version':1,'site_id':8,'site_name':'京城夜谈','created_at':datetime.datetime.now().isoformat(),'preferences':{'theme':current['site']['content_topic']},'items':items,'source_errors':[],'workflow':'owner-authorized-beijing-places-fiction','notice':'真实地名只作背景；本批均原创虚构，不冒称民间流传史料。军事与政治题材排除。'}
 file.write_text(json.dumps(data,ensure_ascii=False,indent=2));directory=ROOT/'catalogs/site-8'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');emit(directory,data);(ROOT/'catalogs/site-8/latest.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False));(base/'directory.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False))
data=json.loads(file.read_text());print(json.dumps({'catalog':str(file),'items':len(data['items']),'categories':dict(collections.Counter(x['background_category'] for x in data['items'])),'mode':'execute' if args.execute else 'catalog-only'},ensure_ascii=False),flush=True)
if not args.execute:raise SystemExit(0)
pf=base/'progress.json';progress=json.loads(pf.read_text()) if pf.exists() else {'site_id':8,'target':50,'started_at':datetime.datetime.now().isoformat(),'status':'生成中','batches':[]}
def save():
 progress['updated_at']=datetime.datetime.now().isoformat();temp=base/'progress.tmp';temp.write_text(json.dumps(progress,ensure_ascii=False,indent=2));temp.replace(pf)
all_ids={x['id'] for x in data['items']}
def generated():return [a for a in state(8)['articles'] if int(a['site_id'])==8 and json.loads(a.get('metadata') or '{}').get('catalog_id') in all_ids]
for start in range(0,50,10):
 rows=data['items'][start:start+10];snap=base/f'batch-{start//10+1}.json';snap.write_text(json.dumps({**data,'items':rows},ensure_ascii=False,indent=2));batch=next((b for b in progress['batches'] if b['number']==start//10+1),None)
 if batch is None:batch={'number':start//10+1,'status':'生成中','attempts':0};progress['batches'].append(batch)
 ids={x['id'] for x in rows}
 for attempt in range(3):
  done={json.loads(a['metadata'])['catalog_id'] for a in generated()}
  if ids<=done:break
  batch['attempts']+=1;save();workers=[]
  for provider in ['qwen','glm']:
   workers.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/editorial/catalog_drafts.py'),'--site-id','8','--provider',provider,'--catalog',str(snap),'--parallel-worker','--execute','--limit','10','--daily-limit','100'],cwd=ROOT))
  codes=[w.wait() for w in workers]
 done={json.loads(a['metadata'])['catalog_id'] for a in generated()};batch['generated']=len(ids&done);batch['status']='完成' if ids<=done else '需重试';progress['generated']=len(done);save();print('PROGRESS '+str(len(done))+'/50',flush=True)
 if not ids<=done:raise SystemExit('Batch incomplete; safely resume with --execute')
progress['status']='生成完成';progress['finished_at']=datetime.datetime.now().isoformat();progress['generated']=len(generated());save()
