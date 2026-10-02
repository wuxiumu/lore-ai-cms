"""One focused local smoke check: settings, theme save, export and site isolation."""
from pathlib import Path
import http.cookiejar,urllib.request,urllib.parse,re,json,subprocess,zipfile,io
ROOT=Path(__file__).resolve().parents[2]
client=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(path,data=None,host=None):
 req=urllib.request.Request('http://localhost:8080'+path,data=urllib.parse.urlencode(data).encode() if data is not None else None,headers={'Host':host} if host else {})
 with client.open(req,timeout=30) as r:return r.read(),r.headers
csrf=lambda s:re.search(r'name="csrf" value="([a-f0-9]+)"',s.decode())[1]
body,_=request('/admin/login')
password=re.search(r'初始密码：([^\n]+)',(ROOT/'.local/admin-credentials.txt').read_text())[1]
body,_=request('/admin/login',{'csrf':csrf(body),'username':'admin','password':password})
assert '站点与内容' in body.decode()
for sid,domain in [(1,'lore.chiguashentan.com'),(2,'jiexiangqiwen.chiguashentan.com')]:
 snap=json.loads(subprocess.check_output(['php','scripts/php/static-snapshot.php',str(sid)],cwd=ROOT));site=snap['site']
 body,_=request(f'/admin/site?id={sid}')
 data={k:site[k] for k in ('name','host','description','seo_title','seo_description','seo_keywords','content_topic','topic_keywords')}
 data.update(csrf=csrf(body),indexable='1')
 body,_=request(f'/admin/site?id={sid}',data);assert '保存成功' in body.decode()
 path=f'/admin/theme?site_id={sid}&file=home.html'
 body,_=request(path);original=(ROOT/f'new-project/themes/site-{sid}/home.html').read_text();marker=f'<!-- smoke-site-{sid} -->'
 try:
  body,_=request(path,{'csrf':csrf(body),'source':original+marker});assert '已保存' in body.decode()
  body,headers=request('/',host=f'site-{sid}.localhost:8080');assert marker in body.decode() and 'noindex' in headers['X-Robots-Tag']
 finally:
  body,_=request(path);request(path,{'csrf':csrf(body),'source':original})
 body,_=request(f'/admin/static?site_id={sid}');assert 'name="base_url"' not in body.decode()
 body,_=request(f'/admin/static?site_id={sid}',{'csrf':csrf(body)});assert '静态包已生成' in body.decode()
 binary,_=request(f'/admin/static/download?site_id={sid}')
 with zipfile.ZipFile(io.BytesIO(binary)) as z:
  assert z.testzip() is None
  html=z.read('index.html').decode();assert f'<title>{site["seo_title"]}</title>' in html
  assert f'https://{domain}/' in html and '<meta name="keywords"' in html
  assert 'noindex' not in html and 'localhost' not in html and '/admin' not in html
  assert z.read('theme/style.css').decode()==(ROOT/f'new-project/themes/site-{sid}/style.css').read_text()
  assert z.read('theme/script.js').decode()==(ROOT/f'new-project/themes/site-{sid}/script.js').read_text()
  assert b'<?php' not in z.read('index.html') and all(not n.endswith(('.php','.sql','.py')) for n in z.namelist())
  sitemap=z.read('sitemap.xml').decode();assert domain in sitemap
  other='lore.chiguashentan.com' if sid==2 else 'jiexiangqiwen.chiguashentan.com';assert other not in sitemap
  assert len([n for n in z.namelist() if n.startswith('article/')])==(3 if sid==2 else 0)
 req=urllib.request.Request('http://127.0.0.1:8081/',headers={'Host':f'site-{sid}.localhost:8081'})
 with client.open(req) as r: assert site['seo_title'] in r.read().decode() and 'noindex' in r.headers['X-Robots-Tag']
print('PASS: two-site settings save, independent template editing, local previews, per-site ZIP download, TDK/domain/content/assets isolation.')
