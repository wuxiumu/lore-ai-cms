<?php
$id=(int)($_GET['site_id']??2);
$s=query('SELECT * FROM mvp_sites WHERE id=?',[$id])->fetch();if(!$s) fail('站点不存在');
$file=(string)($_GET['file']??'layout.html');if(!in_array($file,themeFiles(),true)) fail('文件不存在');
$files=themeRead($id);$error='';
if($isPost) {
    $text=(string)($_POST['source']??'');
    if(strlen($text)>1000000) $error='文件最大 1 MB。';
    elseif($file==='layout.html' && (!str_contains($text,'{{head}}') || !str_contains($text,'{{content}}'))) $error='layout.html 必须保留 {{head}} 和 {{content}}，用于输出 TDK 与页面正文。';
    else {
        $target=themeDir($id).'/'.$file;
        $backup=ROOT.'/.local/theme-history/site-'.$id; if(!is_dir($backup)) mkdir($backup,0700,true);
        copy($target,$backup.'/'.date('Ymd-His').'-'.bin2hex(random_bytes(3)).'-'.$file);
        $tmp=tempnam(themeDir($id),'.save-');file_put_contents($tmp,$text);chmod($tmp,0644);rename($tmp,$target);
        redirect('/admin/theme?site_id='.$id.'&file='.rawurlencode($file).'&saved=1');
    }
}
$body=adminNav().'<section class="dashboard-title"><h1>'.h($s['name']).' · 页面主题</h1><p>直接编辑 HTML、CSS、JavaScript。每站一份文件；保存后本地立即生效，线上需要重新打包上传。</p><a href="http://site-'.$id.'.localhost:8080/" target="_blank">本地预览 ↗</a> · <a href="/admin/static?site_id='.$id.'">生成静态包</a></section><div class="chips">';
foreach(query('SELECT id,name FROM mvp_sites ORDER BY id') as $item) $body.='<a href="/admin/theme?site_id='.$item['id'].'">'.h($item['name']).'</a>';
$body.='</div><div class="chips">';foreach(themeFiles() as $name) $body.='<a href="/admin/theme?site_id='.$id.'&file='.$name.'"'.($name===$file?' aria-current="page"':'').'>'.h($name).'</a>';
$body.='</div>';if($error) $body.='<p class="notice error">'.h($error).'</p>';if(isset($_GET['saved'])) $body.='<p class="notice">已保存，旧版本保存在本机 .local/theme-history 中。</p>';
$body.='<section class="panel"><form method="post">'.csrf().textfield($file,'source',$isPost?(string)($_POST['source']??''):$files[$file],26).'<button>保存文件</button></form></section><section class="notice"><p>layout.html 是整页外壳；home / article / category / simple.html 是首页 / 文章 / 分类 / 其他页面的内容模板。style.css 和 script.js 分别是本站独立样式和脚本。</p><p>可用变量：{{head}}（仅外壳）、{{content}}、{{site_name}}、{{title}}、{{description}}、{{topic}}、{{year}}、{{canonical}}、{{about_url}}、{{css_url}}、{{js_url}}、{{nonce}}。文字变量自动转义。{{content}} 包含生成的正文与列表，可用自定义 HTML 包裹；移除后将不显示自动内容。</p><p>推荐把样式写在 style.css、脚本写在 script.js。HTML 内联脚本需要 nonce="{{nonce}}" 才能在本地执行。这里保存的是模板文本，不执行 PHP。</p></section>';
page('页面主题编辑',$body);
