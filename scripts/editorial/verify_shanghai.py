#!/usr/bin/env python3
"""Audit 200 Shanghai original horror stories before publication."""
import argparse,collections,datetime,hashlib,json,re,subprocess
from catalog import ROOT,topic_key
p=argparse.ArgumentParser();p.add_argument('--batch-dir',default='.local/shanghai-200');p.add_argument('--expected',type=int,default=200);args=p.parse_args();base=(ROOT/args.batch_dir).resolve();assert base.is_relative_to((ROOT/'.local').resolve());data=json.loads((base/'catalog.json').read_text());wanted={x['id']:x for x in data['items']}
code="require 'new-project/app/src/bootstrap.php';echo json_encode(query('SELECT a.*,m.metadata FROM mvp_articles a LEFT JOIN mvp_article_meta m ON m.article_id=a.id')->fetchAll(),JSON_UNESCAPED_UNICODE);"
rows=json.loads(subprocess.run(['php','-r',code],cwd=ROOT,text=True,capture_output=True,check=True).stdout);articles=[a for a in rows if int(a['site_id'])==9 and json.loads(a['metadata'] or '{}').get('catalog_id') in wanted];ids={a['id'] for a in articles}
issues=[];tokens=collections.defaultdict(lambda:{'calls':0,'input_tokens':0,'output_tokens':0,'total_tokens':0})
for a in articles:
 m=json.loads(a['metadata']);x=wanted[m['catalog_id']]
 if m.get('story_type')!='fiction' or m.get('schema_version')!=1 or m.get('sources')!=[]:issues.append({'id':a['id'],'issue':'schema/nature/sources'})
 if not isinstance(m.get('keywords'),list) or any(not isinstance(k,str) for k in m.get('keywords',[])):issues.append({'id':a['id'],'issue':'keywords must be string array'})
 if m.get('background',{}).get('place')!=x['background_place']:issues.append({'id':a['id'],'issue':'background metadata'})
 if '上海地名仅作故事背景' not in a['content'] or '原创虚构' not in a['content']:issues.append({'id':a['id'],'issue':'missing fiction labels'})
 # Verified Shanghai street name is geographic background, not a military topic.
 scope_text=(a['title']+' '+a['content']).replace('军工路','上海街道路名')
 forbidden=re.findall('军事|军队|军人|军营|军工|军区|部队|军政|政治|政党|党政|领导人|政府机关|中央机关|战争|抗战|革命|战场|士兵|军官|老兵|司令|孙中山|慈禧|乾隆|溥仪|康熙|毛泽东|周恩来|蒋介石',scope_text)
 if forbidden:issues.append({'id':a['id'],'issue':'scope keyword requires review','words':forbidden})
 if m.get('review',{}).get('approved') is not True:issues.append({'id':a['id'],'issue':'model review','details':m.get('review')})
 if len(a['content'])<400 or a['content'].count('## ')<3:issues.append({'id':a['id'],'issue':'content format'})
 if any(b['id']!=a['id'] and (b['title']==a['title'] or b['content']==a['content']) for b in rows):issues.append({'id':a['id'],'issue':'exact duplicate title/body'})
for x in data['items']:
 f=ROOT/'.local/catalog-generation'/('9-'+topic_key(x))/'usage.json'
 if f.exists():
  for u in json.loads(f.read_text()):
   t=tokens[u['model_requested']];t['calls']+=1
   for k in ['input_tokens','output_tokens','total_tokens']:t[k]+=int(u.get(k) or 0)
def grams(s):
 s=re.sub(r'\W','',s);return {s[i:i+3] for i in range(max(0,len(s)-2))}
g={a['id']:grams(a['content']) for a in rows if int(a['site_id'])==9};near=[]
for a in articles:
 for b in rows:
  if int(b['site_id'])!=9 or b['id']==a['id'] or (b['id'] in ids and b['id']>a['id']):continue
  score=len(g[a['id']]&g[b['id']])/max(1,len(g[a['id']]|g[b['id']]))
  if score>=.6:near.append({'ids':[a['id'],b['id']],'score':round(score,3)})
issues+=near
article_tokens=sum(u['total_tokens'] for u in tokens.values());catalog_tokens=0
if (base/'catalog-usage.json').exists():
 for u in json.loads((base/'catalog-usage.json').read_text()):
  t=tokens[u['model_requested']];t['calls']+=1
  for k in ['input_tokens','output_tokens','total_tokens']:t[k]+=int(u.get(k) or 0)
  catalog_tokens+=int(u.get('total_tokens') or 0)
p=json.loads((base/'progress.json').read_text());seconds=None
if p.get('finished_at'):seconds=round((datetime.datetime.fromisoformat(p['finished_at'])-datetime.datetime.fromisoformat(p['started_at'])).total_seconds(),2)
summary={'new_articles':len(articles),'categories':dict(collections.Counter(a['category'] for a in articles)),'usage':dict(tokens),'total_tokens':sum(u['total_tokens'] for u in tokens.values()),'article_tokens':article_tokens,'catalog_tokens':catalog_tokens,'seconds':seconds,'issues':issues,'articles':[{'id':a['id'],'title':a['title'],'slug':a['slug'],'status':a['status']} for a in articles]};(base/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='articles'},ensure_ascii=False,indent=2))
if len(articles)!=args.expected or issues:raise SystemExit(1)
