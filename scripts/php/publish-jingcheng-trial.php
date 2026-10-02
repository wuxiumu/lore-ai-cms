<?php
if(PHP_SAPI!=='cli')exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$catalog=json_decode(file_get_contents(ROOT.'/.local/jingcheng-10/catalog.json'),true);$keys=array_column($catalog['items'],'id');$rows=[];
foreach(query('SELECT a.id,m.metadata FROM mvp_articles a JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.site_id=8')->fetchAll() as $r){$meta=json_decode($r['metadata'],true);if(in_array($meta['catalog_id']??'',$keys,true))$rows[]=[$r['id'],$meta];}
if(count($rows)!==10)throw new RuntimeException('Expected 10 trial stories');
db()->beginTransaction();try{foreach($rows as [$id,$meta]){$meta['publication_decision']=['mode'=>'owner-requested-local-preview','at'=>date(DATE_ATOM),'model_review_retained'=>true];query('UPDATE mvp_article_meta SET metadata=? WHERE article_id=?',[json_encode($meta,JSON_UNESCAPED_UNICODE),$id]);query('UPDATE mvp_articles SET status="published",published_at=COALESCE(published_at,NOW()),updated_at=NOW() WHERE site_id=8 AND id=?',[$id]);query('UPDATE mvp_editorial_jobs SET status="published" WHERE site_id=8 AND article_id=?',[$id]);}db()->commit();echo "Published 10 local preview stories; original trial draft retained\n";}catch(Throwable $e){db()->rollBack();throw $e;}
