#!/usr/bin/env python3
"""Inspect Git candidate/staged files. Never print credential values."""
from pathlib import Path
import argparse,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def main():
    p=argparse.ArgumentParser();p.add_argument('--staged',action='store_true');a=p.parse_args()
    paths=git('diff','--cached','--name-only','--diff-filter=ACMR','-z') if a.staged else git('ls-files','--cached','--others','--exclude-standard','-z')
    names=sorted(set(x.decode() for x in paths.split(b'\0') if x));issues=[]
    patterns=[re.compile(rb'sk-(?:sp-)?[A-Za-z0-9_.-]{20,}'),re.compile(rb'(?i)(?:api[_-]?key|password|secret)\s*[=:]\s*[\x22\x27][A-Za-z0-9_.-]{24,}[\x22\x27]'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    forbidden=('.local/','legacy-project/','catalogs/','dist/','.claude/')
    for name in names:
        if name.startswith(forbidden) or (name.startswith('doc/') and not name.startswith('doc/open-source/')):issues.append((name,'私有或未授权发布路径'));continue
        if a.staged:data=git('show',':'+name)
        else:
            f=ROOT/name
            if not f.is_file():continue
            data=f.read_bytes()
        if any(rx.search(data) for rx in patterns):issues.append((name,'疑似凭据，请人工检查（值已隐藏）'))
        if len(data)>2_000_000:issues.append((name,'文件超过2MB，检查是否是生成产物'))
    for name,reason in issues:print(f'{name}: {reason}')
    print(f'检查 {len(names)} 个'+('暂存' if a.staged else '候选')+f'文件；发现 {len(issues)} 项。检查只提供辅助，仍需人工审阅 diff。')
    return bool(issues)
if __name__=='__main__':sys.exit(main())
