#!/usr/bin/env python3
"""Prepare 200 Chongqing original horror topics, then generate resumable batches."""
import argparse,collections,datetime,fcntl,hashlib,json,subprocess,sys,time
from catalog import ROOT,state,emit,duplicate,risk_flags,topic_key
from model_client import call,json_result
p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');args=p.parse_args()
base=ROOT/'.local/chongqing-200';base.mkdir(exist_ok=True);lock=(base/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
pf=base/'progress.json';progress=json.loads(pf.read_text()) if pf.exists() else {'site_id':10,'target':200,'new_target':200,'baseline':0,'started_at':datetime.datetime.now().isoformat(),'status':'目录生成中','batches':[]}
def save():
 progress['updated_at']=datetime.datetime.now().isoformat();tmp=base/'progress.tmp';tmp.write_text(json.dumps(progress,ensure_ascii=False,indent=2));tmp.replace(pf)
save();current=state(10)
places={
'地铁':['两路口','牛角沱','李子坝','小什字','大坪','较场口','沙坪坝','红旗河沟','观音桥','五里店','弹子石','上新街','南坪','鱼洞','杨家坪','谢家湾','石桥铺','大溪沟','曾家岩','大石坝'],
'老街':['十八梯','山城巷','白象街','下浩里','龙门浩','黄桷垭','磁器口','弹子石老街','民生路','戴家巷','中山四路','枇杷山正街','南纪门','储奇门','望龙门','慈云寺老街','菜园坝','铜元局','仁义街','盘溪'],
'小区':['大坪','石油路','谢家湾','杨家坪','南坪','四公里','江北城','五里店','红旗河沟','龙头寺','人和','冉家坝','大竹林','礼嘉','蔡家','回兴','鸳鸯','茶园','大渡口','华岩'],
'江岸':['朝天门','洪崖洞','南滨路','北滨路','江北嘴','鹅岭公园','枇杷山公园','珊瑚公园','照母山','鸿恩寺公园','重庆中央公园','龙头寺公园','彩云湖公园','华岩湖','嘉陵江','长江','九滨路','广阳岛','黄桷坪','黄葛古道'],
'大学':['重庆大学','西南大学','重庆师范大学','重庆交通大学','重庆邮电大学','重庆理工大学','重庆工商大学','重庆科技大学','四川美术学院','四川外国语大学','重庆医科大学','重庆第二师范学院','重庆三峡学院','长江师范学院','重庆文理学院','重庆人文科技学院','重庆城市科技学院','重庆工程学院','重庆财经学院','重庆对外经贸学院']}
file=base/'catalog.json';data=json.loads(file.read_text()) if file.exists() else {'schema_version':1,'site_id':10,'site_name':'山城怪谈','created_at':datetime.datetime.now().isoformat(),'preferences':{'theme':current['site']['content_topic']},'items':[],'source_errors':[],'workflow':'owner-authorized-expand-to-200','notice':'新增200篇原创民间风格鬼怪故事；真实重庆地名只作背景，不涉军事政治。'}
providers=json.loads((ROOT/'.local/model-providers.json').read_text());events=json.loads((base/'catalog-usage.json').read_text()) if (base/'catalog-usage.json').exists() else []
for category in places:
 while sum(x['background_category']==category for x in data['items'])<40:
  needed=min(10,40-sum(x['background_category']==category for x in data['items']));provider=providers['qwen' if len(events)%2==0 else 'glm']
  payload={'category':category,'places':places[category],'count':needed,'existing_titles':[a['title'] for a in current['articles'] if int(a['site_id'])==10]+[x['title'] for x in data['items']],'used_plots':[x['description'] for x in data['items']],'avoid':'不能重复灯亮、旧伞、末班车鬼乘客、失物地图、父母声音、旧家书、自动全家福等已有套路。不要每篇都用亡故亲人叮嘱收尾。人物关系可为邻里、夫妻、成年兄弟姐妹、旧友、成年同学、退休街坊；恐怖为主，压迫、疑惧和余悸结尾；避免重复温情治愈。'}
  prompt='你是重庆鬼怪小说的选题编辑。只输出JSON {"items":[{"place":"白名单地名","title":"18—35字含地名的原创标题","description":"80—200字完整创意，含独特怪异现象、生活矛盾、发展与结尾方向"}]}。生成指定数量，地点从白名单选择。均为原创虚构民间风格小故事，不是史料或真实传闻。以重庆日常生活和熟悉地点制造可信的恐怖感，雾气、江风、坡地、楼梯、方言对白和夜班生活真实自然；不编造具体交通路线、地名相邻关系或地点历史，高校标题用学校附近的虚构场所；超自然情节仍为虚构，每篇情节独立，不重复已有题目或剧情。禁止军事、政治、军政机关、军工、时政、历史政治人物、真实机构事故犯罪、学生受害、危险模仿和具体开放交通信息。只把地名作背景，具体人物店铺院落设施虚构。不要编造来源，也不要写正文。'
  
  for retry in range(3):
   try:raw,u=call(provider,prompt,payload,4500);break
   except (OSError,TimeoutError):
    if retry==2:raise
    print('Directory transport retry',retry+1,flush=True);time.sleep(3)
  events.append(u);(base/'catalog-usage.json').write_text(json.dumps(events,ensure_ascii=False,indent=2));(base/f'catalog-response-{len(events)}.txt').write_text(raw)
  try:rows=json_result(raw)['items']
  except (ValueError,KeyError):continue
  accepted=0
  for row in rows:
   title=row.get('title','');place=row.get('place','');desc=row.get('description','')
   if place not in places[category] or not isinstance(title,str) or not 5<=len(title)<=70 or not isinstance(desc,str) or len(desc)<25:continue
   if place not in title:title=place+'：'+title
   if sum(x['background_category']==category for x in data['items'])>=40:break
   x={'id':hashlib.sha256(('chongqing-expand200-v1:'+title).encode()).hexdigest()[:12],'title':title,'city':'重庆','background_category':category,'background_place':place,'story_type':'fiction','description':desc,'sources':[],'selected':True,'provider':'qwen' if len(data['items'])%2==0 else 'glm','review_status':'approved','risk_reviewed':True,'duplicate_override':False,'notes':'站长授权山城怪谈累计200篇：先目录后执行，沿用重庆地名背景的原创民间小故事。地名只作背景，人物、具体场所细节虚构，不伪称流传史料；禁止军政、军工、时政和历史政治人物，不指控真实个人机构，不编造事故，不写学生受害或危险行为。情节必须与旧作不同，避免反复亡故亲人、神秘信件与旧照片，人物情绪和结局多样，强烈惊悚但不血腥，以成人日常生活的细节制造真实感，不写真实案件或亲历。'}
   shadow=[{'id':z['id'],'title':z['title'],'metadata':json.dumps({'story_type':'fiction','catalog_topic_key':topic_key(z)})} for z in data['items']]
   x['duplicate']=duplicate(x,current['articles']+shadow);x['risk_flags']=risk_flags(x)
   if x['duplicate']['level']!='clear':continue
   data['items'].append(x);accepted+=1
  tmp=base/'catalog.tmp';tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.replace(file);progress['catalog_count']=len(data['items']);save();print('CATALOG '+str(len(data['items']))+'/200',flush=True)
  if accepted==0 and len(events)>70:raise SystemExit('Catalog needs manual diversity review; preserved current progress')
if not (base/'directory.json').exists():
 directory=ROOT/'catalogs/site-10'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');emit(directory,data);(ROOT/'catalogs/site-10/latest.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False));(base/'directory.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False))
progress.setdefault('catalog_finished_at',datetime.datetime.now().isoformat());progress['status']='目录完成';save()
if not args.execute:raise SystemExit(0)
if not (base/'premise-changes.json').exists():
 subprocess.run([sys.executable,str(ROOT/'scripts/editorial/chongqing_catalog_review.py')],cwd=ROOT,check=True)
 data=json.loads(file.read_text())
progress.setdefault('article_started_at',datetime.datetime.now().isoformat());progress['status']='文章生成中';save();all_ids={x['id'] for x in data['items']}
def generated():return [a for a in state(10)['articles'] if int(a['site_id'])==10 and json.loads(a.get('metadata') or '{}').get('catalog_id') in all_ids]
for start in range(0,200,10):
 rows=data['items'][start:start+10];snap=base/f'batch-{start//10+1}.json';snap.write_text(json.dumps({**data,'items':rows},ensure_ascii=False,indent=2));batch=next((b for b in progress['batches'] if b['number']==start//10+1),None)
 if batch is None:batch={'number':start//10+1,'status':'生成中','attempts':0};progress['batches'].append(batch)
 ids={x['id'] for x in rows}
 for attempt in range(3):
  done={json.loads(a['metadata'])['catalog_id'] for a in generated()}
  if ids<=done:break
  batch['attempts']+=1;save();workers=[]
  for provider in ['qwen','glm']:
   workers.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/editorial/catalog_drafts.py'),'--site-id','10','--provider',provider,'--catalog',str(snap),'--parallel-worker','--execute','--limit','10','--daily-limit','200'],cwd=ROOT))
  codes=[w.wait() for w in workers]
 done={json.loads(a['metadata'])['catalog_id'] for a in generated()};batch['generated']=len(ids&done);batch['status']='完成' if ids<=done else '需重试';progress['generated']=len(done);save();print('PROGRESS '+str(len(done))+'/200',flush=True)
 if not ids<=done:raise SystemExit('Incomplete batch; resume existing progress')
progress['status']='生成完成';progress['finished_at']=datetime.datetime.now().isoformat();progress['generated']=len(generated());save()
