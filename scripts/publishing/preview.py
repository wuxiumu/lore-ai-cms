#!/usr/bin/env python3
"""Preview each site's latest static export on site-ID.localhost:8081."""
from pathlib import Path
import http.server,json,re
ROOT=Path(__file__).resolve().parents[2]
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT/'.local/no-public-files'),**kwargs)
    def do_GET(self):
        if self.select_site(): super().do_GET()
    def do_HEAD(self):
        if self.select_site(): super().do_HEAD()
    def select_site(self):
        host=self.headers.get('Host','').split(':')[0]
        match=re.fullmatch(r'site-([1-9][0-9]*)\.localhost',host)
        sid=int(match[1]) if match else 2
        path=ROOT/'.local/releases'/f'site-{sid}'/'latest.json'
        if not path.is_file(): self.send_error(404);return False
        self.directory=json.loads(path.read_text())['public_dir'];return True
    def end_headers(self):
        self.send_header('X-Robots-Tag','noindex, nofollow')
        self.send_header('Cache-Control','no-store')
        super().end_headers()
    def send_error(self,code,message=None,explain=None):
        file=Path(self.directory)/'404.html'
        if code==404 and file.exists():
            body=file.read_bytes();self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers()
            if self.command!='HEAD':self.wfile.write(body)
        else:super().send_error(code,message,explain)
    def list_directory(self,path):self.send_error(404);return None
server=http.server.ThreadingHTTPServer(('127.0.0.1',8081),Handler)
print('Static previews: http://site-2.localhost:8081/ and http://site-1.localhost:8081/',flush=True)
server.serve_forever()
