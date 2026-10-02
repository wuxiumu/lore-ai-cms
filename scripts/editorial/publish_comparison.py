#!/usr/bin/env python3
"""Publish the six explicitly reviewed trial artifacts through the normal store."""
import hashlib,json,subprocess
from pathlib import Path
from pipeline import store,validate
ROOT=Path(__file__).resolve().parents[2];DIR=ROOT/'.local/comparison'
def main():
 topics=json.loads((DIR/'topics.json').read_text());state=store({'action':'state','site_id':2})
 if state['site']['host']!='jiexiangqiwen.chiguashentan.com':raise SystemExit('Unexpected target site')
 # One-run allowance, do not change the standing daily limit of 3.
 cap=min(20,state['today']+6)
 results=[]
 for topic in topics:
  p=DIR/(topic['key']+'.json');x=json.loads(p.read_text())
  if not x.get('editorial_reviewed'):raise SystemExit('Editorial source review incomplete: '+topic['key'])
  validate(x['article'],x['metadata'])
  key=hashlib.sha256(('six-model-trial-20260930:'+topic['key']).encode()).hexdigest()
  out=store({'action':'publish','site_id':2,'topic_key':key,'article':x['article'],'metadata':x['metadata'],'status':'published','daily_limit':cap})
  x['publication']=out;p.write_text(json.dumps(x,ensure_ascii=False,indent=2));results.append(out)
 subprocess.run(['python3',str(ROOT/'scripts/publishing/build.py'),'--site-id','2'],check=True)
 (DIR/'publication.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
