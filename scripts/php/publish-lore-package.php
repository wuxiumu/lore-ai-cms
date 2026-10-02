<?php
if(PHP_SAPI!=='cli')exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$rows=query('SELECT a.id,m.metadata FROM mvp_articles a JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.site_id=1 AND a.id<>1')->fetchAll();
if(count($rows)!==200)throw new RuntimeException('Expected 200 articles');
db()->beginTransaction();try{foreach($rows as $row){$meta=json_decode($row['metadata'],true);$meta['publication_decision']=['mode'=>'owner-requested-package','instruction'=>'打包页应该包含200篇文章','at'=>date(DATE_ATOM),'model_review_retained'=>true];query('UPDATE mvp_article_meta SET metadata=? WHERE article_id=?',[json_encode($meta,JSON_UNESCAPED_UNICODE),$row['id']]);query('UPDATE mvp_articles SET status="published",published_at=COALESCE(published_at,NOW()),updated_at=NOW() WHERE id=?',[$row['id']]);}query('UPDATE mvp_editorial_jobs j JOIN mvp_articles a ON a.id=j.article_id SET j.status="published" WHERE a.site_id=1 AND a.id<>1');db()->commit();echo "Published 200; excluded seed id1; model reviews retained\n";}catch(Throwable $e){db()->rollBack();throw $e;}
