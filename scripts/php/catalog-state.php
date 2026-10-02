<?php
if(PHP_SAPI!=='cli') exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$id=(int)($argv[1]??2);$site=query('SELECT * FROM mvp_sites WHERE id=?',[$id])->fetch();if(!$site)exit(1);
$articles=query('SELECT a.id,a.site_id,a.title,a.slug,a.status,m.metadata FROM mvp_articles a LEFT JOIN mvp_article_meta m ON m.article_id=a.id ORDER BY a.id')->fetchAll();
echo json_encode(['site'=>$site,'articles'=>$articles],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
