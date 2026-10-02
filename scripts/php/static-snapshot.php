<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli') exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$sid=(int)($argv[1]??0);
db()->exec('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ'); db()->beginTransaction();
$site=query('SELECT * FROM mvp_sites WHERE id=?',[$sid])->fetch();
if(!$site) { fwrite(STDERR,"Unknown site\n"); exit(1); }
$articles=query("SELECT a.*,m.metadata FROM mvp_articles a LEFT JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.site_id=? AND a.status='published' ORDER BY a.published_at DESC,a.id DESC",[$sid])->fetchAll();
db()->commit();
$site['_theme']=themeRead($sid);
echo json_encode(['site'=>$site,'articles'=>$articles],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
