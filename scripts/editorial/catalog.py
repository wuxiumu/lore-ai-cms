#!/usr/bin/env python3
"""Collect only titles/source pointers for owner review. Never calls a model."""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,re,subprocess,urllib.parse,concurrent.futures
from pipeline import rss,similarity
ROOT=Path(__file__).resolve().parents[2]
COLUMNS=['id','selected','provider','review_status','title','story_type','city','description','source_title','source_url','source_publisher','source_date','source_role','duplicate_level','duplicate_matches','risk_flags','risk_reviewed','duplicate_override','notes']
def state(site_id):
 p=subprocess.run(['php',str(ROOT/'scripts/php/catalog-state.php'),str(site_id)],cwd=ROOT,text=True,capture_output=True,check=True);return json.loads(p.stdout)
def canonical_url(url):
 p=urllib.parse.urlsplit(url);q=urllib.parse.parse_qsl(p.query,keep_blank_values=True);q=sorted((k,v) for k,v in q if not k.lower().startswith(('utm_','spm')))
 return urllib.parse.urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/'),urllib.parse.urlencode(q),''))
def topic_key(item):
 urls=sorted(canonical_url(s['url']) for s in item['sources'])
 # Fiction ideas are distinct plots; source links are setting/background only.
 basis=('fiction:'+str(item.get('id') or re.sub(r'\W','',item['title']))) if item['story_type']=='fiction' else '|'.join(urls)
 return hashlib.sha256(basis.encode()).hexdigest()
def duplicate(item,articles,other_items=()):
 matches=[];urls={canonical_url(s['url']) for s in item['sources']};kind=item['story_type']
 for a in articles:
  meta=json.loads(a.get('metadata') or '{}');au={canonical_url(s['url']) for s in meta.get('sources',[]) if s.get('url')}
  score=similarity(item['title'],a['title'])
  same=bool(urls&au) and kind!='fiction' and meta.get('story_type')!='fiction'
  if same or score>=.42 or meta.get('catalog_topic_key')==topic_key(item):matches.append({'where':'article','id':a['id'],'title':a['title'],'reason':'相同来源或主题' if same else '标题相似/主题键相同','score':round(score,2),'exact':same or meta.get('catalog_topic_key')==topic_key(item)})
 for a in other_items:
  if a['id']==item['id']:continue
  score=similarity(item['title'],a['title']);same=topic_key(item)==topic_key(a)
  if same or score>=.55:matches.append({'where':'catalog','id':a['id'],'title':a['title'],'reason':'候选内主题相同' if same else '候选标题相近','score':round(score,2),'exact':same})
 return {'level':'duplicate' if any(m['exact'] for m in matches) else ('similar' if matches else 'clear'),'matches':matches}
def risk_flags(item):
 text=item['title']+' '+item.get('description','');flags=[]
 if item['story_type']=='fiction':flags.append('原创虚构：必须标注鬼故事/虚构，来源仅作背景')
 if item['story_type']=='folklore':flags.append('民间传说：不能当成真实事件')
 for label,words in [('真实人物隐私或指控需核验',['出轨','私生活','爆料','丑闻','绯闻','隐私','被指','指控']),('暴力/未成年人/危险模仿需复核',['杀人','血腥','自杀','虐待','儿童','未成年','跳水']),('传闻或超自然断言需区分事实',['网传','灵异','闹鬼','鬼故事','诅咒','锁龙','怪谈'])]:
  if any(w in text for w in words):flags.append(label)
 if not item.get('description'):flags.append('描述信息不足')
 if any(not s.get('date') for s in item['sources']):flags.append('来源日期待核实')
 if any(urllib.parse.urlsplit(s['url']).scheme not in ('http','https') for s in item['sources']):flags.append('来源地址无效')
 return list(dict.fromkeys(flags))
def emit(directory,data):
 directory.mkdir(parents=True,exist_ok=True)
 temp=directory/'catalog.tmp';temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));temp.replace(directory/'catalog.json')
 with (directory/'catalog.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader()
  for x in data['items']:
   source=x['sources'][0] if x['sources'] else {'title':'原创虚构，无外部出处','url':'','publisher':'本站','date':'','role':'原创故事'};row={k:x.get(k,'') for k in COLUMNS};row.update(source_title=source['title'],source_url=source['url'],source_publisher=source['publisher'],source_date=source.get('date',''),source_role=source.get('role','事实来源'),duplicate_level=x['duplicate']['level'],duplicate_matches='；'.join(m['title'] for m in x['duplicate']['matches']),risk_flags='；'.join(x['risk_flags']));w.writerow({k:("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v) for k,v in row.items()})
 lines=['# 候选标题与来源目录','',f"站点：{data['site_name']}；偏好：{data['preferences']['theme']}",'所有条目默认待审，CSV 用于查看；生成以 catalog.json 的明确选择为准。','']
 for x in data['items']:
  lines += [f"## {x['id']} · {x['title']}",f"性质：{x['story_type']}；城市：{x.get('city','')}；重复：{x['duplicate']['level']}",x.get('description',''),f"需复核：{'；'.join(x['risk_flags']) or '未命中关键词规则，仍需自行阅读来源'}"]
  lines += [f"- [{s['publisher']}｜{s['title']}]({s['url']}) · {s.get('date','日期待核实')} · {s.get('role','事实来源')}" for s in x['sources']];lines.append('')
 (directory/'README.md').write_text('\n\n'.join(lines))
def main():
 import sys
 if len(sys.argv)==3 and sys.argv[1]=='--refresh':
  directory=Path(sys.argv[2]).resolve();data=json.loads((directory/'catalog.json').read_text());s=state(data['site_id'])
  for x in data['items']:x['duplicate']=duplicate(x,s['articles'],data['items']);x['risk_flags']=risk_flags(x)
  emit(directory,data);return
 p=argparse.ArgumentParser();p.add_argument('--site-id',type=int,default=2);p.add_argument('--limit',type=int,default=30);p.add_argument('--preferences');p.add_argument('--no-feeds',action='store_true');args=p.parse_args()
 base=ROOT/'catalogs'/f'site-{args.site_id}';base.mkdir(exist_ok=True)
 prefs_path=Path(args.preferences) if args.preferences else base/'preferences.json'
 if not prefs_path.exists():prefs_path.write_text((ROOT/'scripts/editorial/preferences.example.json').read_text())
 prefs=json.loads(prefs_path.read_text());s=state(args.site_id);raw=json.loads((ROOT/'scripts/editorial/catalog-seeds.json').read_text());errors=[]
 if not args.no_feeds:
  def collect(feed):
   try:return rss(feed),None
   except Exception as e:return [],{'source':feed['name'],'error':type(e).__name__}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   for items,error in pool.map(collect,prefs.get('feeds',[])):
    if error:errors.append(error)
    for item in items:
     text=item['title']+' '+item['summary'];cities=[c for c in prefs['cities'] if c in text]
     if not cities or not any(k in text for k in prefs['keywords']) or any(w in text for w in prefs['exclude']):continue
     raw.append({'title':item['title'],'description':item['summary'][:260],'story_type':'nonfiction','city':cities[0],'sources':[{'title':item['title'],'url':item['url'],'publisher':item['publisher'],'date':item['date'][:10],'role':'事实来源'}]})
 seen=set();items=[]
 for x in raw:
  if len(items)>=max(1,min(args.limit,100)):break
  if any(w in x['title']+' '+x.get('description','') for w in prefs['exclude']):continue
  # Future curated seeds still obey owner cities and keywords unless fictional.
  if prefs.get('cities') and x.get('city') not in prefs['cities']:continue
  if x['story_type'] not in prefs.get('story_types',['nonfiction','folklore','fiction']):continue
  if prefs.get('keywords') and not any(w in x['title']+' '+x.get('description','') for w in prefs['keywords']):continue
  identity=topic_key(x)
  if identity in seen:continue
  seen.add(identity);x.update(id=identity[:12],selected=False,provider='',review_status='pending',risk_reviewed=False,duplicate_override=False,notes='');items.append(x)
 for x in items:x['duplicate']=duplicate(x,s['articles'],items);x['risk_flags']=risk_flags(x)
 data={'schema_version':1,'site_id':args.site_id,'site_name':s['site']['name'],'created_at':datetime.datetime.now().astimezone().isoformat(),'preferences':prefs,'items':items,'source_errors':errors,'workflow':'collect-review-draft','notice':'风险标记是线索，不是法律合规结论；请阅读来源。'}
 directory=base/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');emit(directory,data)
 (base/'latest.json').write_text(json.dumps({'directory':str(directory)},ensure_ascii=False,indent=2))
 print(json.dumps({'directory':str(directory),'candidate_count':len(items),'duplicates':sum(x['duplicate']['level']!='clear' for x in items),'selected':0,'source_errors':errors},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
