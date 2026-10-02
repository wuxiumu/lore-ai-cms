<?php
declare(strict_types=1);
const ROOT = __DIR__ . '/../../..';
date_default_timezone_set('Asia/Shanghai');
require_once __DIR__.'/themes.php';
require_once __DIR__.'/reader.php';
function db(): PDO {
    static $db;
    if (!$db) {
        $c = json_decode(file_get_contents(ROOT . '/.local/native.json'), true, 512, JSON_THROW_ON_ERROR);
        $db = new PDO('mysql:host='.$c['host'].';dbname='.$c['database'].';charset=utf8mb4', $c['user'], $c['password'], [PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC, PDO::ATTR_EMULATE_PREPARES=>false]);
        $db->exec("SET time_zone = '+08:00'");
    }
    return $db;
}
function query(string $sql, array $args=[]): PDOStatement { $s=db()->prepare($sql); $s->execute($args); return $s; }
function h(mixed $v): string { return htmlspecialchars((string)$v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function redirect(string $url): never { header('Location: '.$url, true, 303); exit; }
function localHost(string $host): bool {
    return $host === 'localhost' || str_ends_with($host,'.localhost') || str_ends_with($host,'.test') || str_ends_with($host,'.local') || !str_contains($host,'.') || (filter_var($host,FILTER_VALIDATE_IP) && !filter_var($host,FILTER_VALIDATE_IP,FILTER_FLAG_NO_PRIV_RANGE|FILTER_FLAG_NO_RES_RANGE));
}
function indexable(array $site): bool { return (bool)$site['indexable'] && !localHost($site['host']); }
function csrf(): string { $_SESSION['csrf'] ??= bin2hex(random_bytes(24)); return '<input type="hidden" name="csrf" value="'.h($_SESSION['csrf']).'">'; }
function verifyCsrf(): void { if (!hash_equals($_SESSION['csrf'] ?? '', (string)($_POST['csrf'] ?? '')) || empty($_SESSION['csrf'])) { http_response_code(403); exit('表单已过期，请刷新后重试。'); } }
function loggedIn(): bool { return isset($_SESSION['admin']); }
function page(string $title, string $body, ?array $site=null, string $description='', string $canonical='', bool $noindex=false, array $structured=[]): void {
    if ($noindex || !$site || !indexable($site)) header('X-Robots-Tag: noindex, nofollow');
    header('Content-Type: text/html; charset=utf-8');
    $brand=$site['name'] ?? '站群工作台';
    $home=$site && rtrim($canonical,'/')===rtrim($site['base_url'],'/');
    $fullTitle=$home && !empty($site['seo_title'])?$site['seo_title']:$title.' · '.$brand;
    if($home && !empty($site['seo_description'])) $description=$site['seo_description'];
    ob_start();
    echo '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'.h($fullTitle).'</title><meta name="description" content="'.h($description ?: ($site['description'] ?? '管理独立站点，发布有价值的内容。')).'">';
    if($site && !empty($site['seo_keywords'])) echo '<meta name="keywords" content="'.h($site['seo_keywords']).'">';
    if ($noindex || !$site || !indexable($site)) echo '<meta name="robots" content="noindex,nofollow">';
    if ($canonical) {
        echo '<link rel="canonical" href="'.h($canonical).'">';
        echo '<meta property="og:url" content="'.h($canonical).'"><meta property="og:title" content="'.h($fullTitle).'"><meta property="og:description" content="'.h($description ?: ($site['description']??'')).'"><meta property="og:locale" content="zh_CN"><meta property="og:type" content="'.($structured?'article':'website').'">';
    }
    if ($structured) echo '<script type="application/ld+json" nonce="'.h(defined('CSP_NONCE')?CSP_NONCE:'').'">'.json_encode($structured,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_HEX_TAG|JSON_HEX_AMP|JSON_HEX_APOS|JSON_HEX_QUOT).'</script>';
    echo '<link rel="stylesheet" href="/style.css"></head><body class="'.($brand==='街巷奇闻'?'urban':'standard').'"><header><a class="brand" href="/">'.h($brand).'<span class="dot"></span></a><nav><a href="/">网站首页</a><a href="/about">关于本站</a><a href="/sitemap.xml">站点地图</a>'.(defined('STATIC_EXPORT')?'':'<a href="/admin">管理工作台 ↗</a>').'</nav></header><main>'.$body.'</main><footer><span>'.h($brand).' © '.date('Y').'</span><span>好奇有据 · 阅读有趣</span></footer></body></html>';

    $default=ob_get_clean();
    if(!$site || empty($site['id'])) { echo $default; return; }
    $files=$site['_theme']??themeRead((int)$site['id']);
    preg_match('~<head>(.*?)</head>~s',$default,$matches);
    $asset=defined('STATIC_EXPORT')?'/theme/':'/theme/site-'.(int)$site['id'].'/';
    $head=str_replace('/style.css',$asset.'style.css',$matches[1]).'<link rel="stylesheet" href="/reader.css">';
    $pagePath=parse_url($canonical,PHP_URL_PATH)?:'/';
    $homeTemplate=$home || $pagePath==='/' || str_starts_with($pagePath,'/page/');
    $kind=$structured?'article':($homeTemplate?'home':(str_contains($canonical,'/category/')?'category':'simple'));
    $vars=['{{site_name}}'=>h($brand),'{{title}}'=>h($title),'{{description}}'=>h($description?:$site['description']),'{{topic}}'=>h($site['content_topic']??''),'{{year}}'=>date('Y'),'{{canonical}}'=>h($canonical),'{{about_url}}'=>defined('STATIC_EXPORT')?'/about.html':'/about','{{css_url}}'=>$asset.'style.css','{{js_url}}'=>$asset.'script.js','{{nonce}}'=>h(defined('CSP_NONCE')?CSP_NONCE:'')];
    $template=$files[$kind.'.html'];
    if($kind==='article')$template=preg_replace('~<section class="story-tools".*?</section>~s','',$template);
    $content=strtr($template,$vars+['{{content}}'=>$body]);
    if($kind==='article')$content.=readerTools($site);
    $html=strtr($files['layout.html'],$vars+['{{head}}'=>$head,'{{content}}'=>$content]);
    $footer=readerFooter($site);
    if(str_contains($html,'<footer'))$html=preg_replace('~<footer\b~',$footer.'<footer',$html,1);
    else $html=str_replace('</body>',$footer.'</body>',$html);
    $html=str_replace('</body>','<script src="/reader.js" defer nonce="'.h(defined('CSP_NONCE')?CSP_NONCE:'').'"></script></body>',$html);
    echo $html;
}
function field(string $label, string $name, mixed $value='', string $type='text', bool $required=true): string { return '<label>'.h($label).'<input type="'.h($type).'" name="'.h($name).'" value="'.h($value).'"'.($required?' required':'').'></label>'; }
function textfield(string $label,string $name,mixed $value='',int $rows=4):string { return '<label>'.h($label).'<textarea name="'.h($name).'" rows="'.$rows.'">'.h($value).'</textarea></label>'; }
function adminSelectedSite(): array {
    $path=$GLOBALS['path']??parse_url($_SERVER['REQUEST_URI']??'/admin',PHP_URL_PATH);
    if(in_array($path,['/admin/article','/admin/article/preview'],true) && !empty($_GET['id'])) {
        $id=query('SELECT site_id FROM mvp_articles WHERE id=?',[(int)$_GET['id']])->fetchColumn();
        if(!$id) fail('文章不存在');
    } elseif($path==='/admin/site' && !empty($_GET['id'])) {
        $id=(int)$_GET['id'];
        if(!query('SELECT id FROM mvp_sites WHERE id=?',[$id])->fetchColumn()) fail('站点不存在');
    } elseif(array_key_exists('site_id',$_GET)) {
        $id=filter_var($_GET['site_id'],FILTER_VALIDATE_INT);
        if(!$id || $id<1) fail('站点参数无效',400);
    } else $id=$_SESSION['admin_site_id']??0;
    $site=$id?query('SELECT * FROM mvp_sites WHERE id=?',[(int)$id])->fetch():false;
    if(!$site && array_key_exists('site_id',$_GET)) fail('站点不存在');
    if(!$site) $site=query('SELECT * FROM mvp_sites ORDER BY id LIMIT 1')->fetch();
    if(!$site) fail('请先新建站点');
    $_SESSION['admin_site_id']=(int)$site['id'];
    return $site;
}
function adminNav(): string {
    $site=adminSelectedSite();$sid=(int)$site['id'];$path=$GLOBALS['path']??'/admin';
    $sections=['/admin/progress'=>'内容进度','/admin/articles'=>'文章（人工）','/admin/catalog'=>'AI 选题目录（人工确认）','/admin/static'=>'人工打包'];
    $active=in_array($path,['/admin/article','/admin/article/preview'],true)?'/admin/articles':(str_starts_with($path,'/admin/catalog')?'/admin/catalog':(str_starts_with($path,'/admin/static')?'/admin/static':$path));
    $switchPath=isset($sections[$active])?$active:'/admin/articles';
    $html='<div class="toolbar"><div><a href="/admin">工作台</a><a href="/admin/promotion"'.(str_starts_with($path,'/admin/promotion')?' class="active" aria-current="page"':'').'>宣传页面</a><a href="/admin/reader-settings">全局转图设置</a><a href="/admin/site">新建站点</a><a href="/admin/models">大模型配置（人工）</a><a href="/admin/password">修改密码</a></div><form method="post" action="/admin/logout">'.csrf().'<button class="secondary">退出登录</button></form></div>';
    if(str_starts_with($path,'/admin/promotion') || $path==='/admin/reader-settings')return $html;
    $html.='<section class="admin-site-context" aria-label="当前子站"><p class="eyebrow">当前子站</p><h2>'.h($site['name']).'</h2><p>'.h($site['host']).'</p><div class="chips" aria-label="切换子站">';
    foreach(query('SELECT id,name FROM mvp_sites ORDER BY id') as $item) $html.='<a'.((int)$item['id']===$sid?' class="active" aria-current="page"':'').' href="'.$switchPath.'?site_id='.(int)$item['id'].'">'.h($item['name']).'</a>';
    $html.='</div><nav class="admin-tabs" aria-label="子站管理">';
    foreach($sections as $url=>$label) $html.='<a'.($active===$url?' class="active" aria-current="page"':'').' href="'.$url.'?site_id='.$sid.'">'.$label.'</a>';
    return $html.'</nav><p class="hint">切换子站后，这四个入口跟随当前站点；当前页面地址固定站点，多标签页操作互不串站。</p></section>';
}
function fail(string $message,int $code=404,?array $site=null):never { http_response_code($code); page((string)$code,'<section class="hero"><p class="eyebrow">'.(int)$code.'</p><h1>'.h($message).'</h1><a href="/">返回首页</a></section>',$site,'','',true); exit; }
