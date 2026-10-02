# 城市故事集 · 本地站群内容管理与静态发布

用本地 PHP + MySQL 管理多个内容站点，人工确认选题与文章，按独立 HTML/CSS/JS 模板导出静态网站，手动上传到服务器。无需 Docker，线上不需要 PHP 或数据库。

当前为 **0.1.0 MVP**：适合个人内容网站的本地运营与静态发布。AI 生成通过单独脚本执行，模型账户与费用由使用者自行配置。程序不保证搜索引擎收录。

## 在线演示

[打开五站宣传页](https://img.chiguashentan.com/X/%E6%95%85%E4%BA%8B.html)，或直接进入下面的站点查看静态页面、文章与主题效果：

| 站点 | 内容方向 | 在线查看 |
| --- | --- | --- |
| 城市拾遗 | 城市掌故与日常发现 | [lore.chiguashentan.com](https://lore.chiguashentan.com/) |
| 街巷奇闻 | 街巷趣闻与城市故事 | [jiexiangqiwen.chiguashentan.com](https://jiexiangqiwen.chiguashentan.com/) |
| 京城夜谈 | 北京地名背景的原创鬼怪故事 | [jingcheng.chiguashentan.com](https://jingcheng.chiguashentan.com/) |
| 沪上异闻 | 上海地名背景的原创恐怖故事 | [hushang.chiguashentan.com](https://hushang.chiguashentan.com/) |
| 山城怪谈 | 重庆地名背景的原创恐怖故事 | [shancheng.chiguashentan.com](https://shancheng.chiguashentan.com/) |

这些是站长运营的演示网站，文章数据不随源码仓库发布；鬼怪故事为虚构，真实地名仅作背景。

## 已有功能

- 多站点管理、TDK 设置，后台四个业务入口保持当前站点。
- 文章增删改查、批量操作、草稿与发布状态。
- 选题目录、来源配置、人工确认，千问 / 智谱模型与 Key 设置。
- 每站 HTML 模板、独立 CSS / JS，静态 HTML、sitemap、robots 与 ZIP 导出。
- 宣传页选择站点、预览与下载单个内联 CSS 的 HTML。

## 本地快速开始

需要 Python 3.10+、PHP 8.3+（`pdo_mysql`、`mysqli`、`mbstring`）、运行中的 MySQL 8。Python 脚本使用标准库；本地脚本包含 Unix 功能，目前按 macOS / Linux 使用。

```sh
php -m                   # 检查上述 PHP 扩展
python3 project.py start
```

首次启动会创建独立数据库、运行账户、数据表和两个示例站点。默认尝试连接 `127.0.0.1` 的 MySQL root 空密码账户；有密码时先通过环境变量配置 `MVP_DB_ADMIN_HOST`、`MVP_DB_ADMIN_USER`、`MVP_DB_ADMIN_PASSWORD`，再启动。管理账户须有创建数据库、用户及授权的权限。程序不会重置已有配置。

打开 `http://localhost:8080/admin`，从本机 `.local/admin-credentials.txt` 读取初始密码，登录后修改。后台设置自己的域名、TDK、选题与内容。

```sh
python3 project.py status
python3 project.py build --site-id 1     # 读取站点设置中的正式域名
python3 project.py preview              # 静态预览
python3 project.py backup
python3 project.py stop
```

正式 ZIP 位于 `.local/releases/site-ID/`。解压后将网站文件上传到域名对应的根目录；上传前检查首页、链接、域名与 robots 设置。不要上传本项目根目录或 `.local`。

## AI 内容流程

后台配置模型 → 配置来源与目录提示词 → 生成目录 → 人工去重、确认 → 生成草稿 → 人工审阅发布 → 静态打包。

```sh
python3 project.py catalog-model --site-id 1 --provider qwen --limit 3
python3 project.py draft-qwen --site-id 1
```

先运行默认预览 / 执行计划；实际调用模型需要按对应脚本参数加 `--execute`。模型 Key 只保存在私有本地配置，不进入 Git。部分历史批处理脚本可能有发布动作，使用前阅读脚本，不把它们当作通用默认流程。引用材料应核对来源，虚构故事标明虚构。

## 目录与文档

| 路径 | 用途 |
| --- | --- |
| `new-project/app/` | 当前 PHP 应用与后台 |
| `new-project/themes/` | 站点主题实例 |
| `scripts/` | 本地运行、内容生成、静态发布与检查 |
| `project.py` | 根目录统一命令入口 |
| `doc/open-source/` | 公共架构、使用范围、路线图和发布说明 |
| `.local/` | 私有运行数据，不提交 |

[架构与边界](doc/open-source/01-架构与功能边界.md) · [开源与提交规划](doc/open-source/02-开源范围与Git提交.md) · [路线图](doc/open-source/03-路线图与进度.md)

## 当前限制

宣传页目前对应原有站点 ID `1/2/8/9/10`；全新安装只有两个示例站点，尚未改为任意站点选择。部分主题和批量写作脚本保留城市、分类及固定站点 ID，属于可参考的业务实例。PHP 内置服务用于本机开发，不是公网后台部署方案。尚未提供 Windows 支持、多用户权限、队列调度或完整 CI。

## 开源许可

本仓库纳入 Git 的新系统源码和文档使用 [MIT](LICENSE)。旧项目未纳入发布范围；真实文章、来源平台材料、模型服务及第三方内容不因本仓库许可证获得转载授权。禁止提交密钥、个人数据和数据库备份。
