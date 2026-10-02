# 02 开源范围与 Git 提交

首版定位：个人站群内容管理及静态发布工具。采用 MIT 许可，新旧项目不合并发布。

公开：新项目应用、主题实例、根目录入口、脚本、公共文档和示例配置。

保留本机：旧项目（授权未核实）、`.local` 配置与模型结果、真实 catalogs、dist 产物、历史执行文档与个人进度。公开文档独立放入 `doc/open-source`，避免历史成本与业务记录进入公共仓库。当前 scripts 包含历史城市脚本，下一版本再做通用化，不宣称全部可用于任意新站。

## 首次提交

```sh
python3 scripts/release/check.py
# 查看忽略项和实际提交范围
git status --short --ignored
git add .
python3 scripts/release/check.py --staged
git diff --cached --stat
git diff --cached
# 检查结果通过且确认内容后
git commit -m "feat: initial local publishing MVP"
```

仓库地址和作者身份由维护者设置。创建空远程仓库后，执行 `git remote add origin <你的仓库地址>`，再 `git push -u origin main`。不要使用 `git add -f` 加入被忽略的业务数据。

## 首版完成标准

README 能定位安装条件和生成结果；敏感目录被忽略；提交内容检查通过；许可证说明只覆盖有权发布的新系统；真实内容和旧项目均不在暂存区。

全新机器端到端安装仍需完成后，才适合标记稳定版本。当前版本是 MVP，保留限制说明。
