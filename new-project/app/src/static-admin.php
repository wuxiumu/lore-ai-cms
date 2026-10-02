<?php
$sid=(int)adminSelectedSite()['id'];
$selected=query('SELECT * FROM mvp_sites WHERE id=?',[$sid])->fetch();if(!$selected) fail('站点不存在');
$manifestPath=ROOT.'/.local/releases/site-'.$sid.'/latest.json';
if($path==='/admin/static/download') {
    if(!is_file($manifestPath)) fail('还没有生成静态包');
    $m=json_decode(file_get_contents($manifestPath),true);
    $file=realpath($m['zip']);$allowed=realpath(ROOT.'/.local/releases/site-'.$sid);
    if(!$file||!$allowed||!str_starts_with($file,$allowed.DIRECTORY_SEPARATOR)) fail('文件不可用');
    header('Content-Type: application/zip');header('Content-Disposition: attachment; filename="'.basename($file).'"');header('Content-Length: '.filesize($file));readfile($file);return;
}
$error='';
if($isPost) {
    $command=['python3',ROOT.'/scripts/publishing/build.py','--site-id',(string)$sid];
    $pipes=[];$process=proc_open($command,[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,ROOT);
    if(!is_resource($process)) $error='无法运行构建程序，请从终端执行 publishing/build.py。';
    else {
        fclose($pipes[0]);$out=stream_get_contents($pipes[1]);fclose($pipes[1]);$err=stream_get_contents($pipes[2]);fclose($pipes[2]);$code=proc_close($process);
        if($code===0) redirect('/admin/static?site_id='.$sid.'&built=1');
        $error='生成失败，请检查地址格式与本机 PHP / Python 环境。旧包仍保留。';error_log('Static build failed: '.substr($err,0,1000));
    }
}
$m=is_file($manifestPath)?json_decode(file_get_contents($manifestPath),true):null;
$counts=query('SELECT SUM(status="published") published,SUM(status="draft") drafts FROM mvp_articles WHERE site_id=?',[$sid])->fetch();
$body=adminNav().'<section class="dashboard-title"><p class="eyebrow">STATIC PUBLISHING</p><h1 class="publishing-site-title">'.h($selected['name']).' · 静态打包</h1><p>线上只需要解压后的 HTML 和资源文件，无需 PHP、数据库或模型密钥。</p></section>';
if($error) $body.='<p class="notice error">'.h($error).'</p>';
if(isset($_GET['built'])) $body.='<p class="notice">静态包已生成，下面可以下载。</p>';
$body.='<section class="panel narrow"><h2>'.h($selected['name']).'</h2><p>当前可打包：<strong>'.(int)$counts['published'].' 篇已发布文章</strong>；草稿 '.(int)$counts['drafts'].' 篇（不进入线上包）。<a href="/admin/articles?site_id='.$sid.'">管理文章与发布状态</a></p><p>上线地址：'.h($selected['base_url']).'</p><p><a href="/admin/site?id='.$sid.'">修改站点设置 / TDK</a> · <a href="/admin/theme?site_id='.$sid.'">修改页面主题</a></p><form method="post">'.csrf().'<button>生成 HTML 并打包 ZIP</button></form><p>自动使用本站已保存的域名和独立主题。</p></section>';
if($m) {
    if((int)$m['article_count']!==(int)$counts['published'])$body.='<p class="notice">上次包包含 '.(int)$m['article_count'].' 篇，当前已发布 '.(int)$counts['published'].' 篇。请重新生成后下载，旧包不会自动更新。</p>';
    $body.='<section class="panel"><h2>上次生成的包</h2><p><span class="badge">'.($m['mode']==='production'?'线上包':'本地预览包 · 禁止收录').'</span></p><p>'.(int)$m['article_count'].' 篇文章 · '.(int)$m['html_count'].' 个 HTML 页面 · '.h($m['created_at']).'</p><p>站点地址：'.h($m['base_url']).'</p><a class="button" href="/admin/static/download?site_id='.$sid.'">下载 ZIP</a> <a class="button secondary" href="http://site-'.$sid.'.localhost:8081/" target="_blank" rel="noopener">查看纯静态预览</a><h3>上传方式</h3><p>解压 ZIP，将里面的 index.html、article、category、covers 等直接上传到网站根目录。不要上传外层文件夹，也不要上传本地代码或数据库。</p>';
    if($m['stale_files']) { $body.='<h3>旧包可能遗留的文件</h3><p>如果线上有这些旧文件，请一并移除，避免下架文章仍可访问。</p><pre>'.h(implode("\n",$m['stale_files'])).'</pre>'; }
    $body.='</section>';
}
page('静态打包发布',$body);
