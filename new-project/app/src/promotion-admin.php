<?php
declare(strict_types=1);
require_once __DIR__.'/promotion.php';
$config=promotionConfig();$sites=promotionSites();$file=ROOT.'/.local/promotion/index.html';
if(in_array($path,['/admin/promotion/download','/admin/promotion/preview'],true)) {
    if(!is_file($file))fail('请先生成宣传页面');
    header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'; base-uri 'none'");
    header('Content-Type: text/html; charset=utf-8');
    if($path==='/admin/promotion/download')header('Content-Disposition: attachment; filename="index.html"');
    readfile($file);return;
}
$error='';
if($isPost){
    $config=['title'=>trim((string)($_POST['title']??'')),'intro'=>trim((string)($_POST['intro']??'')),'footer'=>trim((string)($_POST['footer']??'')),'site_ids'=>array_values(array_intersect([1,2,8,9,10],array_map('intval',(array)($_POST['site_ids']??[]))))];
    if($config['title']==='' || mb_strlen($config['title'])>100 || mb_strlen($config['intro'])>1000 || mb_strlen($config['footer'])>500)$error='请填写标题（最多100字）；简介最多1000字，页脚最多500字。';
    else try{promotionSave($config);redirect('/admin/promotion?generated=1');}catch(Throwable $e){$error=$e->getMessage();}
}
$body=adminNav().'<section class="dashboard-title"><p class="eyebrow">PROMOTION PAGE · 人工操作</p><h1>宣传页面</h1><p>这是整个站群的宣传入口。勾选站点，生成一个内含 CSS 的 HTML 文件；上传到网站根目录即可使用。</p></section>';
if($error)$body.='<p class="notice error">'.h($error).'</p>';
if(isset($_GET['generated']))$body.='<p class="notice">宣传页面已重新生成，可以预览或下载。</p>';
$body.='<section class="panel"><form method="post">'.csrf().'<h2>1. 选择展示的站点</h2><p class="hint">跳转地址读取各站点设置中的正式地址；修改地址请进入站点设置。这里不切换当前管理的子站。</p>';
foreach($sites as $s)$body.='<p><label><input type="checkbox" name="site_ids[]" value="'.(int)$s['id'].'"'.(in_array((int)$s['id'],$config['site_ids'],true)?' checked':'').'> '.h($s['name']).' · '.h($s['base_url']).'</label></p>';
$body.='<h2>2. 编辑宣传文字</h2>'.field('页面标题','title',$config['title']).'<label>页面简介<textarea name="intro" rows="3">'.h($config['intro']).'</textarea></label>'.field('页脚文案','footer',$config['footer']).'<p><button>生成 / 更新 HTML</button></p><p class="hint">仅人工操作：不会调用大模型，也不会发布或修改文章。重新生成会替换上一版宣传文件。</p></form></section>';
if(is_file($file))$body.='<section class="panel"><h2>3. 预览与下载</h2><p>生成时间：'.date('Y-m-d H:i:s',filemtime($file)).' · '.number_format(filesize($file)/1024,1).' KB · 单个 index.html，无需外部 CSS、JS 或图片。</p><p><a href="/admin/promotion/preview" target="_blank" rel="noopener">打开预览 ↗</a> · <a href="/admin/promotion/download">下载 HTML 文件</a></p><p class="hint">上传到独立宣传站点根目录，或放入现有站点的子目录；替换已有 index.html 前请保留原文件。</p><iframe title="宣传页面预览" src="/admin/promotion/preview" width="100%" height="760" loading="lazy"></iframe></section>';
page('宣传页面',$body);
