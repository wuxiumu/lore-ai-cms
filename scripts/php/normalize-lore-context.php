<?php
if(PHP_SAPI!=='cli')exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$rows=query('SELECT m.article_id,m.metadata FROM mvp_article_meta m JOIN mvp_articles a ON a.id=m.article_id WHERE a.site_id=1 AND a.id<>1')->fetchAll();
foreach($rows as $r){$m=json_decode($r['metadata'],true);if(($m['workflow']??'')!=='owner-selected-catalog-draft')continue;$m['context_note']='据公开参考资料整理；访问日期不代表来源发表日期，史实与传说分别标注。';query('UPDATE mvp_article_meta SET metadata=? WHERE article_id=?',[json_encode($m,JSON_UNESCAPED_UNICODE),$r['article_id']]);}
echo 'Updated context notes: '.count($rows)."\n";
