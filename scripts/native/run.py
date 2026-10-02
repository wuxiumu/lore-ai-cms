#!/usr/bin/env python3
"""Manage the native local development server without Docker or system configuration edits."""
from pathlib import Path
import json, os, shutil, signal, subprocess, sys, time, urllib.request
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'.local/server.json'

def alive(state):
    if not state: return False
    try:
        cmd=subprocess.check_output(['ps','-p',str(state['pid']),'-o','command='],text=True)
        return str(ROOT/'new-project/app/public/router.php') in cmd
    except subprocess.CalledProcessError: return False

def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'start'
    state=json.loads(STATE.read_text()) if STATE.exists() else None
    if action=='stop':
        if alive(state): os.kill(state['pid'],signal.SIGTERM); print('Local web server stopped. MySQL and data retained.')
        else: print('Local web server is not running.')
        STATE.unlink(missing_ok=True); return
    if action=='status':
        print('http://localhost:8080/admin is running' if alive(state) else 'Local web server is stopped.'); return
    if action!='start': raise SystemExit('Usage: python3 native/run.py start|stop|status')
    if alive(state): print('Already running: http://localhost:8080/admin'); return
    php=shutil.which('php')
    if not php: raise SystemExit('PHP CLI missing. Install PHP 8.3+ with pdo_mysql first.')
    (ROOT/'.local').mkdir(mode=0o700,exist_ok=True)
    if not (ROOT/'.local/native.json').exists(): subprocess.run([php,str(ROOT/'scripts/native/setup.php')],check=True)
    subprocess.run([php,str(ROOT/'scripts/php/install.php')],check=True)
    with (ROOT/'.local/server.log').open('ab') as log:
        process=subprocess.Popen([php,'-d','max_input_vars=20000','-d','display_errors=0','-d','log_errors=1','-S','127.0.0.1:8080','-t',str(ROOT/'new-project/app/public'),str(ROOT/'new-project/app/public/router.php')],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    for _ in range(30):
        if process.poll() is not None: raise SystemExit('Server failed to start; inspect .local/server.log (port 8080 may be occupied).')
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://127.0.0.1:8080/',timeout=2) as response:
                if response.status==200:
                    STATE.write_text(json.dumps({'pid':process.pid})); STATE.chmod(0o600)
                    print('Ready: http://localhost:8080/admin\nSites: http://localhost:8080/ and http://127.0.0.1:8080/\nCredentials: .local/admin-credentials.txt'); return
        except Exception: time.sleep(.15)
    process.terminate()
    raise SystemExit('Server did not become healthy; inspect .local/server.log.')

if __name__=='__main__': main()
