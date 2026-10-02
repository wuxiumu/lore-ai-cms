#!/usr/bin/env python3
"""Stable repository-root command entry; all commands resolve paths from this file."""
from pathlib import Path
import argparse,subprocess,sys,json
ROOT=Path(__file__).resolve().parent
COMMANDS={
 'start':('python3','scripts/native/run.py','start'),
 'stop':('python3','scripts/native/run.py','stop'),
 'status':('python3','scripts/native/run.py','status'),
 'build':('python3','scripts/publishing/build.py'),
 'preview':('python3','scripts/publishing/preview.py'),
 'catalog-model':('python3','scripts/editorial/catalog_model.py'),
 'catalog':('python3','scripts/editorial/catalog.py'),
 'draft-qwen':('python3','scripts/editorial/catalog_drafts.py','--provider','qwen'),
 'draft-glm':('python3','scripts/editorial/catalog_drafts.py','--provider','glm'),
 'discover':('python3','scripts/editorial/catalog.py'),
 'generate':('python3','scripts/editorial/catalog_drafts.py'),
 'backup':('python3','scripts/native/backup.py'),
 'complete-lore':('python3','scripts/editorial/complete_lore.py'),
 'complete-200':('python3','scripts/editorial/complete_200.py'),
 'benchmark':('python3','scripts/editorial/benchmark.py'),
 'progress':('python3','scripts/progress.py'),
}
def main():
 p=argparse.ArgumentParser(description='新项目本地运行、内容生成、静态打包与进度查看')
 p.add_argument('command',choices=COMMANDS);args,extra=p.parse_known_args()
 cmd=list(COMMANDS[args.command]);cmd[1]=str(ROOT/cmd[1]);raise SystemExit(subprocess.call(cmd+extra,cwd=ROOT))
if __name__=='__main__':main()
