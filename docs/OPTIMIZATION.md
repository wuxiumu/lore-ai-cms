# lore-ai-cms · 深优化建议（文档先行）

> 与父仓 `docs/OPTIMIZATION-NEXT.md` Top2 对齐。  
> 轻量加固：✅ C1 PR（`.env.example` / `project.py build --dry-run` / 导出 SEO 说明）。**下列留给下一轮代码。**

## 现状对照

| 项 | 现状 |
|---|---|
| 入口 | `project.py` 调度 `scripts/publishing/build.py` 等 |
| Demo | 五站在线演示已在 README 表格 |
| 文档 | `SECURITY.md` / `CHANGELOG.md`；缺 `CUSTOM.md` 与上传示例 |
| 模板 | `new-project/` 存在；缺一城一站字段清单 |

## 建议（可执行）

| # | 建议 | 类型 | 验收 |
|---|---|---|---|
| 1 | 把 `python3 project.py build --dry-run` 写进 README「快速开始」第一屏 | 可运行 | 新人 5 分钟看到 dry-run 输出 |
| 2 | 单城交付模板：`sites/_template/` + TDK/GEO 字段清单（title/description/canonical/城市名） | 定制 | 复制模板即可新站 |
| 3 | 导出校验：缺 `canonical` / `description` 时 build 结束打印缺字段列表（非静默） | SEO | 缺字段即告警 exit≠0 或明确 WARN |
| 4 | 五站 Demo 截图进 `docs/samples/`（每站 1 张首页） | Demo | README 中部可浏览 |
| 5 | 套餐边界：`docs/CUSTOM.md`（含几次改稿、不含代运营/代写） | 文档 | 谈单可转发 |
| 6 | 静态导出后：`scripts/upload.example.sh`（nginx/OSS 上传示例，占位变量） | 可运行 | 跟脚本变量即可试传 |

## 建议落地顺序

1 → 3 → 2 → 6 → 5 → 4。

## 定制联系

微信 **qingbao199101**（备注：城市站群）· [wuxiumu@163.com](mailto:wuxiumu@163.com)
