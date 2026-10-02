<?php
declare(strict_types=1);
require __DIR__.'/../src/bootstrap.php';
require __DIR__.'/../src/editorial.php';
define('CSP_NONCE',base64_encode(random_bytes(18)));
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('Referrer-Policy: strict-origin-when-cross-origin');
header("Content-Security-Policy: default-src 'self'; script-src 'nonce-".CSP_NONCE."'; style-src 'self'; img-src 'self' data:; form-action 'self'; frame-ancestors 'self'; base-uri 'none'");
set_exception_handler(function(Throwable $e) { error_log($e->__toString()); fail('服务暂时不可用，请查看本地日志',500); });
$host=strtolower(parse_url('http://'.($_SERVER['HTTP_HOST']??''),PHP_URL_HOST)??'');
$local=in_array($host,['localhost','127.0.0.1','::1'],true)||preg_match('/^site-[1-9][0-9]*\.localhost$/',$host);
$hostSite=preg_match('/^site-([1-9][0-9]*)\.localhost$/',$host,$localMatch)?(int)$localMatch[1]:0;
$previewId=$local?($hostSite?:(int)($_GET['site_id']??($_COOKIE['preview_site']??($host==='localhost'?1:2)))):0;
$site=$previewId?query('SELECT * FROM mvp_sites WHERE id=?',[$previewId])->fetch():query('SELECT * FROM mvp_sites WHERE host=?',[$host])->fetch();
if($local && $site) { setcookie('preview_site',(string)$site['id'],['path'=>'/','httponly'=>true,'samesite'=>'Lax']); $site['indexable']=0; }
if (!$site) fail('未配置此域名',404);
$path=parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH) ?: '/';
if (str_starts_with($path,'/admin')) {
    session_name('station_admin');
    session_set_cookie_params(['httponly'=>true,'samesite'=>'Lax','secure'=>(!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS']!=='off'),'path'=>'/admin']);
    session_start();
    header('Cache-Control: no-store');
    header('X-Robots-Tag: noindex, nofollow');
    require __DIR__.'/../src/admin.php'; exit;
}
if (!in_array($_SERVER['REQUEST_METHOD'],['GET','HEAD'],true)) { header('Allow: GET, HEAD'); fail('不支持此请求方式',405,$site); }
$base=rtrim($site['base_url'],'/');
if (!indexable($site)) header('X-Robots-Tag: noindex, nofollow');
if ($path==='/about') {
    page('关于本站',((int)$site['id']===9?hushang_about($site):((int)$site['id']===10?shancheng_about($site):((int)$site['id']===8?jingcheng_about($site):'<article class="reading"><p class="eyebrow">ABOUT THE JOURNAL</p><h1>好奇有据，阅读有趣。</h1><p class="lead">'.h($site['description']).'</p><div class="prose"><h2>我们写什么</h2><p>关注城市里的反常识景观、日常趣事与有依据的奇闻。用清晰的解释，补上短视频画面之外的背景。</p><h2>内容如何产生</h2><p>以公开热门话题作为选题线索，依据可查来源原创整理，使用 AI 辅助写作。文章会标明资料日期，历史事件不作为刚刚发生的新闻发布。示意插画不会伪装成现场照片。</p><h2>如何核对信息</h2><p>每篇文章附有资料链接。涉及开放时间、票价和现场安排时，请以运营方的最新公告为准。若发现错误，可在管理后台将文章退回草稿后修正。</p></div></article>'))),$site,'了解'. $site['name'].'的选题范围、资料来源与编辑方式。',$base.'/about'); exit;
}
if ($path==='/robots.txt') {
    header('Content-Type: text/plain; charset=utf-8');
    echo indexable($site)?"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /search\nSitemap: $base/sitemap.xml\n":"User-agent: *\nDisallow: /\n"; exit;
}
if ($path==='/sitemap.xml') {
    header('Content-Type: application/xml; charset=utf-8');
    $count=(int)query("SELECT COUNT(*) FROM mvp_articles WHERE site_id=? AND status='published'",[$site['id']])->fetchColumn();
    $chunks=max(1,(int)ceil($count/1000));
    echo '<?xml version="1.0" encoding="UTF-8"?>';
    if (!isset($_GET['page']) && $chunks>1) {
        echo '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">';
        for($i=1;$i<=$chunks;$i++) echo '<sitemap><loc>'.h($base.'/sitemap.xml?page='.$i).'</loc></sitemap>';
        echo '</sitemapindex>'; exit;
    }
    $p=filter_var($_GET['page']??1,FILTER_VALIDATE_INT);
    if (!$p || $p<1 || $p>$chunks) { http_response_code(404); exit; }
    echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">';
    if ($p===1) {
        echo '<url><loc>'.h($base.'/').'</loc></url><url><loc>'.h($base.'/about').'</loc></url>';
        foreach(query("SELECT DISTINCT category FROM mvp_articles WHERE site_id=? AND status='published' ORDER BY category",[$site['id']]) as $c) echo '<url><loc>'.h($base.'/category/'.rawurlencode($c['category'])).'</loc></url>';
    }
    $offset=($p-1)*1000;
    foreach(query("SELECT slug,updated_at FROM mvp_articles WHERE site_id=? AND status='published' ORDER BY id LIMIT 1000 OFFSET $offset",[$site['id']]) as $a) echo '<url><loc>'.h($base.'/article/'.$a['slug'].'.html').'</loc><lastmod>'.h(date(DATE_ATOM,strtotime($a['updated_at']))).'</lastmod></url>';
    echo '</urlset>'; exit;
}
if (preg_match('~^/article/([a-z0-9][a-z0-9-]{0,159})\.html$~',$path,$m)) {
    $a=query("SELECT * FROM mvp_articles WHERE site_id=? AND slug=? AND status='published'",[$site['id'],$m[1]])->fetch();
    if (!$a) fail('文章不存在或尚未发布',404,$site);
    $meta=editorial_meta((int)$a['id']);
    if(!empty($meta['keywords'])) $site['seo_keywords']=implode(',',array_filter($meta['keywords'],'is_string'));
    $body='<div class="breadcrumbs"><a href="/">首页</a> / <a href="/category/'.rawurlencode($a['category']).'">'.h($a['category']).'</a></div><article class="reading"><p class="eyebrow">'.h($a['category']).'</p><h1>'.h($a['title']).'</h1><p class="meta">发布于 '.h(substr($a['published_at'],0,10)).' · 更新于 '.h(substr($a['updated_at'],0,10)).'</p><p class="lead">'.h($a['description']).'</p>'.cover_html($meta,$a['title']).'<p class="byline">'.h($meta['author']??$site['name'].'编辑部').' · 约 '.max(1,(int)ceil(mb_strlen($a['content'])/400)).' 分钟阅读</p><div class="prose">';
    $body.=render_story($a['content']);
    $body.='</div>'.story_sources($meta).'</article><section class="related"><h2>继续阅读</h2>';
    foreach(query("SELECT title,slug FROM mvp_articles WHERE site_id=? AND status='published' AND id<>? ORDER BY (category=?) DESC,published_at DESC LIMIT 4",[$site['id'],$a['id'],$a['category']]) as $r) $body.='<p><a href="/article/'.h($r['slug']).'.html">'.h($r['title']).' →</a></p>';
    $body.='<a href="/">返回全部文章 →</a></section>';
    $structured=['@context'=>'https://schema.org','@type'=>'Article','headline'=>$a['title'],'description'=>$a['description'],'datePublished'=>date(DATE_ATOM,strtotime($a['published_at'])),'dateModified'=>date(DATE_ATOM,strtotime($a['updated_at'])),'inLanguage'=>'zh-CN','mainEntityOfPage'=>$base.$path,'author'=>['@type'=>'Organization','name'=>$meta['author']??$site['name'].'编辑部'],'publisher'=>['@type'=>'Organization','name'=>$site['name']],'articleSection'=>$a['category']];
    page($a['title'],$body,$site,$a['description'],$base.$path,false,$structured); exit;
}
$category=null;
if (preg_match('~^/category/([^/]+)$~',$path,$m)) $category=rawurldecode($m[1]);
if ($path!=='/' && $path!=='/search' && $category===null) fail('页面不存在',404,$site);
$q=trim((string)($_GET['q']??''));
$p=filter_var($_GET['page']??1,FILTER_VALIDATE_INT);
if (!$p || $p<1 || $p>100000) fail('分页不存在',404,$site);
$where="site_id=? AND status='published'"; $args=[$site['id']];
if ($category!==null) { $where.=' AND category=?'; $args[]=$category; }
if ($path==='/search' && $q!=='') { $where.=' AND (title LIKE ? OR content LIKE ?)'; $args[]='%'.$q.'%'; $args[]='%'.$q.'%'; }
$count=(int)query("SELECT COUNT(*) FROM mvp_articles WHERE $where",$args)->fetchColumn();
$pages=max(1,(int)ceil($count/12));
if ($p>$pages || ($category!==null && !$count)) fail('页面不存在',404,$site);
$title=$path==='/search'?'搜索结果':($category ?? ($site['name']==='街巷奇闻'?'奇闻逸事与都市趣闻':'精选内容'));
if ($p>1) $title.=' · 第 '.$p.' 页';
$body='<section class="hero"><p class="eyebrow">'.($path==='/search'?'SEARCH':($site['name']==='街巷奇闻'?'城市有故事 · 好奇有答案':'独立记录 / 持续分享')).'</p><h1>'.h($category ?? ($path==='/search'?'发现你需要的内容':$site['name'])).'</h1><p class="lead">'.h($site['description']).'</p><form action="/search" method="get" class="search"><input aria-label="搜索文章" name="q" placeholder="搜一座城，或一件好奇的事…" value="'.h($q).'"><button>搜索 →</button></form></section><div class="section-heading"><h2>'.h($title).'</h2><span>'.$count.' 篇文章</span></div><div class="chips"><a href="/">全部</a>';
foreach(query("SELECT DISTINCT category FROM mvp_articles WHERE site_id=? AND status='published' ORDER BY category",[$site['id']]) as $c) $body.='<a href="/category/'.rawurlencode($c['category']).'">'.h($c['category']).'</a>';
$body.='</div><div class="cards">'; $offset=($p-1)*12;
foreach(query("SELECT a.*,m.metadata FROM mvp_articles a LEFT JOIN mvp_article_meta m ON m.article_id=a.id WHERE $where ORDER BY published_at DESC,a.id DESC LIMIT 12 OFFSET $offset",$args) as $a) $body.='<article class="card">'.cover_html(json_decode($a['metadata']??'{}',true),$a['title'],true).'<p class="eyebrow">'.h($a['category']).'</p><h2><a href="/article/'.h($a['slug']).'.html">'.h($a['title']).'</a></h2><p>'.h($a['description']).'</p><div class="card-foot"><span>'.h(substr($a['published_at'],0,10)).'</span><a href="/article/'.h($a['slug']).'.html">阅读全文 ↗</a></div></article>';
if (!$count) $body.='<div class="empty">暂无匹配的文章。换个关键词，或在后台发布第一篇内容。</div>';
$body.='</div><div class="pagination">';
for($i=max(1,$p-2);$i<=min($pages,$p+2);$i++) $body.='<a href="'.h($path.'?'.http_build_query(array_filter(['q'=>$path==='/search'?$q:null,'page'=>$i],fn($x)=>$x!==null))).'">'.$i.'</a>';
$body.='</div>';
page($title,$body,$site,$category!==null?$category.'：'.$site['description']:'',$base.$path.($p>1?'?page='.$p:''),$path==='/search');
