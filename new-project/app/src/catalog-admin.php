<?php
$sid=(int)adminSelectedSite()['id'];$target=query('SELECT * FROM mvp_sites WHERE id=?',[$sid])->fetch();if(!$target)fail('站点不存在');
$base=ROOT.'/catalogs/site-'.$sid;if(!is_dir($base))mkdir($base,0755,true);
$prefsFile=$base.'/preferences.json';if(!is_file($prefsFile))copy(ROOT.'/scripts/editorial/preferences.example.json',$prefsFile);
$prefs=json_decode(file_get_contents($prefsFile),true);
function catalogCommand(array $args):bool {
 $pipes=[];$process=proc_open(array_merge(['python3',ROOT.'/scripts/editorial/catalog.py'],$args),[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,ROOT);
 if(!is_resource($process))return false;fclose($pipes[0]);$out=stream_get_contents($pipes[1]);fclose($pipes[1]);$err=stream_get_contents($pipes[2]);fclose($pipes[2]);$exit=proc_close($process);if($exit)error_log('Catalog command failed: '.substr($err,0,500));return $exit===0;
}
$directory=null;$latest=$base.'/latest.json';
if(is_file($latest)) {
 $candidate=realpath(json_decode(file_get_contents($latest),true)['directory']??'');$allowed=realpath($base);
 if($candidate && $allowed && str_starts_with($candidate,$allowed.DIRECTORY_SEPARATOR))$directory=$candidate;
}
$data=$directory?json_decode(file_get_contents($directory.'/catalog.json'),true):null;
if($path==='/admin/catalog/download') {
 $type=(string)($_GET['format']??'json');$files=['json'=>['catalog.json','application/json'],'csv'=>['catalog.csv','text/csv'],'md'=>['README.md','text/markdown']];
 if(!$directory || !isset($files[$type]))fail('目录文件不存在');[$filename,$mime]=$files[$type];
 header('Content-Type: '.$mime.'; charset=utf-8');header('Content-Disposition: attachment; filename="site-'.$sid.'-'.$filename.'"');readfile($directory.'/'.$filename);return;
}
$error='';
if($isPost) {
 $action=$_POST['action']??'';
 if($action==='model_collect'){
  $provider=$_POST['provider']??'';$limit=max(1,min(20,(int)($_POST['limit']??3)));
  if(!in_array($provider,['qwen','glm'],true))$error='请选择模型。';
  else{$pipes=[];$process=proc_open(['python3',ROOT.'/scripts/editorial/catalog_model.py','--site-id',(string)$sid,'--provider',$provider,'--limit',(string)$limit,'--execute'],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,ROOT);
   if(is_resource($process)){fclose($pipes[0]);$out=stream_get_contents($pipes[1]);fclose($pipes[1]);$err=stream_get_contents($pipes[2]);fclose($pipes[2]);$code=proc_close($process);if($code===0)redirect('/admin/catalog?site_id='.$sid.'&saved=1');$error='模型目录生成未完成，请检查来源和模型配置，原目录保留。';}else $error='无法启动目录生成脚本。';}
 } elseif(in_array($action,['preferences','collect'],true)) {
  try {
   $updated=json_decode((string)($_POST['preferences']??''),true,32,JSON_THROW_ON_ERROR);
   foreach(['cities','keywords','exclude','feeds'] as $key)if(!isset($updated[$key])||!is_array($updated[$key])||count($updated[$key])>100)throw new RuntimeException('invalid preferences');
   foreach(['cities','keywords','exclude'] as $key)foreach($updated[$key] as $value)if(!is_string($value)||mb_strlen($value)>120)throw new RuntimeException('invalid words');
   if(!is_string($updated['theme']??null))throw new RuntimeException('invalid theme');
   if(isset($updated['sources'])&&!is_array($updated['sources']))throw new RuntimeException('invalid sources');
   $updated['site_id']=$sid;$updated['use_hot_rank']=false;file_put_contents($prefsFile,json_encode($updated,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT),LOCK_EX);
   if($action==='collect' && !catalogCommand(['--site-id',(string)$sid,'--limit','30']))$error='收集失败，旧目录保留，请查看本地日志。';
   else redirect('/admin/catalog?site_id='.$sid.'&saved=1');
  } catch(Throwable $e) {$error='偏好配置需要合法 JSON，包含 cities、keywords、exclude、feeds 数组和 theme 字符串。';}
 } elseif($action==='import') {
  try {
   $incoming=json_decode((string)($_POST['import_json']??''),true,32,JSON_THROW_ON_ERROR);
   if(!is_array($incoming['items']??null)||count($incoming['items'])>100)throw new RuntimeException('invalid items');
   $new=$data?:['schema_version'=>1,'site_id'=>$sid,'site_name'=>$target['name'],'created_at'=>date(DATE_ATOM),'preferences'=>$prefs,'items'=>[],'source_errors'=>[],'workflow'=>'collect-review-draft'];
   foreach($incoming['items'] as $row){
    if(!is_array($row)||empty($row['title'])||mb_strlen($row['title'])>180||!in_array($row['story_type']??'',['fiction','folklore','nonfiction'],true)||!is_array($row['sources']??null)||($row['story_type']!=='fiction'&&empty($row['sources']))||count($row['sources'])>3)throw new RuntimeException('invalid row');
    foreach($row['sources'] as &$source){if(!filter_var($source['url']??'',FILTER_VALIDATE_URL)||!in_array(parse_url($source['url'],PHP_URL_SCHEME),['https','http'],true))throw new RuntimeException('invalid source');foreach(['title','publisher','date','role'] as $field)$source[$field]=(string)($source[$field]??'');}unset($source);
    $row=['title'=>(string)$row['title'],'city'=>(string)($row['city']??''),'description'=>(string)($row['description']??''),'story_type'=>$row['story_type'],'sources'=>$row['sources'],'id'=>bin2hex(random_bytes(6)),'selected'=>false,'provider'=>'','review_status'=>'pending','risk_reviewed'=>false,'duplicate_override'=>false,'notes'=>'','duplicate'=>['level'=>'clear','matches'=>[]],'risk_flags'=>[]];
    $new['items'][]=$row;
   }
   if(!$directory){$directory=$base.'/'.date('Ymd-His').'-'.bin2hex(random_bytes(3));mkdir($directory,0755,true);file_put_contents($latest,json_encode(['directory'=>$directory]));}
   $temp=tempnam($directory,'.import-');file_put_contents($temp,json_encode($new,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));rename($temp,$directory.'/catalog.json');
   if(!catalogCommand(['--refresh',$directory]))throw new RuntimeException('refresh failed');
   redirect('/admin/catalog?site_id='.$sid.'&saved=1');
  }catch(Throwable $e){$error='导入未完成：请使用提示词规定的 items JSON，每条包含标题、性质与公开来源；单次最多100条。';}
 } elseif($action==='select'  && $data) {
  $rows=$_POST['rows']??[];if(count($rows)!==count($data['items']))fail('目录表单不完整，请刷新重试；数据未保存。',422);
  foreach($data['items'] as &$item) {
   $row=$rows[$item['id']]??[];if(isset($row['delete'])){ $item['_delete']=true;continue; }$title=trim((string)($row['title']??$item['title']));$description=trim((string)($row['description']??$item['description']));$notes=trim((string)($row['notes']??''));
   if(!$title||mb_strlen($title)>180||mb_strlen($description)>1000||mb_strlen($notes)>1000){$error='标题需1—180字，描述和备注最多1000字。';break;}
   $kind=$row['story_type']??$item['story_type'];
   if(!in_array($kind,['nonfiction','folklore','fiction'],true)){$error='内容性质无效。';break;}
   try{$sources=json_decode((string)($row['sources']??json_encode($item['sources'])),true,16,JSON_THROW_ON_ERROR);if(!is_array($sources)||($kind!=='fiction'&&!$sources)||count($sources)>3)throw new RuntimeException();foreach($sources as $source)if(!is_array($source)||!filter_var($source['url']??'',FILTER_VALIDATE_URL)||!in_array(parse_url($source['url'],PHP_URL_SCHEME),['http','https'],true)||!isset($source['title'],$source['publisher'],$source['date']))throw new RuntimeException();}catch(Throwable $e){$error='来源需要合法JSON数组，最多3条；原创虚构可填[]，真实故事和传说仍需出处。';break;}
   $item['sources']=$sources;$item['story_type']=$kind;$item['city']=mb_substr(trim((string)($row['city']??$item['city'])),0,80);
   $item['title']=$title;$item['description']=$description;$item['notes']=$notes;$item['selected']=isset($row['selected']);$item['provider']=in_array($row['provider']??'',['qwen','glm'],true)?$row['provider']:'';
   $item['review_status']=$item['selected']?'approved':'pending';$item['risk_reviewed']=isset($row['risk_reviewed']);$item['duplicate_override']=isset($row['duplicate_override']);
  }unset($item);
  if(!$error) {
   $data['items']=array_values(array_filter($data['items'],fn($item)=>empty($item['_delete'])));
   $temp=tempnam($directory,'.save-');file_put_contents($temp,json_encode($data,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));rename($temp,$directory.'/catalog.json');
   if(catalogCommand(['--refresh',$directory]))redirect('/admin/catalog?site_id='.$sid.'&saved=1');
   $error='选择已保存，导出文件刷新失败；可用 catalog.json 继续操作。';
  }
 }
}
$body=adminNav().'<section class="dashboard-title"><h1>'.h($target['name']).' · 我的选题目录</h1><p>先看标题、描述和来源，再决定写哪些。人工配置与审核：普通导入、编辑和保存不调用模型；下方“调用模型生成目录”会消耗模型用量。AI 负责按提示词提供目录，以及通过脚本把已确认选题写成草稿。</p></section>';
if($error)$body.='<p class="notice error">'.h($error).'</p>';if(isset($_GET['saved']))$body.='<p class="notice">已保存。</p>';
$body.='<details class="panel"><summary>我的偏好 / 指定来源</summary><form method="post">'.csrf().textfield('偏好与来源 JSON：sources 配置资料网页；feeds 配置 RSS；可修改主题、城市、排除词','preferences',json_encode($prefs,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT),16).'<button name="action" value="preferences">保存偏好</button> <button name="action" value="collect">按偏好重新收集目录</button></form><p>种子选题按主题性质、城市和排除词过滤；新增 RSS 按城市及关键词匹配。收集不依赖热榜，保存偏好后需重新收集才应用。</p></details>';
$body.='<section class="panel"><h2>用已配置大模型生成目录</h2><p>先保存下方来源配置。支持 sources（具体资料网页）和 feeds（RSS）。先抓取公开来源，再让模型生成标题、简介和来源。新条目追加且默认待审；不会生成文章或发布。</p><form method="post">'.csrf().'<input type="hidden" name="action" value="model_collect"><label>模型<select name="provider"><option value="qwen">千问</option><option value="glm">智谱</option></select></label>'.field('新增选题数量（1—20）','limit',3,'number').'<button>调用模型生成目录（消耗用量）</button></form><p>生成需要等待，请勿重复提交。先在 <a href="/admin/models">模型配置</a> 保存 Key 和模型。</p></section>';
$body.='<details class="panel"><summary>如何让 AI 生成新目录？复制提示词</summary><p>下载现有目录 JSON，把它和已有文章标题交给支持联网的 AI，再粘贴下方提示词。AI 返回的目录需要人工导入和确认；网页不会发送 Key 或调用模型。</p>'.textfield('可复制提示词','catalog_prompt','你是我的私人网站选题助手，为《'.$target['name'].'》整理20个候选题。本站主题：'.$target['content_topic'].'；不按热榜排序。先阅读我提供的已有文章和目录，排除重复来源与相近话题。真实内容必须联网核验公开来源，不能编造链接、事实或人身指控；民间传说标为folklore；原创鬼故事标为fiction，来源只作城市背景。不要生成正文，不要替我确认或发布。
只返回 JSON：{"items":[{"title":"标题","city":"城市","story_type":"nonfiction/folklore/fiction 三者之一","description":"简介、我可能喜欢的角度及需复核的点","sources":[{"title":"资料标题","url":"已核验的公开链接","publisher":"发布方","date":"YYYY-MM-DD；未知则空字符串","role":"事实来源/传说资料/场景背景"}]}]}。
我的额外偏好：【填入】。已有文章及目录：【粘贴下载JSON和已有标题】。',12).'</details>';
$body.='<details class="panel"><summary>＋ 导入 AI 目录 / 人工新增选题</summary><form method="post">'.csrf().'<input type="hidden" name="action" value="import">'.textfield('粘贴 AI 返回的 JSON；人工新建也使用同一格式','import_json','',10).'<button>人工追加目录（不生成文章）</button></form><p>保留已有目录，新条目默认为未采用；导入后重新计算重复提示。</p></details>';
if($data) {
 if(isset($data['generation']['usage']))$body.='<p class="notice">最近一次目录生成：'.h($data['generation']['usage']['provider']).' · '.h($data['generation']['usage']['model_returned']).' · '.(int)$data['generation']['usage']['total_tokens'].' tokens。新目录项默认待审。</p>';
 $body.='<section class="panel"><p>'.count($data['items']).' 个候选 · '.h($data['created_at']).'</p><p><a href="/admin/catalog/download?site_id='.$sid.'&format=json">下载 JSON（脚本使用）</a> · <a href="/admin/catalog/download?site_id='.$sid.'&format=csv">下载 CSV（查看）</a> · <a href="/admin/catalog/download?site_id='.$sid.'&format=md">下载目录说明</a></p><p>勾选“采用”，分配模型，阅读来源后确认复核。重复项还需明确允许，并在备注说明不同角度。</p></section><form method="post">'.csrf().'<input type="hidden" name="action" value="select"><section class="panel"><label>批量模型<select id="bulk-0"><option value="">暂不分配</option><option value="qwen">千问</option><option value="glm">智谱</option></select></label><label class="check"><input type="checkbox" id="bulk-1"> 全选 / 取消采用</label><p>批量操作只改变表单，点击保存后生效。风险与重复复核仍逐条确认。</p></section>';
 $generated=[];
 foreach(query('SELECT a.id,a.status,m.metadata FROM mvp_articles a JOIN mvp_article_meta m ON m.article_id=a.id WHERE a.site_id=?',[$sid]) as $article) { $meta=json_decode($article['metadata'],true)?:[]; if(!empty($meta['catalog_id'])) $generated[$meta['catalog_id']]=[$article,$meta]; }
 foreach($data['items'] as $item) {
  if(isset($generated[$item['id']])) { [$article,$meta]=$generated[$item['id']]; $body.='<p class="notice">已生成：'.h($meta['generation']['provider']??'').' · '.h($article['status']==='draft'?'草稿':'已发布').' · <a href="/admin/article/preview?id='.$article['id'].'">阅读效果</a> · <a href="/admin/article?id='.$article['id'].'">编辑</a>'.(!empty($meta['review']['issues'])?' · 复核提示：'.h(implode('；',$meta['review']['issues'])):'').'</p>'; }
  $name='rows['.$item['id'].']';$kind=['nonfiction'=>'真实资料','folklore'=>'民间传说','fiction'=>'原创虚构鬼故事'][$item['story_type']]??'待分类';
  $body.='<section class="panel"><p class="eyebrow">'.h($item['city'].' · '.$kind.' · '.$item['id']).'</p>'.field('城市',$name.'[city]',$item['city']).'<label>内容性质<select name="'.$name.'[story_type]">'.implode('',array_map(fn($k)=>'<option value="'.$k.'"'.($item['story_type']===$k?' selected':'').'>'.h(['nonfiction'=>'真实资料','folklore'=>'民间传说','fiction'=>'原创虚构'][$k]).'</option>',['nonfiction','folklore','fiction'])).'</select></label>'.textfield('来源 JSON（人工可修改）',$name.'[sources]',json_encode($item['sources'],JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT),5).field('候选标题',$name.'[title]',$item['title']).textfield('描述 / 你想写的角度',$name.'[description]',$item['description'],2).'<ul>';
  foreach($item['sources'] as $source)$body.='<li><a href="'.h($source['url']).'" target="_blank" rel="noopener noreferrer">'.h($source['publisher'].'｜'.$source['title']).'</a> · '.h($source['date']?:'日期待核实').' · '.h($source['role']??'事实来源').'</li>';
  $body.='</ul><p>重复检查：'.h($item['duplicate']['level']).'</p>';
  foreach($item['duplicate']['matches'] as $match)$body.='<p class="notice">'.h($match['reason'].'：'.$match['title']).'</p>';
  $body.='<p>复核提示：'.h(implode('；',$item['risk_flags'])?:'未命中规则，仍需阅读来源。').'</p><label class="check"><input data-adopt type="checkbox" name="'.$name.'[selected]"'.($item['selected']?' checked':'').'> 采用此题（选题确认）</label><label>交给模型<select data-provider name="'.$name.'[provider]"><option value="">暂不分配</option><option value="qwen"'.($item['provider']==='qwen'?' selected':'').'>千问</option><option value="glm"'.($item['provider']==='glm'?' selected':'').'>智谱</option></select></label><label class="check"><input type="checkbox" name="'.$name.'[risk_reviewed]"'.($item['risk_reviewed']?' checked':'').'> 我已阅读来源与内容性质，确认复核提示</label><label class="check"><input type="checkbox" name="'.$name.'[duplicate_override]"'.($item['duplicate_override']?' checked':'').'> 即使相近仍允许生成（需在备注填写新角度）</label>'.textfield('备注 / 新角度 / 排除内容',$name.'[notes]',$item['notes'],2).'<label class="check"><input type="checkbox" name="'.$name.'[delete]"> 人工删除此目录项（保存后移除，不删除已有文章）</label></section>';
 }
 $body.='<button>人工批量保存目录修改</button></form><section class="notice"><p>保存后下载 JSON，或直接使用本机 catalog.json。生成脚本默认只预览执行计划；加 --execute 才调用模型。产物只存草稿，读过后在文章后台发布。</p><p>内容标记用于提示事实、传说、虚构和潜在问题，并不保证自动判断所有合规问题。</p></section>';
 foreach($data['source_errors'] as $e)$body.='<p>来源暂不可用：'.h($e['source'].' '.$e['error']).'</p>';
}
$body.='<script nonce="'.h(CSP_NONCE).'">document.getElementById("bulk-0").addEventListener("change",function(){this.form.querySelectorAll("[data-provider]").forEach(x=>x.value=this.value)});document.getElementById("bulk-1").addEventListener("click",function(){this.form.querySelectorAll("[data-adopt]").forEach(x=>x.checked=this.checked)});</script>';page('选题目录',$body);
