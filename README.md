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

## 定制合作

城市站群白标、模板套版、批量 GEO/TDK、部署到你的域名。加微信备注「城市站群」。

## SEO / GEO 字段预留

> 做成独立产品页 / 站群页时，模板与配置预留下列字段（先占位，落地页或导出 HTML 时填入）。

| 字段 | 类型 | 用途 |
|---|---|---|
| `seo_title` | string | `<title>` / OG title |
| `seo_description` | string | meta description |
| `seo_keywords` | string[] | 可选关键词 |
| `canonical_url` | url | 规范链接 |
| `og_image` | url | 分享图 |
| `robots` | string | 如 `index,follow` |
| `json_ld_type` | string | 如 `SoftwareApplication` / `WebPage` / `FAQPage` |
| `geo_region` | string | 地域页：省/州代码或名称 |
| `geo_placename` | string | 城市/地标名（城市站、本地服务页） |
| `geo_position` | string | 可选 lat,long |
| `hreflang` | map | 多语言备用，如 `zh-CN` / `en` |
| `site_name` | string | 品牌名（白标） |


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

