<?php
if(PHP_SAPI!=='cli')exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$sid=(int)($argv[1]??0);if($sid!==2)throw new RuntimeException('Only explicitly authorized site 2');
$count=(int)query('SELECT COUNT(*) FROM mvp_articles WHERE site_id=2 AND id<>2')->fetchColumn();if($count!==200)throw new RuntimeException('Expected exactly200 real articles');
db()->beginTransaction();try {
 foreach(query('SELECT a.id,m.metadata FROM mvp_articles a LEFT JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.site_id=2 AND a.id<>2')->fetchAll() as $row){
 $meta=json_decode($row['metadata']??'{}',true)?:[];$meta['owner_review']=['approved'=>true,'mode'=>'user-default-approval','instruction'=>'继续，完成166篇，并默认全部通过，我要打包','at'=>date(DATE_ATOM)];
 query('INSERT INTO mvp_article_meta(article_id,metadata) VALUES(?,?) ON DUPLICATE KEY UPDATE metadata=VALUES(metadata)',[$row['id'],json_encode($meta,JSON_UNESCAPED_UNICODE)]);
 query('UPDATE mvp_articles SET status="published",published_at=COALESCE(published_at,NOW()),updated_at=NOW() WHERE id=?',[$row['id']]);
 }
 query('UPDATE mvp_editorial_jobs j JOIN mvp_articles a ON a.id=j.article_id SET j.status="published" WHERE a.site_id=2 AND a.id<>2');
 db()->commit();echo json_encode(['published'=>200,'seed_excluded'=>2]);
}catch(Throwable $e){db()->rollBack();throw $e;}
