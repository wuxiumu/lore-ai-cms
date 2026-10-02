#!/usr/bin/env python3
"""HTTP smoke tests. Creates and removes its own temporary site/articles only."""
from pathlib import Path
import http.cookiejar, os, re, secrets, subprocess, urllib.error, urllib.parse, urllib.request, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
BASE='http://localhost:8080'
jar=http.cookiejar.CookieJar()
client=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(jar))

def request(path='/',data=None,host=None):
    headers={} if host is None else {'Host':host}
    req=urllib.request.Request(BASE+path,data=urllib.parse.urlencode(data).encode() if data is not None else None,headers=headers)
    try:
        with client.open(req,timeout=5) as r: return r.status,r.read().decode(),r.headers
    except urllib.error.HTTPError as e: return e.code,e.read().decode(),e.headers

def token(html): return re.search(r'name="csrf" value="([a-f0-9]+)"',html)[1]

def sql(code):
    r=subprocess.run(['php','-r','require "new-project/app/src/bootstrap.php"; '+code],cwd=ROOT,capture_output=True,text=True,check=True)
    return r.stdout.strip()

suffix=secrets.token_hex(5)
host='smoke-'+suffix+'.localhost'
site_id=None
checks=[]
try:
    status,body,headers=request()
    assert status==200 and '知识与工具' in body and 'noindex' in headers['X-Robots-Tag']; checks.append('server-rendered homepage and preview noindex')
    assert request('/',host='127.0.0.1:8080')[0]==200
    assert request('/',host='unknown-'+suffix+'.test')[0]==404; checks.append('host isolation')
    assert request('/article/not-exist.html')[0]==404
    assert request('/.local/native.json')[0]==404
    assert request('/../src/bootstrap.php')[0]==404; checks.append('404 and private-file protection')
    assert 'Disallow: /' in request('/robots.txt')[1]
    ET.fromstring(request('/sitemap.xml')[1]); checks.append('robots and XML sitemap')
    status,body,_=request('/admin')
    assert '管理员账号' in body
    cred=(ROOT/'.local/admin-credentials.txt').read_text()
    password=os.environ.get('MVP_TEST_PASSWORD') or re.search(r'初始密码：([^\n]+)',cred)[1]
    status,body,_=request('/admin/login',{'csrf':token(body),'username':'admin','password':password})
    assert status==200 and '站点与内容' in body; checks.append('administrator login')
    assert request('/admin/site',{'name':'missing-csrf'})[0]==403; checks.append('CSRF rejection')
    _,body,_=request('/admin/site')
    status,body,_=request('/admin/site',{'csrf':token(body),'name':'临时验证站 '+suffix,'host':host,'base_url':'http://'+host+':8080','description':'仅测试，自动清理'})
    assert status==200 and '临时验证站 '+suffix in body
    site_id=int(sql("echo query('SELECT id FROM mvp_sites WHERE host=?',['"+host+"'])->fetchColumn();"))
    assert request('/',host=host+':8080')[0]==200; checks.append('create and route new site')
    _,body,_=request('/admin/article?site_id='+str(site_id))
    payload={'csrf':token(body),'site_id':site_id,'title':'验证内容 '+suffix,'slug':'test-'+suffix,'description':'文章隔离验证','category':'验证分类','content':'真实内容段落\n\n<script>alert(1)</script>','status':'draft'}
    status,body,_=request('/admin/article',payload)
    assert status==200
    article_id=int(sql("echo query('SELECT id FROM mvp_articles WHERE site_id=?', ["+str(site_id)+"])->fetchColumn();"))
    path='/article/test-'+suffix+'.html'
    assert request(path,host=host+':8080')[0]==404
    assert 'test-'+suffix not in request('/sitemap.xml',host=host+':8080')[1]; checks.append('draft excluded from public page and sitemap')
    _,body,_=request('/admin/article?id='+str(article_id))
    payload.update(csrf=token(body),status='published')
    assert request('/admin/article?id='+str(article_id),payload)[0]==200
    status,body,_=request(path,host=host+':8080')
    assert status==200 and '&lt;script&gt;' in body and '<script>' not in body
    assert 'rel="canonical" href="http://'+host+':8080'+path+'"' in body
    assert request(path)[0]==404; checks.append('publish, canonical, XSS escaping and cross-site isolation')
    assert 'test-'+suffix in request('/sitemap.xml',host=host+':8080')[1]
    assert '验证内容 '+suffix in request('/search?q='+urllib.parse.quote(suffix),host=host+':8080')[1]
    assert request('/?page=99999',host=host+':8080')[0]==404; checks.append('search, sitemap refresh and invalid pagination')
    _,body,_=request('/admin/article?id='+str(article_id))
    payload.update(csrf=token(body),slug='changed-'+suffix)
    assert '已发布文章的站点和网址保持稳定' in request('/admin/article?id='+str(article_id),payload)[1]; checks.append('published URL stability')
    _,body,_=request('/admin/article?id='+str(article_id))
    assert request('/admin/article?id='+str(article_id),{'csrf':token(body),'action':'delete'})[0]==200
    assert request(path,host=host+':8080')[0]==404
    assert 'test-'+suffix not in request('/sitemap.xml',host=host+':8080')[1]; checks.append('delete removes page and sitemap entry')
    assert request('/admin/urls?site_id='+str(site_id))[0]==422; checks.append('local URLs cannot be exported for indexing')
    _,body,_=request('/admin/site?id='+str(site_id))
    site_payload={'csrf':token(body),'name':'临时验证站 '+suffix,'host':host,'base_url':'http://'+host+':8080','description':'仅测试，自动清理','indexable':'1'}
    assert '开放收录须填写真实域名和 HTTPS 地址' in request('/admin/site?id='+str(site_id),site_payload)[1]
    public_host='smoke-'+suffix+'.example.com'
    site_payload.update(host=public_host,base_url='https://'+public_host)
    assert request('/admin/site?id='+str(site_id),site_payload)[0]==200
    host=public_host
    status,body,headers=request('/',host=host)
    assert status==200 and headers.get('X-Robots-Tag') is None
    assert 'Allow: /' in request('/robots.txt',host=host)[1]
    assert request('/admin/urls?site_id='+str(site_id))[1]=='https://'+host+'/\n'
    checks.append('public indexing setting and per-site URL export (local Host simulation only)')
    _,body,_=request('/admin')
    request('/admin/logout',{'csrf':token(body)})
    assert '管理员账号' in request('/admin')[1]; checks.append('logout revokes session')
finally:
    if site_id:
        sql("query('DELETE FROM mvp_articles WHERE site_id=?',["+str(site_id)+"]); query('DELETE FROM mvp_sites WHERE id=? AND host=?',["+str(site_id)+",'"+host+"']);")
for c in checks: print('PASS '+c)
print(str(len(checks))+' smoke checks passed. Temporary test content removed.')
