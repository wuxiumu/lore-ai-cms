#!/usr/bin/env python3
"""Revise one flagged fictional story; retain original review and API usage."""
import json,subprocess,time
from catalog import ROOT,emit,topic_key
from model_client import call,json_result
from pipeline import validate
base=ROOT/'.local/beijing-210';data=json.loads((base/'catalog.json').read_text());item=next(x for x in data['items'] if x['id']=='ba4cf4e49e29')
code="require 'new-project/app/src/bootstrap.php';echo json_encode(query('SELECT a.*,m.metadata FROM mvp_articles a JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.id=602 AND a.site_id=8')->fetch(),JSON_UNESCAPED_UNICODE);"
a=json.loads(subprocess.run(['php','-r',code],cwd=ROOT,text=True,capture_output=True,check=True).stdout);assert a['status']=='draft','Refusing to rewrite a published story';meta=json.loads(a['metadata']);provider=json.loads((ROOT/'.local/model-providers.json').read_text())['qwen' if meta['generation']['provider']=='千问' else 'glm'];trace=ROOT/'.local/catalog-generation'/('8-'+topic_key(item));events=json.loads((trace/'usage.json').read_text());start=time.monotonic()
def ask(stage,system,payload):
 text,u=call(provider,system,payload,4500);u['stage']=stage;events.append(u);(trace/'usage.json').write_text(json.dumps(events,ensure_ascii=False,indent=2));(trace/(stage+'.txt')).write_text(text);return json_result(text)
title='北京电影学院附近的旧镜头，专拍演员没有说出口的心事'
article=ask('revise-place-background','你是原创小说编辑。输出合法JSON：title,slug,description,category,content,keywords。保留旧故事的镜头与演戏悬念，但必须把实际场景设为北京电影学院附近的一间虚构排练工作室，人物均为成年虚构演员，学校仅为附近地名背景。不得将该校写成虚构院校，也不能写该校真实设施、真实师生、校园传闻、事故或犯罪。标题固定为指定新标题。正文800—1200字，至少3个独立##小标题。开头必须明确北京地名仅作背景，学校附近的工作室、人物和情节全属原创虚构。禁止军政、危险行为。keywords不要使用北电灵异、北电闹鬼等把机构与灵异绑定的词，只用地名背景和原创题材关键词。只输出JSON。',{'title':title,'original':{k:a[k] for k in ['title','description','category','content']}})
if '北京地名仅作故事背景' not in article['content']:article['content']='北京地名仅作故事背景，不表示该地点存在真实灵异事件；附近工作室、人物与情节为原创虚构。\n\n'+article['content']
article['title']=title;article['slug']=a['slug'];article['category']=a['category'];keywords=article.pop('keywords',[])
verdict=ask('review-place-background','你是小说审核员，只输出JSON {"approved":true或false,"issues":[]}。真实北京地名可以作为明确标注的虚构小说背景，但不能误称真实学校为虚构学校，也不得把学校或真实师生描述为真实灵异事件、事故或犯罪。正文应明确主要场所为学校附近的虚构工作室，成年人虚构情节；核对此背景边界、军政排除、虚构声明和危险模仿，不将有明确标签的超自然情节当真实新闻。',{'article':article,'keywords':keywords,'story_type':'fiction','background_role':'学校仅作邻近地名，工作室并非学校真实设施'})
if verdict.get('approved') is not True:raise RuntimeError('Revision requires follow-up: '+json.dumps(verdict,ensure_ascii=False))
meta.setdefault('review_history',[]).append(meta['review']);meta['review']=verdict;meta['keywords']=keywords;meta['generation']['calls']=events;meta['generation']['seconds']+=round(time.monotonic()-start,2);validate(article,meta);(trace/'article-background-revised.json').write_text(json.dumps({'article':article,'metadata':meta},ensure_ascii=False,indent=2))
update="require 'new-project/app/src/bootstrap.php';$d=json_decode(stream_get_contents(STDIN),true);db()->beginTransaction();query('UPDATE mvp_articles SET title=?,description=?,content=?,updated_at=NOW() WHERE id=602 AND site_id=8 AND status=\"draft\"',[$d['article']['title'],$d['article']['description'],$d['article']['content']]);query('UPDATE mvp_article_meta SET metadata=? WHERE article_id=602',[json_encode($d['metadata'],JSON_UNESCAPED_UNICODE)]);query('UPDATE mvp_editorial_jobs SET title=? WHERE article_id=602 AND site_id=8',[$d['article']['title']]);db()->commit();"
subprocess.run(['php','-r',update],input=json.dumps({'article':article,'metadata':meta},ensure_ascii=False),cwd=ROOT,text=True,check=True)
item['title']=title;item['description']='以北京电影学院附近的一间虚构排练工作室为背景，成年演员通过旧镜头看到自己没有表达过的心事。真实学校仅作地名背景，不涉及真实设施、师生或传闻。';(base/'catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));directory=__import__('pathlib').Path(json.loads((base/'directory.json').read_text())['directory']);combined=json.loads((directory/'catalog.json').read_text());combined['items']=[item if x['id']==item['id'] else x for x in combined['items']];emit(directory,combined);print('Revised story602; re-review passed; original model verdict retained')
