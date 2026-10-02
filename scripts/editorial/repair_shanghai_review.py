#!/usr/bin/env python3
"""Revise only draft stories flagged by review, keeping verdict history and usage."""
import json,re,subprocess,time
from catalog import ROOT,topic_key
from model_client import call,json_result
from pipeline import validate
base=ROOT/'.local/shanghai-200';data=json.loads((base/'catalog.json').read_text());wanted={x['id']:x for x in data['items']};providers=json.loads((ROOT/'.local/model-providers.json').read_text())
code="require 'new-project/app/src/bootstrap.php';echo json_encode(query('SELECT a.*,m.metadata FROM mvp_articles a JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.site_id=9')->fetchAll(),JSON_UNESCAPED_UNICODE);"
rows=json.loads(subprocess.run(['php','-r',code],cwd=ROOT,text=True,capture_output=True,check=True).stdout)
for a in rows:
 m=json.loads(a['metadata']);item=wanted.get(m.get('catalog_id'))
 if not item or m.get('review',{}).get('approved') is True:continue
 assert a['status']=='draft';trace=ROOT/'.local/catalog-generation'/('9-'+topic_key(item));events=json.loads((trace/'usage.json').read_text());provider=providers['qwen' if m['generation']['provider']=='千问' else 'glm'];started=time.monotonic()
 def ask(stage,prompt,payload):
  raw,u=call(provider,prompt,payload,4500);u['stage']=stage;events.append(u);(trace/'usage.json').write_text(json.dumps(events,ensure_ascii=False,indent=2));(trace/(stage+'.txt')).write_text(raw);return json_result(raw)
 if m.get('review',{}).get('invalid_json'):
  verdict=ask('review-json-retry','你是小说审核员，必须仅输出一个合法JSON对象 {"approved":true或false,"issues":[]}，不得附带说明、括号文字或Markdown。审核明确标注虚构的上海恐怖故事；允许虚构剧情，不当作新闻核验，不含真实个人机构的事实性指控、军政、危险模仿。',{'article':{k:a[k] for k in ['title','description','content','category']},'story_type':'fiction'})
  if verdict.get('approved') is True:
   m.setdefault('review_history',[]).append(m['review']);m['review']=verdict;m['generation']['calls']=events;m['generation']['seconds']+=round(time.monotonic()-started,2)
   update="require 'new-project/app/src/bootstrap.php';$d=json_decode(stream_get_contents(STDIN),true);db()->beginTransaction();if(!query('SELECT id FROM mvp_articles WHERE id=? AND site_id=9 AND status=\"draft\" FOR UPDATE',[$d['id']])->fetch())throw new RuntimeException('Draft required');query('UPDATE mvp_article_meta SET metadata=? WHERE article_id=?',[json_encode($d['metadata'],JSON_UNESCAPED_UNICODE),$d['id']]);db()->commit();"
   subprocess.run(['php','-r',update],input=json.dumps({'id':a['id'],'metadata':m},ensure_ascii=False),cwd=ROOT,text=True,check=True);print('Re-reviewed JSON '+str(a['id']),flush=True);continue
  m.setdefault('review_history',[]).append(m['review']);m['review']=verdict
 for attempt in range(3):
  article=ask('review-revise-'+str(attempt),'你是原创恐怖故事编辑。修正给定审核问题，保留标题与主要悬念，强化可信生活细节与恐怖余悸。只输出JSON title,slug,description,category,content,keywords。正文800—1200字，至少3个独立##小标题。真实上海地名只作附近地理背景，实际房间设施和成年人为虚构，不称真实学校为虚构学校，不捏造真实机构事故、犯罪或亲历；不用军政、学生受害、危险操作。程序统一添加性质说明，直接进入故事，不反复说虚构的。',{'title':item['title'],'article':{k:a[k] for k in ['title','description','content','category']},'issues':m['review']})
  pre,sep,body=article['content'].partition('## ')
  if sep and len(pre)<300 and '虚构' in pre:article['content']='## '+body
  article['content']='上海地名仅作故事背景，不表示该地点存在真实灵异事件；人物、场所细节与情节为原创虚构。\n\n'+article['content'];article['title']=item['title'];article['slug']=a['slug'];article['category']=a['category'];keywords=article.pop('keywords',[])
  if isinstance(keywords,str):keywords=[x.strip() for x in re.split(r'[,，、;；]',keywords) if x.strip()]
  if not isinstance(keywords,list) or any(not isinstance(x,str) for x in keywords):raise ValueError('Invalid keywords array')
  verdict=ask('re-review-'+str(attempt),'审核原创虚构恐怖故事，仅输出JSON {"approved":true或false,"issues":[]}。允许带明确标签的虚构人物、鬼怪和日常设施，不当作新闻核验；实际地名只作背景。不允许捏造真实机构的真实事故指控、真实案件或亲历；不要把真实学校称为虚构学校。不含军政、学生受害或危险模仿教程。',{'article':article,'story_type':'fiction','previous_issues':m['review']})
  m.setdefault('review_history',[]).append(m['review']);m['review']=verdict
  if verdict.get('approved') is True:break
 else:raise RuntimeError('Review still requires follow-up '+str(a['id']))
 m['keywords']=keywords;m['generation']['calls']=events;m['generation']['seconds']+=round(time.monotonic()-started,2);validate(article,m);(trace/'article-reviewed.json').write_text(json.dumps({'article':article,'metadata':m},ensure_ascii=False,indent=2))
 update="require 'new-project/app/src/bootstrap.php';$d=json_decode(stream_get_contents(STDIN),true);db()->beginTransaction();$a=query('SELECT id FROM mvp_articles WHERE id=? AND site_id=9 AND status=\"draft\" FOR UPDATE',[$d['id']])->fetch();if(!$a)throw new RuntimeException('Draft required');query('UPDATE mvp_articles SET description=?,content=?,updated_at=NOW() WHERE id=?',[$d['article']['description'],$d['article']['content'],$d['id']]);query('UPDATE mvp_article_meta SET metadata=? WHERE article_id=?',[json_encode($d['metadata'],JSON_UNESCAPED_UNICODE),$d['id']]);db()->commit();"
 subprocess.run(['php','-r',update],input=json.dumps({'id':a['id'],'article':article,'metadata':m},ensure_ascii=False),cwd=ROOT,text=True,check=True);print('Revised and reviewed '+str(a['id']),flush=True)
