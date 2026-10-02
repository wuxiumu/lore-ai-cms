#!/usr/bin/env python3
"""Read milestone specification and live article counts without exposing secrets."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parent.parent
private_spec=ROOT/'doc/project-status.json'
spec=json.loads(private_spec.read_text()) if private_spec.exists() else {'stage':'开源本地发布 MVP；公开路线图见 doc/open-source/03-路线图与进度.md','updated_on':'2026-10-02','milestones':[]}
print('阶段：'+spec['stage']+'；规格更新：'+spec['updated_on'])
for x in spec['milestones']:print(f"[{x['status']}] {x['name']}")
code="require 'new-project/app/src/bootstrap.php'; echo json_encode(query(\"SELECT s.id,s.host,COUNT(CASE WHEN a.status='published' THEN 1 END) published,COUNT(CASE WHEN a.status='draft' THEN 1 END) drafts FROM mvp_sites s LEFT JOIN mvp_articles a ON a.site_id=s.id GROUP BY s.id,s.host ORDER BY s.id\")->fetchAll());"
r=subprocess.run(['php','-r',code],cwd=ROOT,text=True,capture_output=True)
if r.returncode:print('实时数据：数据库暂不可读，以上为文档记录；详情查看本地服务日志。')
else:
 print('实时站点数据：')
 for site in json.loads(r.stdout):print(f"  {site['host']}: 已发布 {site['published']}，草稿 {site['drafts']}")
if private_spec.exists(): print('当前规格：doc/13-目录规范与项目进度.md；最新执行：doc/27-山城怪谈200篇执行记录.md；沪上记录：doc/26-沪上异闻200篇执行记录.md；京城记录：doc/25-京城夜谈累计210篇执行记录.md；街巷打包：doc/19-街巷奇闻200篇发布与打包记录.md；历史用量：doc/12-双模型六篇试写与实际用量.md')
