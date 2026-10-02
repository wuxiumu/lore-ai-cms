<?php
if(PHP_SAPI!=='cli')exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$summary=json_decode(file_get_contents(ROOT.'/.local/beijing-places-50/summary.json'),true);
if(($summary['new_articles']??0)!==50||!empty($summary['issues']))throw new RuntimeException('50-story audit must pass first');
$catalog=json_decode(file_get_contents(ROOT.'/.local/beijing-places-50/catalog.json'),true);$ids=array_column($catalog['items'],'id');$rows=[];
foreach(query('SELECT a.id,m.metadata FROM mvp_articles a JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.site_id=8')->fetchAll() as $row){$meta=json_decode($row['metadata'],true);if(in_array($meta['catalog_id']??'',$ids,true))$rows[]=[$row['id'],$meta];}
if(count($rows)!==50)throw new RuntimeException('Expected 50 matching stories');
db()->beginTransaction();try{query('SELECT id FROM mvp_sites WHERE id=8 FOR UPDATE');foreach($rows as [$id,$meta]){if(($meta['review']['approved']??false)!==true)throw new RuntimeException('Model review requires follow-up');$meta['publication_decision']=['mode'=>'owner-requested-local-preview','instruction'=>'先做好目录，再执行50篇北京背景鬼怪小故事，不涉及军和政','at'=>date(DATE_ATOM),'model_review_retained'=>true];query('UPDATE mvp_article_meta SET metadata=? WHERE article_id=?',[json_encode($meta,JSON_UNESCAPED_UNICODE),$id]);query('UPDATE mvp_articles SET status="published",published_at=COALESCE(published_at,NOW()),updated_at=NOW() WHERE id=? AND site_id=8',[$id]);query('UPDATE mvp_editorial_jobs SET status="published" WHERE article_id=? AND site_id=8',[$id]);}db()->commit();echo "Published 50 new stories; earlier10 retained; original draft unchanged\n";}catch(Throwable $e){db()->rollBack();throw $e;}
