<?php
require __DIR__.'/../../new-project/app/src/bootstrap.php';
foreach([
[2,'jiexiangqiwen.chiguashentan.com','街巷奇闻','奇闻逸事、都市趣闻、城市里的反常识景观','奇闻,趣闻,街头,城市,地铁,空轨,重庆,武汉,天津','街巷奇闻 - 奇闻逸事与都市趣闻','发现城市里的奇闻逸事、反常识景观与街头故事，依据公开资料原创整理。'],
[1,'lore.chiguashentan.com','城市拾遗','城市掌故、地方文化与民俗故事，区分史实和传说','掌故,民俗,文化,历史,古镇,博物馆,城市,故事','城市拾遗 - 城市掌故与民俗故事','记录城市掌故、地方文化与民俗故事，让有出处的历史与传说得到清晰呈现。']
] as [$id,$host,$name,$topic,$keywords,$title,$description]) {
    $old=query('SELECT * FROM mvp_sites WHERE id=?',[$id])->fetch();
    if($old && in_array($old['host'],['localhost','127.0.0.1'],true)) {
        query('UPDATE mvp_sites SET host=?,base_url=?,name=?,description=?,seo_title=?,seo_description=?,seo_keywords=?,content_topic=?,topic_keywords=?,indexable=1 WHERE id=?',[$host,'https://'.$host,$name,$description,$title,$description,$keywords,$topic,$keywords,$id]);
        if($id===1) query("UPDATE mvp_articles SET status='draft' WHERE site_id=1 AND slug='build-a-useful-tool-library'");
    }
    themeInit($id);
}
echo "Two sites configured; existing content retained.\n";
