#!/usr/bin/env python3
"""Verify the authorized 200-article static package without printing secrets."""
from pathlib import Path
import argparse,json,zipfile,urllib.parse,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser();p.add_argument('--site-id',type=int,choices=[1,2,9,10],default=2);args=p.parse_args()
 m=json.loads((ROOT/f'.local/releases/site-{args.site_id}/latest.json').read_text());expected={1:'https://lore.chiguashentan.com',2:'https://jiexiangqiwen.chiguashentan.com',9:'https://hushang.chiguashentan.com',10:'https://shancheng.chiguashentan.com'};assert m['article_count']==200 and m['base_url']==expected[args.site_id]
 with zipfile.ZipFile(m['zip']) as z:
  assert z.testzip() is None;names=z.namelist();assert sum(n.startswith('article/') and n.endswith('.html') for n in names)==200
  assert all(Path(n).suffix not in ['.php','.sql','.py','.env','.toml'] for n in names)
  secrets=[]
  for v in json.loads((ROOT/'.local/model-providers.json').read_text()).values():
   if v.get('api_key'):secrets.append(v['api_key'].encode())
  for name in names:
   content=z.read(name);assert not any(secret in content for secret in secrets),'Secret detected in package'
  sitemap=ET.fromstring(z.read('sitemap.xml'));urls=[e.text for e in sitemap.iter() if e.tag.endswith('loc')];assert sum('/article/' in u for u in urls)==200;assert all(u.startswith(m['base_url']+'/') for u in urls)
  assert b'Allow: /' in z.read('robots.txt')
  assert len(json.loads(z.read('search-index.json')))==200
  for url in urls:
   path=urllib.parse.urlsplit(url).path.lstrip('/') or 'index.html';assert path in names, 'Missing sitemap file'
  for name in ['theme/style.css','theme/script.js','index.html','404.html']:assert name in names
 print(json.dumps({'verified':True,'article_count':200,'html_count':m['html_count'],'zip_bytes':Path(m['zip']).stat().st_size,'zip':m['zip']},ensure_ascii=False))
if __name__=='__main__':main()
