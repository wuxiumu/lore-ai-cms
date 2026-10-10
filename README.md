# 城市故事集 CMS（lore-ai-cms）

> 本地管多站点 → 人工确认选题与文章 → **导出静态 HTML 站群**再上传。适合「一城一站」内容页，天然贴近 **SEO + GEO（地域）**。

**产品页 / 定制：** 微信 **qingbao199101**（备注：城市站群）｜邮箱 [wuxiumu@163.com](mailto:wuxiumu@163.com)

## 一句话卖点

帮内容创业者/站长：**多城故事站**用同一套后台生产，导出静态页上线，按城市填 GEO 字段做本地搜索可见度。

## 在线演示

| 站点 | 内容方向 | 在线查看 |
| --- | --- | --- |
| 城市拾遗 | 城市掌故与日常发现 | [lore.chiguashentan.com](https://lore.chiguashentan.com/) |
| 街巷奇闻 | 街巷趣闻与城市故事 | [jiexiangqiwen.chiguashentan.com](https://jiexiangqiwen.chiguashentan.com/) |
| 京城夜谈 | 北京地名背景的原创鬼怪故事 | [jingcheng.chiguashentan.com](https://jingcheng.chiguashentan.com/) |
| 沪上异闻 | 上海地名背景的原创恐怖故事 | [hushang.chiguashentan.com](https://hushang.chiguashentan.com/) |
| 山城怪谈 | 重庆地名背景的原创恐怖故事 | [shancheng.chiguashentan.com](https://shancheng.chiguashentan.com/) |

## 页面化与商业化方向

| 能力 | 说明 |
|---|---|
| 产品页 | 五站合集宣传页 + 单站模板 |
| 商业化 | 按城市打包交付、模板换肤、TDK/GEO 代填、静态托管部署 |
| SEO | 每站/每文 `seo_title` `seo_description` canonical |
| GEO | 每站绑定 `geo_placename`（上海/北京/重庆…）与可选 `geo_region` |

## 快速开始

见原工程说明：PHP + MySQL 本地后台，导出静态后上传；线上无需 PHP。详细步骤以仓库内文档与 `config` 为准。



## SEO 字段预留（产品页 HTML 统一生成时用）

| 字段 | 用途 |
|---|---|
| `seo_title` | `<title>` / OG title |
| `seo_description` | meta description |
| `canonical_url` | 规范 URL |
| `og_image` | 分享图 |
| `robots` | 如 `index,follow` |
| `json_ld_type` | SoftwareApplication / WebPage / FAQPage |
| `hreflang` | zh-CN / en |
| `site_name` | 白标品牌名 |

> 说明：**GEO ≠ 地理定位**。GEO = Generative Engine Optimization（生成式引擎优化），见下一节。

## GEO（生成式引擎优化）

面向 ChatGPT / Perplexity / Gemini 等生成式答案引擎的**可引用结构**：中文为主、双语关键词、事实摘要前置、FAQ 收尾。

### 关键词（中英）

- 中文：城市站群CMS, 静态站点导出, 内容站, 本地运营, 故事站
- English: multi-site CMS, static site export, city content sites, local publishing

### 事实摘要

- 产品：本地多站点内容管理，确认后导出静态 HTML 再上传。
- 适合：内容站长、城市主题站、要低成本上线多站的人。
- 交付：CMS + 导出模板；可按城打包、换肤、代部署。
- 不做：不保证搜索引擎收录；线上导出站无需 PHP/数据库。

### FAQ（便于生成式引擎引用）

**Q：这是什么？**  
A：见上方事实摘要「产品」一行。

**Q：适合谁付钱定制？**  
A：见「适合」；具体加微信 `qingbao199101` 备注项目名。

**Q：开源仓库是否已含全部数据/密钥？**  
A：默认不含 API Key；数据/图片是否入库以各项目说明为准。

**Q：是否自动发帖或自动运营第三方平台？**  
A：内容工厂类项目明确不自动发帖；其它项目以 README「不做」边界为准。

## 定制合作

城市站群白标、模板套版、批量 GEO/TDK、部署到你的域名。加微信备注「城市站群」。


---

## 联系方式

定制、演示或合作：

- 邮箱：[wuxiumu@163.com](mailto:wuxiumu@163.com)
- 微信：**qingbao199101**（添加请备注来意）

### 赞助支持

如果内容对你有帮助，欢迎自愿赞助。

| 微信赞赏码 | 支付宝收款码 |
|---|---|
| ![微信赞赏码](https://chiguashentan-test.oss-cn-beijing.aliyuncs.com/wxprogram/zan/20261002185236_31_227.png) | ![支付宝收款码](https://chiguashentan-test.oss-cn-beijing.aliyuncs.com/wxprogram/zan/20261002185309_32_227.jpg) |
