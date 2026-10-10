"""Load a repository-root .env without overriding existing environment variables."""
from pathlib import Path
import os, re
_KEY=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def load_env(root):
    path=Path(root)/'.env'
    if not path.is_file(): return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line=raw.strip()
        if not line or line.startswith('#'): continue
        if line.startswith('export '): line=line[7:].strip()
        if '=' not in line: continue
        key,value=line.split('=',1)
        key=key.strip()
        if not _KEY.match(key) or key in os.environ: continue
        value=value.strip()
        if len(value)>=2 and value[0]==value[-1] and value[0] in '"\'': value=value[1:-1]
        os.environ[key]=value
