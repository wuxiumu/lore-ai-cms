from pathlib import Path
import json,concurrent.futures
from pipeline import fetch,plain
ROOT=Path(__file__).resolve().parents[2]
items=[
('qwen','liziba-train-building','李子坝列车穿楼：轨道和住宅怎样相处','https://www.cq.gov.cn/ywdt/jrcq/202111/t20211125_10030692.html','重庆市人民政府','重庆轨道交通建设攻克了哪些难题？','2021-11-25'),
('qwen','wukang-building-corner','武康大楼为什么像一艘停在街角的船','https://www.xuhui.gov.cn/zfjg_qzfbm_fgj_bmdt/20230128/509539.html','上海市徐汇区人民政府','壹月 | 转角遇见 武康大楼','2023-01-28'),
('qwen','guangzhou-qilou-arcade','广州骑楼：为什么房子下面留出一条走廊','https://www.gz.gov.cn/zlgz/whgz/content/post_8564096.html','广州市人民政府','百年骑楼筑老城肌理 廊下烟火延千载商脉',''),
('glm','quanzhou-oyster-shell-houses','泉州蟳埔的墙为什么镶着一层牡蛎壳','https://www.fujian.gov.cn/zwgk/ztzl/sxzygwzxsgzx/sdjj/wvjj/202401/t20240123_6384984.htm','福建省人民政府','当“簪花围”遇上“蚵壳厝”','2024-01-23'),
('glm','fuzhou-heart-camphor-tree','福州烟台山比心树：半颗爱心怎么让路人停下脚步','https://www.fuzhou.gov.cn/zgfzzt/zjrc/rcyx/202605/t20260514_5321946.htm','福州市人民政府','烟台山“比心”香樟树走红','2026-05-14'),
('glm','harbin-snowman-winter-2025','哈尔滨大雪人：2025年冬天的19米笑脸怎样造出来','https://news.cctv.cn/2025/12/04/ARTI3LVryvAphjxYaOPgvB9D251204.shtml','央视网','19米高！用雪超3000立方米 哈尔滨的“大雪人”又开工了','2025-12-04')]
def read(row):
 provider,key,topic,url,publisher,title,date=row
 try:
  text=plain(fetch(url))
  return {'provider':provider,'key':key,'topic':topic,'sources':[{'url':url,'publisher':publisher,'title':title,'date':date}],'source_text':text,'selection':'人工选定的长期城市趣闻，非今日热榜'}
 except Exception as e:return {'provider':provider,'key':key,'error':type(e).__name__}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:data=list(pool.map(read,items))
p=ROOT/'.local/comparison';p.mkdir(exist_ok=True)
(p/'sources.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
for a in data:print(a['key'],a.get('error','OK'),len(a.get('source_text','')))
