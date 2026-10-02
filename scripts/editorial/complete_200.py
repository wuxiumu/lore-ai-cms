#!/usr/bin/env python3
"""Resume authorized expansion to 200, publish all approved content, build static ZIP."""
from pathlib import Path
import datetime,json,time,subprocess,sys,fcntl
from catalog import ROOT,state,emit,duplicate

def main():
 base=ROOT/'.local/complete-200';base.mkdir(exist_ok=True);lock=(base/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 progress_file=base/'progress.json';progress=json.loads(progress_file.read_text()) if progress_file.exists() else {'target':200,'started_at':datetime.datetime.now().isoformat(),'status':'执行中','batches':[]}
 def save():
  progress['updated_at']=datetime.datetime.now().isoformat();tmp=base/'progress.tmp';tmp.write_text(json.dumps(progress,ensure_ascii=False,indent=2));tmp.replace(progress_file)
 def cli(*args):return subprocess.run([sys.executable,str(ROOT/'project.py'),*args],cwd=ROOT).returncode
 prefs=json.loads((ROOT/'.local/benchmark-200/preferences.json').read_text())
 # Broader city settings; these are fictional story backgrounds, not event evidence.
 seeds=json.loads((ROOT/'scripts/editorial/catalog-seeds.json').read_text());sources=prefs['sources'][:]
 for seed in seeds:
  for source in seed['sources']:
   if source['url'] not in {x['url'] for x in sources}:
    source=dict(source)
    if source['url'].startswith('https://sc.people.com.cn/'):source['fetch_url']=source['url'].replace('https://','http://',1)
    sources.append(source)
 prefs['sources']=sources[:12];prefs['theme']='原创虚构城市悬疑鬼故事。题材需多样：失物、老书店、电台、雨夜窗户、门牌、地下通道、旧相机、旅店、夜班、街巷记忆、信件、异常时间。避免重复列车/扶梯/时刻表套路，禁止指控真实个人和商家。匿名虚构人物与具体场所。来源仅作城市文化背景。每篇800—1200中文字。'
 pref=base/'preferences.json';pref.write_text(json.dumps(prefs,ensure_ascii=False,indent=2));save()
 while True:
  articles=state(2)['articles'];effective=[a for a in articles if int(a['site_id'])==2 and a['id']!=2];progress['effective_articles']=len(effective);save()
  if len(effective)>=200:break
  batch=next((b for b in progress['batches'] if b['status']!='完成' and b.get('catalog_file')),None)
  if not batch:
   size=min(10,200-len(effective));index=len(progress['batches'])+1;started=time.monotonic()
   if cli('catalog-model','--site-id','2','--provider','qwen' if index%2 else 'glm','--limit',str(size),'--preferences',str(pref),'--execute'):
    progress['last_error']='目录生成失败，将再次尝试';save();time.sleep(3);continue
   directory=Path(json.loads((ROOT/'catalogs/site-2/latest.json').read_text())['directory']);data=json.loads((directory/'catalog.json').read_text());new=data['items'][-size:];selected=[]
   for i,x in enumerate(new):
    if duplicate(x,articles,data['items'])['level']!='clear':continue
    x.update(selected=True,provider='qwen' if i%2==0 else 'glm',review_status='approved',risk_reviewed=True,notes='站长授权剩余166篇全部默认通过、发布并打包；原创虚构，资料仅背景。');selected.append(x)
   emit(directory,data)
   if not selected:continue
   snap=base/f'batch-{index}.json';snap.write_text(json.dumps({**data,'items':selected},ensure_ascii=False,indent=2));batch={'number':index,'size':len(selected),'catalog_file':str(snap),'status':'生成文章','started_at':datetime.datetime.now().isoformat(),'catalog_seconds':round(time.monotonic()-started,2),'catalog_usage':data['generation']['usage'],'attempts':0};progress['batches'].append(batch);save()
  batch['attempts']+=1;save()
  for provider in ['qwen','glm']:
   cli('generate','--site-id','2','--provider',provider,'--catalog',batch['catalog_file'],'--execute','--skip-blocked','--limit','10','--daily-limit','200','--source-text-limit','2500')
  selected=json.loads(Path(batch['catalog_file']).read_text())['items'];ids={x['id'] for x in selected};current=state(2)['articles'];generated=[]
  for a in current:
   meta=json.loads(a.get('metadata') or '{}')
   if int(a['site_id'])==2 and meta.get('catalog_id') in ids:generated.append({'id':a['id'],'title':a['title']})
  batch['articles']=generated
  if len(generated)==batch['size']:batch['status']='完成';batch['finished_at']=datetime.datetime.now().isoformat()
  elif batch['attempts']>=3:
   batch['status']='完成';batch['missing_skipped']=batch['size']-len(generated);progress['last_error']='少量失败选题已记录，补充新选题直至200篇'
  save();print('PROGRESS '+json.dumps({'effective':len([a for a in current if int(a['site_id'])==2 and a['id']!=2]),'batch':batch['number'],'generated':len(generated)},ensure_ascii=False),flush=True)
 progress['status']='发布与打包';save();subprocess.run(['php',str(ROOT/'scripts/php/approve-site.php'),'2'],cwd=ROOT,check=True)
 if cli('build','--site-id','2'):raise RuntimeError('Build failed')
 progress['release']=json.loads((ROOT/'.local/releases/site-2/latest.json').read_text());progress['status']='完成';progress['finished_at']=datetime.datetime.now().isoformat();progress['effective_articles']=200;save();print('ALL200 COMPLETE',flush=True)
if __name__=='__main__':main()
