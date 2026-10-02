#!/usr/bin/env python3
"""Review directory premises and replace only confirmed redundant ideas before writing."""
import json,datetime
from pathlib import Path
from catalog import ROOT,duplicate,risk_flags,state,emit,topic_key
from model_client import call,json_result
base=ROOT/'.local/shanghai-200';file=base/'catalog.json';d=json.loads(file.read_text());assert len(d['items'])==200
providers=json.loads((ROOT/'.local/model-providers.json').read_text());events=json.loads((base/'catalog-usage.json').read_text())
def ask(stage,prompt,payload):
 raw,u=call(providers['qwen'],prompt,payload,4500);u['stage']=stage;events.append(u);(base/'catalog-usage.json').write_text(json.dumps(events,ensure_ascii=False,indent=2));(base/(stage+'.txt')).write_text(raw);return json_result(raw)
report=ask('premise-review','你是原创恐怖故事目录的去重编辑。只输出JSON {"duplicates":[{"keep":"目录id","replace":"目录id","reason":"相同具体情节"}]}。只有同一地点或相似地点、同一具体物件、同一异常机制且故事发展相近才算重复，不因都写鬼影、电梯、照片等常见恐怖元素而误判。不要更改其他风格。覆盖全部目录，尽量保留先出现的选题。',{'items':[{k:x[k] for k in ['id','title','description']} for x in d['items']]})
known={x['id']:x for x in d['items']};ids=[]
for pair in report.get('duplicates',[]):
 if pair.get('replace') in known and pair.get('keep') in known and pair['replace']!=pair['keep'] and pair['replace'] not in ids:ids.append(pair['replace'])
# Human-confirmed repeated Zhangjiang microwave premise.
if 'db01ab91317e' not in ids:ids.append('db01ab91317e')
existing=state(9)['articles'];changes=[]
for id in ids:
 x=known[id]
 for attempt in range(3):
  new=ask('premise-replace-'+id+'-'+str(attempt),'只输出JSON {"title":"含指定地名的18—45字标题","description":"80—160字完整恐怖创意"}。替换指定重复选题，用全新物件、异常机制、生活矛盾和余悸结尾，不沿用旧剧情。上海真实地名仅作背景，人物和附近具体场所全虚构；不指控真实机构，不写军政、学生受害或危险模仿，不冒充真实事件。',{'place':x['background_place'],'old':x,'avoid_titles':[z['title'] for z in d['items']]})
  trial={**x,'title':new['title'],'description':new['description']}
  if x['background_place'] not in trial['title']:trial['title']=x['background_place']+'：'+trial['title']
  shadow=[{'id':z['id'],'title':z['title'],'metadata':json.dumps({'story_type':'fiction','catalog_topic_key':topic_key(z)})} for z in d['items'] if z['id']!=id]
  trial['duplicate']=duplicate(trial,existing+shadow)
  if trial['duplicate']['level']=='clear':break
 else:raise RuntimeError('Replacement still duplicates: '+id)
 trial['risk_flags']=risk_flags(trial);changes.append({'id':id,'before':x,'after':trial});known[id]=trial;d['items']=[trial if z['id']==id else z for z in d['items']]
file.write_text(json.dumps(d,ensure_ascii=False,indent=2));directory=Path(json.loads((base/'directory.json').read_text())['directory']);emit(directory,d);(base/'premise-changes.json').write_text(json.dumps({'report':report,'changes':changes,'at':datetime.datetime.now().isoformat()},ensure_ascii=False,indent=2));print('Reviewed200 premises; replacements='+str(len(changes)))
