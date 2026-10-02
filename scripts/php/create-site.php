<?php
if(PHP_SAPI!=='cli')exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$input=json_decode(stream_get_contents(STDIN),true,32,JSON_THROW_ON_ERROR);
$host=$input['host'];if(!filter_var($host,FILTER_VALIDATE_DOMAIN,FILTER_FLAG_HOSTNAME))throw new RuntimeException('Invalid host');
$existing=query('SELECT id FROM mvp_sites WHERE host=?',[$host])->fetchColumn();if($existing){echo json_encode(['id'=>(int)$existing,'existing'=>true]);exit;}
query('INSERT INTO mvp_sites(host,base_url,name,description,indexable,created_at,seo_title,seo_description,seo_keywords,content_topic,topic_keywords) VALUES(?,?,?,?,0,NOW(),?,?,?,?,?)',[$host,'http://'.$host.':8080',$input['name'],$input['description'],$input['name'],$input['description'],$input['keywords'],$input['theme'],$input['keywords']]);
$id=(int)db()->lastInsertId();themeInit($id);echo json_encode(['id'=>$id,'existing'=>false]);
