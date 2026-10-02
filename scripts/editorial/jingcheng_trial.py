#!/usr/bin/env python3
"""Prepare and generate ten distinct Beijing fictional ghost stories for site8."""
import datetime,json,hashlib,subprocess,sys
from catalog import ROOT,state,emit,duplicate,risk_flags
base=ROOT/'.local/jingcheng-10';base.mkdir(exist_ok=True)
topics=[
('胡同口的声控灯，只认已经搬走的人','老胡同里的声控灯只在某个声音响起时亮起，主角发现那句问候来自一位多年前搬走的邻居。用邻里细节铺悬念，结尾回到一句家常话。'),
('末班公交到了终点，有个乘客还没下车','虚构公交线路，不使用真实事故和运营方。司机发现后排乘客只在后视镜中可见，但留下的旧车票指向另一段记忆。不要仿写北京375路传闻。'),
('北京雨夜，出租车后座多出一把旧伞','匿名虚构出租车司机收到一把无人认领的伞，每逢下雨，车载收音机就播报同一条失物信息。以物件和选择推进，不写跳车逃生。'),
('四合院的空屋，每晚有人摆好两副碗筷','虚构院落，合租年轻人发现封闭空屋里的餐桌每晚变化。围绕等待与家人记忆，门内真相保留余味。'),
('凌晨两点，老楼电梯把我送到了不存在的六层','虚构普通住宅楼。主角认识楼中每位邻居，却在不存在的楼层听到自己小时候的乳名。避免危险逃生示范。'),
('胡同里的修鞋摊，天黑后不收活人的钱','虚构摊主与街道。新搬来的住户发现夜间鞋底带来不同年份的泥，修鞋摊的规矩与一桩失约有关。不能指控真实商家。'),
('冬夜的护城河边，有人替我喊了一声名字','虚构河岸小路。主角追寻幼时玩伴留下的录音，河边的回应总比自己早一秒。夜色与冰冷氛围为主，不写涉水攀爬。'),
('旧书里夹着一张北京地图，标出了我明天的路','旧书摊买来的手绘地图每天多一笔，主角发现路线终点总是同一扇未开过的门。以选择与悬念收束，不加伪造史料。'),
('夜班保安的对讲机，接到了十年前自己的声音','虚构写字楼。新保安接到声音与自己相同的指令，双方记忆却不一致；围绕一次未说出口的道歉展开。'),
('腊月送到家的快递，收件人是我姥姥的小名','虚构普通北京家庭，包裹寄件日期空白，内含一件旧毛衣和一封没有署名的信。通过家庭细节制造惊悚与温情，结尾不把亲历当真实。')]
file=base/'catalog.json'
if not file.exists():
 s=state(8);items=[]
 for i,(title,desc) in enumerate(topics):
  x={'id':hashlib.sha256(('jingcheng-trial-v1:'+title).encode()).hexdigest()[:12],'title':title,'city':'北京','story_type':'fiction','description':desc,'sources':[],'selected':True,'provider':'qwen' if i%2==0 else 'glm','review_status':'approved','risk_reviewed':True,'duplicate_override':False,'notes':'站长授权北京鬼故事首批10篇。无外部出处的原创虚构，禁止捏造亲历或真实个人机构事故。正文900—1300字，至少3个小标题，以具体生活细节、逐层悬念、结尾回响吸引读者。'}
  x['duplicate']=duplicate(x,s['articles'],items);x['risk_flags']=risk_flags(x)
  if x['duplicate']['level']!='clear':raise RuntimeError('Duplicate topic: '+title)
  items.append(x)
 data={'schema_version':1,'site_id':8,'site_name':'京城夜谈','created_at':datetime.datetime.now().isoformat(),'preferences':{'theme':s['site']['content_topic']},'items':items,'source_errors':[],'workflow':'owner-authorized-original-fiction-trial'}
 file.write_text(json.dumps(data,ensure_ascii=False,indent=2));directory=ROOT/'catalogs/site-8'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');emit(directory,data);(ROOT/'catalogs/site-8/latest.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False))
progress={'site_id':8,'status':'生成中','started_at':datetime.datetime.now().isoformat(),'target':10}
(base/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2))
workers=[]
for provider in ['qwen','glm']:
 workers.append(subprocess.Popen([sys.executable,str(ROOT/'scripts/editorial/catalog_drafts.py'),'--site-id','8','--provider',provider,'--catalog',str(file),'--parallel-worker','--execute','--limit','10','--daily-limit','20'],cwd=ROOT))
codes=[w.wait() for w in workers];items=json.loads(file.read_text())['items'];ids={x['id'] for x in items};articles=[a for a in state(8)['articles'] if int(a['site_id'])==8 and json.loads(a.get('metadata') or '{}').get('catalog_id') in ids];progress.update(status='生成完成' if len(articles)==10 else '需重试',generated=len(articles),finished_at=datetime.datetime.now().isoformat(),articles=[{'id':a['id'],'title':a['title']} for a in articles]);(base/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2));print(json.dumps(progress,ensure_ascii=False,indent=2))
if len(articles)!=10:raise SystemExit(1)
