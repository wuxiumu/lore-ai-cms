#!/usr/bin/env python3
"""Audit City Lore drafts, sources, exact duplicates, content similarity and usage."""
import collections,hashlib,json,re,subprocess,sys
from pathlib import Path
from catalog import ROOT,canonical_url
code="require 'new-project/app/src/bootstrap.php';echo json_encode(query('SELECT a.id,a.site_id,a.title,a.content,a.status,m.metadata FROM mvp_articles a LEFT JOIN mvp_article_meta m ON m.article_id=a.id ORDER BY a.id')->fetchAll(),JSON_UNESCAPED_UNICODE);"
rows=json.loads(subprocess.run(['php','-r',code],cwd=ROOT,capture_output=True,text=True,check=True).stdout)
articles=[a for a in rows if int(a['site_id'])==1 and a['id']!=1];metas=[json.loads(a['metadata'] or '{}') for a in articles]
def repeated(values):
 c=collections.Counter(values);return [v for v,n in c.items() if n>1]
issues={'titles':repeated([a['title'] for a in articles]),'bodies':repeated([hashlib.sha256(a['content'].encode()).hexdigest() for a in articles]),'topic_keys':repeated([m.get('catalog_topic_key') for m in metas]),'source_urls':repeated([canonical_url(s['url']) for m in metas for s in m['sources']])}
headings=[]
for m in metas:
 u=m['sources'][0]['url'];f=ROOT/'.local/source-cache'/(hashlib.sha256(u.encode()).hexdigest()+'.txt');headings.append(f.read_text().splitlines()[0])
issues['source_pages']=repeated(headings)
def grams(s):
 s=re.sub(r'\W','',s);return {s[i:i+3] for i in range(max(0,len(s)-2))}
g=[grams(a['content']) for a in articles];near=[]
for i in range(len(articles)):
 for j in range(i):
  score=len(g[i]&g[j])/max(1,len(g[i]|g[j]))
  if score>=.6:near.append({'ids':[articles[i]['id'],articles[j]['id']],'score':round(score,3)})
issues['similar_bodies']=near
cross_titles=[a['title'] for a in rows if int(a['site_id'])!=1];issues['cross_site_exact_titles']=[a['title'] for a in articles if a['title'] in cross_titles]
cross_hashes={hashlib.sha256(a['content'].encode()).hexdigest() for a in rows if int(a['site_id'])!=1};issues['cross_site_exact_bodies']=[a['id'] for a in articles if hashlib.sha256(a['content'].encode()).hexdigest() in cross_hashes]
usage=collections.defaultdict(lambda:{'calls':0,'input_tokens':0,'output_tokens':0,'total_tokens':0})
for trace in (ROOT/'.local/catalog-generation').glob('1-*/usage.json'):
 for x in json.loads(trace.read_text()):
  key=x.get('model_requested','unknown');d=usage[key];d['calls']+=1
  for k in ['input_tokens','output_tokens','total_tokens']:d[k]+=int(x.get(k,0))
summary={'site_id':1,'effective_articles':len(articles),'drafts':sum(a['status']=='draft' for a in articles),'published':sum(a['status']=='published' for a in articles),'unique_sources':len(set(headings)),'duplicate_issues':issues,'model_review_flags':sum(m.get('review',{}).get('approved') is not True for m in metas),'providers':dict(collections.Counter(m['generation']['provider'] for m in metas)),'usage':dict(usage),'actual_total_tokens':sum(x['total_tokens'] for x in usage.values()),'schema_versions':dict(collections.Counter(str(m.get('schema_version')) for m in metas)),'min_characters':min((len(a['content']) for a in articles),default=0)}
path=ROOT/'.local/lore-200/summary.json';path.write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if len(articles)!=200 or any(issues.values()):raise SystemExit(1)
