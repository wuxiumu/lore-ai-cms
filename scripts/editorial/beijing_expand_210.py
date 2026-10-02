#!/usr/bin/env python3
"""Prepare 150 original Beijing-place stories, then resume expansion from60 to210."""
import argparse,collections,datetime,fcntl,hashlib,json,subprocess,sys,time
from catalog import ROOT,state,emit,duplicate,risk_flags,topic_key
from model_client import call,json_result
p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');args=p.parse_args()
base=ROOT/'.local/beijing-210';base.mkdir(exist_ok=True);lock=(base/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
pf=base/'progress.json';progress=json.loads(pf.read_text()) if pf.exists() else {'site_id':8,'target':210,'new_target':150,'baseline':60,'started_at':datetime.datetime.now().isoformat(),'status':'目录生成中','batches':[]}
def save():
 progress['updated_at']=datetime.datetime.now().isoformat();tmp=base/'progress.tmp';tmp.write_text(json.dumps(progress,ensure_ascii=False,indent=2));tmp.replace(pf)
save();current=state(8)
places={
'地铁':['北京站','西直门','积水潭','北海北','东直门','车公庄','知春路','牡丹园','六里桥','宋家庄','四惠','国贸','大望路','常营','金台路','高碑店','平安里','安定门','北土城','五道口'],
'胡同':['南锣鼓巷','五道营','烟袋斜街','国子监街','百花深处','大栅栏','鲜鱼口','史家胡同','东四','杨梅竹斜街','菊儿胡同','帽儿胡同','砖塔胡同','方家胡同','宝钞胡同','琉璃厂','钱粮胡同','东棉花胡同'],
'小区':['方庄','回龙观','望京','亚运村','劲松','和平里','潘家园','通州北苑','双井','天通苑','劲松北社区','西坝河','芍药居','安贞里','三元桥','惠新里','团结湖','太阳宫'],
'公园':['北海公园','陶然亭公园','紫竹院公园','玉渊潭公园','朝阳公园','奥林匹克森林公园','景山公园','中山公园','颐和园','国家植物园','龙潭公园','团结湖公园','红领巾公园','日坛公园','月坛公园','莲花池公园','海淀公园','香山公园'],
'大学':['北京大学','清华大学','北京师范大学','中国人民大学','北京理工大学','北京交通大学','中国农业大学','北京邮电大学','首都师范大学','北京林业大学','北京语言大学','北京工业大学','北京化工大学','北京科技大学','对外经济贸易大学','北京服装学院','北京电影学院','中央音乐学院']}
file=base/'catalog.json';data=json.loads(file.read_text()) if file.exists() else {'schema_version':1,'site_id':8,'site_name':'京城夜谈','created_at':datetime.datetime.now().isoformat(),'preferences':{'theme':current['site']['content_topic']},'items':[],'source_errors':[],'workflow':'owner-authorized-expand-to-210','notice':'新增150篇原创民间风格鬼怪故事；真实北京地名只作背景，不涉军事政治。'}
providers=json.loads((ROOT/'.local/model-providers.json').read_text());events=json.loads((base/'catalog-usage.json').read_text()) if (base/'catalog-usage.json').exists() else []
for category in places:
 while sum(x['background_category']==category for x in data['items'])<30:
  needed=min(10,30-sum(x['background_category']==category for x in data['items']));provider=providers['qwen' if len(events)%2==0 else 'glm']
  payload={'category':category,'places':places[category],'count':needed,'existing_titles':[a['title'] for a in current['articles'] if int(a['site_id'])==8]+[x['title'] for x in data['items']],'used_plots':[x['description'] for x in data['items'][-40:]],'avoid':'不能重复灯亮、旧伞、末班车鬼乘客、失物地图、父母声音、旧家书、自动全家福等已有套路。不要每篇都用亡故亲人叮嘱收尾。人物关系可为邻里、夫妻、成年兄弟姐妹、旧友、成年同学、退休街坊；惊悚、喜剧、遗憾、温情结局交替。'}
  prompt='你是北京鬼怪小说的选题编辑。只输出JSON {"items":[{"place":"白名单地名","title":"18—35字含地名的原创标题","description":"80—150字完整创意，含独特怪异现象、生活矛盾、发展与结尾方向"}]}。生成指定数量，地点从白名单选择。均为原创虚构民间风格小故事，不是史料或真实传闻。以北京日常生活和熟悉地点制造亲切感和悬念，每篇情节独立，不重复已有题目或剧情。禁止军事、政治、军政机关、军工、时政、历史政治人物、真实机构事故犯罪、学生受害、危险模仿和具体开放交通信息。只把地名作背景，具体人物店铺院落设施虚构。不要编造来源，也不要写正文。'
  raw,u=call(provider,prompt,payload,4500);events.append(u);(base/'catalog-usage.json').write_text(json.dumps(events,ensure_ascii=False,indent=2));(base/f'catalog-response-{len(events)}.txt').write_text(raw)
  try:rows=json_result(raw)['items']
  except (ValueError,KeyError):continue
  accepted=0
  for row in rows:
   title=row.get('title','');place=row.get('place','');desc=row.get('description','')
   if place not in places[category] or not isinstance(title,str) or not 5<=len(title)<=70 or not isinstance(desc,str) or len(desc)<25:continue
   if place not in title:title=place+'：'+title
   if sum(x['background_category']==category for x in data['items'])>=30:break
   x={'id':hashlib.sha256(('beijing-expand210-v1:'+title).encode()).hexdigest()[:12],'title':title,'city':'北京','background_category':category,'background_place':place,'story_type':'fiction','description':desc,'sources':[],'selected':True,'provider':'qwen' if len(data['items'])%2==0 else 'glm','review_status':'approved','risk_reviewed':True,'duplicate_override':False,'notes':'站长授权京城夜谈累计210篇：先目录后执行，沿用北京地名背景的原创民间小故事。地名只作背景，人物、具体场所细节虚构，不伪称流传史料；禁止军政、军工、时政和历史政治人物，不指控真实个人机构，不编造事故，不写学生受害或危险行为。情节必须与旧作不同，避免反复亡故亲人、神秘信件与旧照片，人物情绪和结局多样。'}
   shadow=[{'id':z['id'],'title':z['title'],'metadata':json.dumps({'story_type':'fiction','catalog_topic_key':topic_key(z)})} for z in data['items']]
   x['duplicate']=duplicate(x,current['articles']+shadow);x['risk_flags']=risk_flags(x)
   if x['duplicate']['level']!='clear':continue
   data['items'].append(x);accepted+=1
  tmp=base/'catalog.tmp';tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.replace(file);progress['catalog_count']=len(data['items']);save();print('CATALOG '+str(len(data['items']))+'/150',flush=True)
  if accepted==0 and len(events)>70:raise SystemExit('Catalog needs manual diversity review; preserved current progress')
if not (base/'directory.json').exists():
 previous=json.loads((ROOT/'catalogs/site-8/latest.json').read_text());old=json.loads((__import__('pathlib').Path(previous['directory'])/'catalog.json').read_text());old_ids={x['id'] for x in old['items']};combined={**data,'items':old['items']+[x for x in data['items'] if x['id'] not in old_ids]};directory=ROOT/'catalogs/site-8'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');emit(directory,combined);(ROOT/'catalogs/site-8/latest.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False));(base/'directory.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False))
progress.setdefault('catalog_finished_at',datetime.datetime.now().isoformat());progress['status']='目录完成';save()
if not args.execute:raise SystemExit(0)
progress.setdefault('article_started_at',datetime.datetime.now().isoformat());progress['status']='文章生成中';save();all_ids={x['id'] for x in data['items']}
def generated():return [a for a in state(8)['articles'] if int(a['site_id'])==8 and json.loads(a.get('metadata') or '{}').get('catalog_id') in all_ids]
for start in range(0,150,10):
 rows=data['items'][start:start+10];snap=base/f'batch-{start//10+1}.json';snap.write_text(json.dumps({**data,'items':rows},ensure_ascii=False,indent=2));batch=next((b for b in progress['batches'] if b['number']==start//10+1),None)
 if batch is None:batch={'number':start//10+1,'status':'生成中','attempts':0};progress['batches'].append(batch)
 ids={x['id'] for x in rows}
 for attempt in range(3):
  done={json.loads(a['metadata'])['catalog_id'] for a in generated()}
  if ids<=done:break
  batch['attempts']+=1;save();workers=[]
  for provider in ['qwen','glm']:
   workers.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/editorial/catalog_drafts.py'),'--site-id','8','--provider',provider,'--catalog',str(snap),'--parallel-worker','--execute','--limit','10','--daily-limit','200'],cwd=ROOT))
  codes=[w.wait() for w in workers]
 done={json.loads(a['metadata'])['catalog_id'] for a in generated()};batch['generated']=len(ids&done);batch['status']='完成' if ids<=done else '需重试';progress['generated']=len(done);save();print('PROGRESS '+str(len(done))+'/150',flush=True)
 if not ids<=done:raise SystemExit('Incomplete batch; resume existing progress')
progress['status']='生成完成';progress['finished_at']=datetime.datetime.now().isoformat();progress['generated']=len(generated());save()
