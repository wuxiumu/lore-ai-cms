"""Small owner-review flow check. No model requests and no article writes."""
from pathlib import Path
import sys,json,copy,subprocess,re,http.cookiejar,urllib.request,urllib.parse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/editorial'))
from catalog import state,duplicate,risk_flags
from catalog_drafts import eligibility
base=ROOT/'catalogs/site-2';directory=Path(json.loads((base/'latest.json').read_text())['directory']);data=json.loads((directory/'catalog.json').read_text());s=state(2)
assert not any(x['selected'] for x in data['items']) and not data['preferences']['use_hot_rank']
fiction=copy.deepcopy(next(x for x in data['items'] if x['story_type']=='fiction'));fiction.update(selected=True,provider='qwen',review_status='approved')
assert not eligibility(fiction,'qwen',s['articles'],data['items'])['eligible']
fiction['risk_reviewed']=True;assert eligibility(fiction,'qwen',s['articles'],data['items'])['eligible']
dup=copy.deepcopy(next(x for x in data['items'] if x['duplicate']['level']=='duplicate'));dup.update(selected=True,provider='glm',review_status='approved',risk_reviewed=True)
assert not eligibility(dup,'glm',s['articles'],data['items'])['eligible']
dup.update(duplicate_override=True,notes='只写一个已核实的新角度');assert eligibility(dup,'glm',s['articles'],data['items'])['eligible']
client=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def get(path):return client.open('http://localhost:8080'+path,timeout=40).read()
body=get('/admin/login').decode();token=re.search(r'name="csrf" value="([a-f0-9]+)"',body)[1];password=re.search(r'初始密码：([^\n]+)',(ROOT/'.local/admin-credentials.txt').read_text())[1]
client.open(urllib.request.Request('http://localhost:8080/admin/login',data=urllib.parse.urlencode({'csrf':token,'username':'admin','password':password}).encode())).read()
body=get('/admin/catalog?site_id=2').decode();assert '我的选题目录' in body and '鬼故事' in body and '下载 JSON' in body
for kind in ('json','csv','md'):assert len(get('/admin/catalog/download?site_id=2&format='+kind))>100
assert json.loads(get('/admin/catalog/download?site_id=2&format=json'))['site_id']==2
# Submit unchanged rows, verifying save and export round trip without adopting items.
fields={'csrf':re.search(r'name="csrf" value="([a-f0-9]+)"',body)[1],'action':'select'}
for x in data['items']:
 for key in ('title','description','notes','provider'):fields[f"rows[{x['id']}][{key}]"]=x[key]
client.open(urllib.request.Request('http://localhost:8080/admin/catalog?site_id=2',data=urllib.parse.urlencode(fields).encode()),timeout=40).read()
assert not any(x['selected'] for x in json.loads((directory/'catalog.json').read_text())['items'])
print('PASS: catalog download/save, all unselected, fiction review gate, duplicate gate/explicit override, no article or model writes.')
