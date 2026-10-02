#!/usr/bin/env python3
"""Take a consistent local content snapshot, render HTML and zip public files only."""
from pathlib import Path
import argparse, datetime as dt, fcntl, hashlib, ipaddress, json, re, shutil, subprocess, sys, tempfile, urllib.parse, xml.etree.ElementTree as ET, zipfile
ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'.local/publishing.json'

def command(args,payload=None):
    result=subprocess.run(args,cwd=ROOT,input=json.dumps(payload,ensure_ascii=False) if payload else None,text=True,capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr.strip()[:600] or 'Renderer failed')
    return json.loads(result.stdout)

def validate_base(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.path not in ('','/') or p.query or p.fragment or p.username or p.password or p.port not in (None,443): raise ValueError('上线地址须为 HTTPS 域名根地址，不含路径、参数或账号。')
    host=p.hostname
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',host) or '.' not in host or host.endswith(('.localhost','.test','.local','.invalid')): raise ValueError('请填写真实线上域名。')
    try:
        if not ipaddress.ip_address(host).is_global: raise ValueError('不能使用本地 IP 上线。')
    except ValueError as e:
        if str(e)=='不能使用本地 IP 上线。': raise
    return 'https://'+host

def build(site_id,preview=False):
    releases=ROOT/'.local/releases'/('site-'+str(site_id));releases.mkdir(parents=True,exist_ok=True)
    with (releases/'build.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        snapshot=command(['php',str(ROOT/'scripts/php/static-snapshot.php'),str(site_id)])
        production=not preview
        base=validate_base(snapshot['site']['base_url']) if production else 'http://127.0.0.1:8081'
        crawlable=production and bool(snapshot['site']['indexable'])
        rendered=command(['php',str(ROOT/'scripts/php/static-render.php')],dict(snapshot,base_url=base,production=crawlable))
        stamp=dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f');mode='production' if production else 'preview'
        release=releases/(stamp+'-'+mode);release.mkdir();public=release/'public';public.mkdir()
        def write(name,content):
            path=public/name
            if path.resolve().is_relative_to(public.resolve()) is False: raise ValueError('Invalid output path')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
        for name,content in rendered['pages'].items():write(name,content)
        write('theme/style.css',snapshot['site']['_theme']['style.css'])
        write('theme/script.js',snapshot['site']['_theme']['script.js'])
        shutil.copy2(ROOT/'scripts/publishing/search.js',public/'search.js')
        shutil.copy2(ROOT/'new-project/app/public/reader.css',public/'reader.css')
        shutil.copy2(ROOT/'new-project/app/public/reader.js',public/'reader.js')
        for article in snapshot['articles']:
            meta=json.loads(article['metadata'] or '{}');cover=meta.get('cover','')
            if re.fullmatch('[a-z-]+',cover) and (ROOT/'new-project/app/public/covers'/f'{cover}.svg').is_file():
                (public/'covers').mkdir(exist_ok=True);shutil.copy2(ROOT/'new-project/app/public/covers'/f'{cover}.svg',public/'covers'/f'{cover}.svg')
        write('search-index.json',json.dumps([{'title':a['title'],'description':a['description'],'category':a['category'],'url':'/article/'+a['slug']+'.html'} for a in snapshot['articles']],ensure_ascii=False))
        ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
        updated={'/article/'+a['slug']+'.html':a['updated_at'].replace(' ','T')+'+08:00' for a in snapshot['articles']}
        # Actual file-based sitemap shards: no query-string routes on the static host.
        urls=rendered['urls']; chunks=[urls[i:i+10000] for i in range(0,len(urls),10000)] or [[]]
        for n,chunk in enumerate(chunks,1):
            tree=ET.Element('{'+ns+'}urlset')
            for path in chunk:
                item=ET.SubElement(tree,'{'+ns+'}url');ET.SubElement(item,'{'+ns+'}loc').text=base+path
                if path in updated:ET.SubElement(item,'{'+ns+'}lastmod').text=updated[path]
            write('sitemap.xml' if len(chunks)==1 else f'sitemap-{n}.xml',ET.tostring(tree,encoding='unicode',xml_declaration=True))
        if len(chunks)>1:
            tree=ET.Element('{'+ns+'}sitemapindex')
            for n in range(1,len(chunks)+1):
                item=ET.SubElement(tree,'{'+ns+'}sitemap');ET.SubElement(item,'{'+ns+'}loc').text=f'{base}/sitemap-{n}.xml'
            write('sitemap.xml',ET.tostring(tree,encoding='unicode',xml_declaration=True))
        write('robots.txt',f'User-agent: *\nAllow: /\nDisallow: /search.html\nSitemap: {base}/sitemap.xml\n' if crawlable else 'User-agent: *\nDisallow: /\n')
        files={str(p.relative_to(public)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(public.rglob('*')) if p.is_file()}
        latest_path=releases/'latest.json';previous=json.loads(latest_path.read_text()) if latest_path.exists() else {}
        known=set(previous.get('known_paths',previous.get('files',{})))|set(files)
        stale=sorted(known-set(files));(release/'stale-files.txt').write_text('\n'.join(stale)+('\n' if stale else ''))
        archive=release/f"{snapshot['site']['host']}-{mode}.zip"
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for name in files:z.write(public/name,arcname=name)
        with zipfile.ZipFile(archive) as z:
            if z.testzip():raise ValueError('ZIP validation failed')
            if 'index.html' not in z.namelist() or any(Path(n).suffix in ('.php','.sql','.py','.env') for n in z.namelist()):raise ValueError('Unexpected package files')
        manifest={'created_at':dt.datetime.now().isoformat(),'site_id':site_id,'site_name':snapshot['site']['name'],'mode':mode,'base_url':base,'article_count':len(snapshot['articles']),'html_count':len(rendered['pages']),'zip':str(archive),'public_dir':str(public),'files':files,'known_paths':sorted(known),'stale_files':stale}
        (release/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        temp=releases/'latest.tmp';temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));temp.replace(latest_path)
        return manifest

def main():
    c=json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    p=argparse.ArgumentParser();p.add_argument('--site-id',type=int,default=c.get('site_id',2));p.add_argument('--preview',action='store_true');args=p.parse_args()
    m=build(args.site_id,args.preview)
    print(json.dumps({k:v for k,v in m.items() if k not in ('files','known_paths')},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
