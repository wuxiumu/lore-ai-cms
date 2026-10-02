#!/usr/bin/env python3
"""Back up this app's database and native configuration to a private local archive."""
from pathlib import Path
import datetime, json, os, shutil, subprocess, tarfile, tempfile
root=Path(__file__).resolve().parents[2]
c=json.loads((root/'.local/native.json').read_text())
bin=shutil.which('mysqldump')
if not bin: raise SystemExit('mysqldump missing')
backup=root/'.local/backups'; backup.mkdir(mode=0o700,parents=True,exist_ok=True)
os.umask(0o077)
target=backup/('native-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.tar.gz')
with tempfile.TemporaryDirectory(prefix='station-backup-') as t:
    sql=Path(t)/'database.sql'
    env=os.environ.copy(); env['MYSQL_PWD']=c['password']
    with sql.open('wb') as out:
        result=subprocess.run([bin,'--host='+c['host'],'--user='+c['user'],'--single-transaction','--skip-triggers','--no-tablespaces','--set-gtid-purged=OFF',c['database']],stdout=out,stderr=subprocess.PIPE,env=env)
    if result.returncode: raise SystemExit('Database backup failed; no archive produced. Check database connection and permissions.')
    with tarfile.open(target,'w:gz') as archive:
        archive.add(sql,arcname='database.sql')
        archive.add(root/'.local/native.json',arcname='native.json')
        for folder in ('new-project','scripts','doc','catalogs'):
            if (root/folder).exists(): archive.add(root/folder,arcname=folder)
        for name in ('project.py','README.md'):
            archive.add(root/name,arcname=name)
        for name in ('editorial.json','publishing.json','model-providers.json','admin-credentials.txt'):
            if (root/'.local'/name).exists(): archive.add(root/'.local'/name,arcname='.local/'+name)
        for folder in ('comparison','editorial','theme-history','catalog-generation'):
            if (root/'.local'/folder).exists(): archive.add(root/'.local'/folder,arcname='.local/'+folder)
    with tarfile.open(target,'r:gz') as archive:
        assert archive.getmember('database.sql').size>0
print('Backup created and archive readable: '+str(target))
