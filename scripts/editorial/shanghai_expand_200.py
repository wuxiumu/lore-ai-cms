#!/usr/bin/env python3
"""Prepare 200 Shanghai original horror topics, then generate resumable batches."""
import argparse,collections,datetime,fcntl,hashlib,json,subprocess,sys,time
from catalog import ROOT,state,emit,duplicate,risk_flags,topic_key
from model_client import call,json_result
p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');args=p.parse_args()
base=ROOT/'.local/shanghai-200';base.mkdir(exist_ok=True);lock=(base/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
pf=base/'progress.json';progress=json.loads(pf.read_text()) if pf.exists() else {'site_id':9,'target':200,'new_target':200,'baseline':0,'started_at':datetime.datetime.now().isoformat(),'status':'目录生成中','batches':[]}
def save():
 progress['updated_at']=datetime.datetime.now().isoformat();tmp=base/'progress.tmp';tmp.write_text(json.dumps(progress,ensure_ascii=False,indent=2));tmp.replace(pf)
save();current=state(9)
places={
'地铁':['人民广场','静安寺','中山公园','徐家汇','陕西南路','南京西路','虹口足球场','世纪大道','陆家嘴','龙阳路','莘庄','漕宝路','江湾镇','嘉定新城','上海体育馆','北新泾','长寿路','曹杨路','大柏树','七宝'],
'胡同':['多伦路','山阴路','甜爱路','愚园路','武康路','思南路','田子坊','老西门','新天地','衡山路','绍兴路','建国西路','安福路','永康路','天平路','复兴中路','巨鹿路','定西路','四川北路','提篮桥'],
'小区':['曹杨','凉城','曲阳','大宁','长风','北新泾','古北','梅陇','七宝','三林','张江','金桥','周浦','南翔','江桥','彭浦','中原','五角场','莘庄','桃浦'],
'公园':['苏州河','外滩','杨浦滨江','徐汇滨江','北外滩','黄浦江','静安公园','复兴公园','鲁迅公园','共青森林公园','世纪公园','中山公园','长风公园','闵行体育公园','大宁公园','襄阳公园','和平公园','顾村公园','上海植物园','前滩'],
'大学':['复旦大学','同济大学','上海交通大学','华东师范大学','上海大学','上海理工大学','上海财经大学','华东理工大学','东华大学','上海师范大学','上海海事大学','上海海洋大学','上海音乐学院','上海戏剧学院','上海外国语大学','上海工程技术大学','上海电力大学','上海应用技术大学','上海体育大学','上海第二工业大学']}
file=base/'catalog.json';data=json.loads(file.read_text()) if file.exists() else {'schema_version':1,'site_id':9,'site_name':'沪上异闻','created_at':datetime.datetime.now().isoformat(),'preferences':{'theme':current['site']['content_topic']},'items':[],'source_errors':[],'workflow':'owner-authorized-expand-to-200','notice':'新增200篇原创民间风格鬼怪故事；真实上海地名只作背景，不涉军事政治。'}
providers=json.loads((ROOT/'.local/model-providers.json').read_text());events=json.loads((base/'catalog-usage.json').read_text()) if (base/'catalog-usage.json').exists() else []
for category in places:
 while sum(x['background_category']==category for x in data['items'])<40:
  needed=min(10,40-sum(x['background_category']==category for x in data['items']));provider=providers['qwen' if len(events)%2==0 else 'glm']
  payload={'category':category,'places':places[category],'count':needed,'existing_titles':[a['title'] for a in current['articles'] if int(a['site_id'])==9]+[x['title'] for x in data['items']],'used_plots':[x['description'] for x in data['items'][-40:]],'avoid':'不能重复灯亮、旧伞、末班车鬼乘客、失物地图、父母声音、旧家书、自动全家福等已有套路。不要每篇都用亡故亲人叮嘱收尾。人物关系可为邻里、夫妻、成年兄弟姐妹、旧友、成年同学、退休街坊；恐怖为主，压迫、疑惧和余悸结尾；避免重复温情治愈。'}
  prompt='你是上海鬼怪小说的选题编辑。只输出JSON {"items":[{"place":"白名单地名","title":"18—35字含地名的原创标题","description":"80—200字完整创意，含独特怪异现象、生活矛盾、发展与结尾方向"}]}。生成指定数量，地点从白名单选择。均为原创虚构民间风格小故事，不是史料或真实传闻。以上海日常生活和熟悉地点制造可信的恐怖感，声音、气味、天气、通勤和邻里对白细节真实自然；超自然情节仍为虚构，每篇情节独立，不重复已有题目或剧情。禁止军事、政治、军政机关、军工、时政、历史政治人物、真实机构事故犯罪、学生受害、危险模仿和具体开放交通信息。只把地名作背景，具体人物店铺院落设施虚构。不要编造来源，也不要写正文。'
  
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
   x={'id':hashlib.sha256(('shanghai-expand200-v1:'+title).encode()).hexdigest()[:12],'title':title,'city':'上海','background_category':category,'background_place':place,'story_type':'fiction','description':desc,'sources':[],'selected':True,'provider':'qwen' if len(data['items'])%2==0 else 'glm','review_status':'approved','risk_reviewed':True,'duplicate_override':False,'notes':'站长授权沪上异闻累计200篇：先目录后执行，沿用上海地名背景的原创民间小故事。地名只作背景，人物、具体场所细节虚构，不伪称流传史料；禁止军政、军工、时政和历史政治人物，不指控真实个人机构，不编造事故，不写学生受害或危险行为。情节必须与旧作不同，避免反复亡故亲人、神秘信件与旧照片，人物情绪和结局多样，强烈惊悚但不血腥，以成人日常生活的细节制造真实感，不写真实案件或亲历。'}
   shadow=[{'id':z['id'],'title':z['title'],'metadata':json.dumps({'story_type':'fiction','catalog_topic_key':topic_key(z)})} for z in data['items']]
   x['duplicate']=duplicate(x,current['articles']+shadow);x['risk_flags']=risk_flags(x)
   if x['duplicate']['level']!='clear':continue
   data['items'].append(x);accepted+=1
  tmp=base/'catalog.tmp';tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.replace(file);progress['catalog_count']=len(data['items']);save();print('CATALOG '+str(len(data['items']))+'/200',flush=True)
  if accepted==0 and len(events)>70:raise SystemExit('Catalog needs manual diversity review; preserved current progress')
if not (base/'directory.json').exists():
 directory=ROOT/'catalogs/site-9'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');emit(directory,data);(ROOT/'catalogs/site-9/latest.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False));(base/'directory.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False))
progress.setdefault('catalog_finished_at',datetime.datetime.now().isoformat());progress['status']='目录完成';save()
if not args.execute:raise SystemExit(0)
progress.setdefault('article_started_at',datetime.datetime.now().isoformat());progress['status']='文章生成中';save();all_ids={x['id'] for x in data['items']}
def generated():return [a for a in state(9)['articles'] if int(a['site_id'])==9 and json.loads(a.get('metadata') or '{}').get('catalog_id') in all_ids]
for start in range(0,200,10):
 rows=data['items'][start:start+10];snap=base/f'batch-{start//10+1}.json';snap.write_text(json.dumps({**data,'items':rows},ensure_ascii=False,indent=2));batch=next((b for b in progress['batches'] if b['number']==start//10+1),None)
 if batch is None:batch={'number':start//10+1,'status':'生成中','attempts':0};progress['batches'].append(batch)
 ids={x['id'] for x in rows}
 for attempt in range(3):
  done={json.loads(a['metadata'])['catalog_id'] for a in generated()}
  if ids<=done:break
  batch['attempts']+=1;save();workers=[]
  for provider in ['qwen','glm']:
   workers.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/editorial/catalog_drafts.py'),'--site-id','9','--provider',provider,'--catalog',str(snap),'--parallel-worker','--execute','--limit','10','--daily-limit','200'],cwd=ROOT))
  codes=[w.wait() for w in workers]
 done={json.loads(a['metadata'])['catalog_id'] for a in generated()};batch['generated']=len(ids&done);batch['status']='完成' if ids<=done else '需重试';progress['generated']=len(done);save();print('PROGRESS '+str(len(done))+'/200',flush=True)
 if not ids<=done:raise SystemExit('Incomplete batch; resume existing progress')
progress['status']='生成完成';progress['finished_at']=datetime.datetime.now().isoformat();progress['generated']=len(generated());save()
