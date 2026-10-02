from pathlib import Path
import copy, importlib.util, json, subprocess, sys, unittest, urllib.request, xml.etree.ElementTree as ET
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('pipeline',ROOT/'scripts/editorial/pipeline.py');pipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipe)
SAMPLES=json.loads((ROOT/'scripts/editorial/samples.json').read_text())
CONFIG=json.loads((ROOT/'.local/editorial.json').read_text())
http=urllib.request.build_opener(urllib.request.ProxyHandler({}))
class EditorialTests(unittest.TestCase):
    def test_sample_pages_and_sitemap(self):
        for topic in SAMPLES:
            with http.open('http://127.0.0.1:8080/article/'+topic['article']['slug']+'.html') as r:
                page=r.read().decode();self.assertEqual(r.status,200);self.assertIn('noindex',r.headers['X-Robots-Tag'])
            self.assertIn('资料与出处',page);self.assertIn('<h2>',page);self.assertIn('原创示意插画',page)
            import re
            data=json.loads(re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',page)[1])
            self.assertEqual(data['@type'],'Article');self.assertEqual(data['headline'],topic['article']['title'])
            self.assertIn("script-src 'nonce-",r.headers['Content-Security-Policy'])
            with http.open('http://127.0.0.1:8080/covers/'+topic['cover']+'.svg') as image: ET.fromstring(image.read())
        with http.open('http://127.0.0.1:8080/sitemap.xml') as r: sitemap=r.read().decode()
        ET.fromstring(sitemap)
        self.assertNotIn('organize-your-daily-notes',sitemap)
        for t in SAMPLES:self.assertIn(t['article']['slug'],sitemap)
    def test_no_duplicate_sample_publications(self):
        state=pipe.store({'action':'state','site_id':CONFIG['site_id']})
        config=dict(CONFIG,daily_limit=10)
        self.assertEqual(pipe.run(config,SAMPLES,True,3),[])
        self.assertEqual(len(state['jobs']),len(pipe.store({'action':'state','site_id':CONFIG['site_id']})['jobs']))
    def test_malformed_rss_ampersand(self):
        xml='<rss><channel><item><title>V&A博物馆</title><link>https://example.com/story</link><pubDate>Wed, 30 Sep 2026 10:00:00 +0800</pubDate><description>趣闻</description></item></channel></rss>'
        with patch.object(pipe,'fetch',return_value=xml):
            self.assertEqual(pipe.rss({'name':'fixture','url':'https://example.com/rss'})[0]['title'],'V&A博物馆')
    def test_private_source_rejected(self):
        with self.assertRaises(ValueError): pipe.fetch('http://127.0.0.1:8080/')
    def test_missing_model_does_not_publish(self):
        with patch.dict(pipe.os.environ,{},clear=True):
            with self.assertRaises(RuntimeError): pipe.complete({'llm':{}},'test',{})
    def test_reviewer_rejection(self):
        topic=copy.deepcopy(SAMPLES[0]);topic['sources'][0]['summary']='事实摘要'
        responses=[{'facts':['可核实事实一','可核实事实二'],'suitable':True},topic['article'],{'approved':False,'issues':['存在无依据的断言']}]
        with patch.object(pipe,'fetch',return_value='公开事实资料'),patch.object(pipe,'complete',side_effect=responses):
            article,meta,approved=pipe.generated(CONFIG,topic)
            self.assertFalse(approved);self.assertEqual(meta['review']['issues'],['存在无依据的断言'])
    def test_approve_publish_and_draft_real_database(self):
        create="require 'new-project/app/src/bootstrap.php'; query('INSERT INTO mvp_sites(host,base_url,name,description,created_at) VALUES(?,?,?,?,NOW())',['editorial-test.localhost','http://editorial-test.localhost:8080','测试自动流程','fixture']); echo db()->lastInsertId();"
        sid=int(subprocess.check_output(['php','-r',create],cwd=ROOT,text=True))
        try:
            topics=copy.deepcopy(SAMPLES[:2]);config=dict(CONFIG,site_id=sid,site_name='测试自动流程',daily_limit=2)
            meta={'sources':topics[0]['sources'],'cover':'city-levels'}
            with patch.object(pipe,'generated',side_effect=[(topics[0]['article'],meta,True),(topics[1]['article'],meta,False)]):
                results=pipe.run(config,topics,False,2)
            self.assertEqual([x['status'] for x in results],['published','draft'])
            self.assertEqual(pipe.run(config,SAMPLES,True,3),[])
            self.assertEqual(len(pipe.store({'action':'state','site_id':sid})['jobs']),2)
        finally:
            code=f"require 'new-project/app/src/bootstrap.php'; query('DELETE FROM mvp_articles WHERE site_id=?',[{sid}]);query('DELETE FROM mvp_sites WHERE id=?',[{sid}]);"
            subprocess.run(['php','-r',code],cwd=ROOT,check=True)
if __name__=='__main__':unittest.main()
