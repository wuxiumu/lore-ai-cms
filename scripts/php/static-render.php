<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli') exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
require __DIR__.'/../../new-project/app/src/editorial.php';
define('STATIC_EXPORT',true);
$input=json_decode(stream_get_contents(STDIN),true,512,JSON_THROW_ON_ERROR);
$site=$input['site']; $articles=$input['articles']; $base=rtrim($input['base_url'],'/');
$site['base_url']=$base; $site['host']=parse_url($base,PHP_URL_HOST); $site['indexable']=$input['production'];
$pages=[]; $urls=[]; $categories=[];
foreach($articles as &$a) { $a['meta']=json_decode($a['metadata']??'{}',true)?:[]; $categories[$a['category']][]=$a; } unset($a);
function caturl(string $name,int $p=1):string { return '/category/'.substr(hash('sha256',$name),0,12).($p>1?'-'.$p:'').'.html'; }
function articleurl(array $a):string { return '/article/'.$a['slug'].'.html'; }
function emitpage(string $path,string $title,string $body,string $description='',bool $noindex=false,array $schema=[]):void {
    global $pages,$site,$base,$urls;
    ob_start(); page($title,$body,$site,$description,$base.$path,$noindex,$schema);$html=ob_get_clean();
    $html=str_replace(['href="/about"','action="/search"'],['href="/about.html"','action="/search.html"'],$html);
    $pages[$path==='/'?'index.html':ltrim($path,'/')]=$html;
    if(!$noindex) $urls[]=$path;
}
function card(array $a):string { return '<article class="card">'.cover_html($a['meta'],$a['title'],true).'<p class="eyebrow">'.h($a['category']).'</p><h2><a href="'.articleurl($a).'">'.h($a['title']).'</a></h2><p>'.h($a['description']).'</p><div class="card-foot"><span>'.h(substr($a['published_at'],0,10)).'</span><a href="'.articleurl($a).'">阅读全文 ↗</a></div></article>'; }
$groups=[''=> $articles]+$categories;
foreach($groups as $category=>$items) {
    $total=max(1,(int)ceil(count($items)/12));
    for($p=1;$p<=$total;$p++) {
        $path=$category!==''?caturl($category,$p):($p===1?'/':'/page/'.$p.'.html');
        $heading=$category!==''?$category:$site['name'];
        $body='<section class="hero"><p class="eyebrow">城市有故事 · 好奇有答案</p><h1>'.h($heading).'</h1><p class="lead">'.h($site['description']).'</p><form action="/search.html" method="get" class="search"><input aria-label="搜索文章" name="q" placeholder="搜一座城，或一件好奇的事…"><button>搜索 →</button></form></section><div class="section-heading"><h2>'.($category!==''?h($category):'奇闻逸事与都市趣闻').'</h2><span>'.count($items).' 篇文章</span></div><div class="chips"><a href="/">全部</a>';
        foreach(array_keys($categories) as $name) $body.='<a href="'.caturl($name).'">'.h($name).'</a>';
        $body.='</div><div class="cards">';
        foreach(array_slice($items,($p-1)*12,12) as $a) $body.=card($a);
        if(!$items) $body.='<p>内容正在整理中。</p>';
        $body.='</div><div class="pagination">';
        for($i=max(1,$p-2);$i<=min($total,$p+2);$i++) $body.='<a href="'.($category!==''?caturl($category,$i):($i===1?'/':'/page/'.$i.'.html')).'"'.($i===$p?' aria-current="page"':'').'>'.$i.'</a>';
        $body.='</div>';
        emitpage($path,($category?:'奇闻逸事与都市趣闻').($p>1?' · 第'.$p.'页':''),$body,($category?$category.'：':'').$site['description']);
    }
}
foreach($articles as $articleIndex=>$a) {
    $url=articleurl($a);
    $body='<div class="breadcrumbs"><a href="/">首页</a> / <a href="'.caturl($a['category']).'">'.h($a['category']).'</a></div><article class="reading"><p class="eyebrow">'.h($a['category']).'</p><h1>'.h($a['title']).'</h1><p class="meta">发布于 '.h(substr($a['published_at'],0,10)).' · 更新于 '.h(substr($a['updated_at'],0,10)).'</p><p class="lead">'.h($a['description']).'</p>'.cover_html($a['meta'],$a['title']).'<p class="byline">'.h($a['meta']['author']??$site['name'].'编辑部').' · 约 '.max(1,(int)ceil(mb_strlen($a['content'])/400)).' 分钟阅读</p><div class="prose">'.render_story($a['content']).'</div>'.story_sources($a['meta']).'</article>'.readerNavigation($articles[$articleIndex-1]??null,$articles[$articleIndex+1]??null).'<section class="related"><h2>继续阅读</h2>';
    $related=array_values(array_filter($articles,fn($x)=>$x['id']!==$a['id']));
    usort($related,fn($x,$y)=>(int)($y['category']===$a['category'])<=>(int)($x['category']===$a['category']));
    foreach(array_slice($related,0,4) as $r) $body.='<p><a href="'.articleurl($r).'">'.h($r['title']).' →</a></p>';
    $body.='<a href="/">返回全部文章 →</a></section>';
    $schema=['@context'=>'https://schema.org','@type'=>'Article','headline'=>$a['title'],'description'=>$a['description'],'datePublished'=>date(DATE_ATOM,strtotime($a['published_at'])),'dateModified'=>date(DATE_ATOM,strtotime($a['updated_at'])),'mainEntityOfPage'=>$base.$url,'inLanguage'=>'zh-CN','author'=>['@type'=>'Organization','name'=>$a['meta']['author']??$site['name'].'编辑部'],'publisher'=>['@type'=>'Organization','name'=>$site['name']],'articleSection'=>$a['category']];
    $siteKeywords=$site['seo_keywords']??'';
    if(!empty($a['meta']['keywords'])) $site['seo_keywords']=implode(',',array_filter($a['meta']['keywords'],'is_string'));
    emitpage($url,$a['title'],$body,$a['description'],false,$schema);
    $site['seo_keywords']=$siteKeywords;
}
emitpage('/about.html','关于本站',((int)$site['id']===9?hushang_about($site):((int)$site['id']===10?shancheng_about($site):((int)$site['id']===8?jingcheng_about($site):'<article class="reading"><p class="eyebrow">ABOUT THE JOURNAL</p><h1>好奇有据，阅读有趣。</h1><p class="lead">'.h($site['description']).'</p><div class="prose"><h2>写什么</h2><p>关注城市奇观、街头往事与有依据的趣闻，解释热门画面背后的故事。</p><h2>怎样写</h2><p>以公开话题作为线索，依据资料原创整理，AI 辅助写作。每篇文章附有来源日期；历史事件不作为最新新闻，示意插画不冒充现场照片。</p><h2>怎样核对</h2><p>文章中的资料链接可供核对。现场安排和运营信息以相关机构最新公告为准。</p></div></article>'))));
emitpage('/search.html','站内搜索','<section class="hero"><h1>寻找一个好故事。</h1><form action="/search.html" class="search"><input name="q" id="search-q" aria-label="搜索文章" placeholder="城市、关键词…"><button>搜索</button></form><p id="search-status">输入关键词，搜索本站已发布内容。</p></section><div class="cards" id="search-results"></div><noscript>搜索需要 JavaScript；你也可以从<a href="/">首页分类</a>浏览全部文章。</noscript><script src="/search.js" defer></script>','搜索本站文章。',true);
emitpage('/404.html','页面不存在','<section class="hero"><p class="eyebrow">404</p><h1>这条街还没有故事。</h1><p>页面不存在或已移除。</p><a href="/">返回首页</a></section>','页面不存在。',true);
echo json_encode(['pages'=>$pages,'urls'=>$urls],JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR);
