<?php
if(PHP_SAPI!=='cli')exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
query('UPDATE mvp_sites SET host=?,base_url=?,name=?,description=?,indexable=1,seo_title=?,seo_description=?,seo_keywords=?,content_topic=?,topic_keywords=? WHERE id=8',['jingcheng.chiguashentan.com','https://jingcheng.chiguashentan.com','京城夜谈','北京街巷里的悬疑鬼故事，胡同旧事、夜班怪谈与都市传说。传说注明传说，原创明确虚构。','京城夜谈 - 北京鬼故事与胡同怪谈','夜深以后，聊聊北京胡同、末班车和老楼里的故事。原创虚构与有出处的传说分开标注。','北京鬼故事,京城夜谈,胡同怪谈,北京都市传说,悬疑故事','北京人愿意聊的鬼故事：胡同、夜班、老楼、末班车、雨夜与邻里旧物。注重悬念、人物与结尾回响。原创可无出处，明确虚构；传说有出处并标明传说，不把超自然当史实。','北京,鬼故事,胡同,悬疑,夜谈,都市传说']);echo "Updated site8 domain and theme\n";
