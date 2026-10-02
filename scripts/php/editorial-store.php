<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli') exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
try {
    $in=json_decode(stream_get_contents(STDIN),true,512,JSON_THROW_ON_ERROR);
    $sid=(int)($in['site_id']??0);
    $site=query('SELECT * FROM mvp_sites WHERE id=?',[$sid])->fetch();
    if(!$site) throw new RuntimeException('Unknown site');
    if($in['action']==='state') {
        echo json_encode(['site'=>$site,'jobs'=>query('SELECT topic_key,status,title,article_id FROM mvp_editorial_jobs WHERE site_id=?',[$sid])->fetchAll(),'recent_titles'=>query('SELECT title FROM mvp_articles WHERE site_id=? ORDER BY id DESC LIMIT 200',[$sid])->fetchAll(),'today'=>(int)query("SELECT COUNT(*) FROM mvp_editorial_jobs WHERE site_id=? AND created_at>=CURDATE()",[$sid])->fetchColumn()],JSON_UNESCAPED_UNICODE); exit;
    }
    if($in['action']!=='publish') throw new RuntimeException('Unsupported action');
    $a=$in['article']; $key=$in['topic_key']; $meta=$in['metadata'];
    if(!preg_match('/^[a-f0-9]{64}$/',$key)||!preg_match('/^[a-z0-9][a-z0-9-]{0,159}$/',$a['slug'])) throw new RuntimeException('Invalid key or slug');
    foreach(['title'=>180,'description'=>500,'category'=>80] as $k=>$limit) if(!is_string($a[$k])||mb_strlen($a[$k])<1||mb_strlen($a[$k])>$limit) throw new RuntimeException('Invalid '.$k);
    if(!is_string($a['content'])||mb_strlen($a['content'])<400||mb_strlen($a['content'])>9000) throw new RuntimeException('Invalid content length');
    if(!in_array($in['status'],['published','draft'],true)) throw new RuntimeException('Invalid status');
    db()->beginTransaction();
    // Lock site row to serialize publications and enforce daily cap across processes.
    query('SELECT id FROM mvp_sites WHERE id=? FOR UPDATE',[$sid]);
    $old=query('SELECT article_id FROM mvp_editorial_jobs WHERE site_id=? AND topic_key=?',[$sid,$key])->fetch();
    if($old) { db()->rollBack(); echo json_encode(['skipped'=>true,'article_id'=>$old['article_id']]); exit; }
    $today=(int)query('SELECT COUNT(*) FROM mvp_editorial_jobs WHERE site_id=? AND created_at>=CURDATE()',[$sid])->fetchColumn();
    if($today>=max(1,min(200,(int)($in['daily_limit']??3)))) throw new RuntimeException('Daily limit reached');
    query('INSERT INTO mvp_articles(site_id,slug,title,description,category,content,status,published_at,updated_at) VALUES(?,?,?,?,?,?,?,?,NOW())',[$sid,$a['slug'],$a['title'],$a['description'],$a['category'],$a['content'],$in['status'],$in['status']==='published'?date('Y-m-d H:i:s'):null]);
    $id=(int)db()->lastInsertId();
    query('INSERT INTO mvp_article_meta(article_id,metadata) VALUES(?,?)',[$id,json_encode($meta,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR)]);
    query('INSERT INTO mvp_editorial_jobs(site_id,topic_key,article_id,status,title,created_at) VALUES(?,?,?,?,?,NOW())',[$sid,$key,$id,$in['status'],$a['title']]);
    db()->commit(); echo json_encode(['article_id'=>$id,'status'=>$in['status'],'url'=>$site['base_url'].'/article/'.$a['slug'].'.html'],JSON_UNESCAPED_UNICODE);
} catch(Throwable $e) { if(db()->inTransaction()) db()->rollBack(); fwrite(STDERR,'Editorial store failed: '.$e->getMessage()."\n"); exit(1); }
