<?php
declare(strict_types=1);
$isPost=$_SERVER['REQUEST_METHOD']==='POST';
if (!in_array($_SERVER['REQUEST_METHOD'],['GET','HEAD','POST'],true)) fail('请求方式不支持',405);
if ($isPost) verifyCsrf();
$error='';
if ($path==='/admin/login') {
    if ($isPost) {
        $u=query('SELECT * FROM mvp_users WHERE username=?',[(string)($_POST['username']??'')])->fetch();
        if ($u && (!$u['locked_until'] || strtotime($u['locked_until'])<=time()) && password_verify((string)($_POST['password']??''),$u['password'])) {
            query('UPDATE mvp_users SET login_failures=0,locked_until=NULL WHERE id=?',[$u['id']]);
            session_regenerate_id(true); $_SESSION['admin']=(int)$u['id']; $_SESSION['csrf']=bin2hex(random_bytes(24)); redirect('/admin');
        }
        if ($u) query('UPDATE mvp_users SET login_failures=login_failures+1,locked_until=IF(login_failures>=5,DATE_ADD(NOW(),INTERVAL 10 MINUTE),locked_until) WHERE id=?',[$u['id']]);
        $error='账号或密码不正确，或连续失败后暂时锁定。';
    }
    page('管理员登录','<section class="login panel"><p class="eyebrow">STATION CONSOLE</p><h1>管理你的站点</h1><p>一个工作台，独立管理每个站点的内容。</p>'.($error?'<p class="notice error">'.h($error).'</p>':'').'<form method="post">'.csrf().field('管理员账号','username','admin').field('密码','password','','password').'<button>登录工作台 →</button></form></section>',null); return;
}
if (!loggedIn()) redirect('/admin/login');
if ($path==='/admin/logout' && $isPost) { $_SESSION=[]; session_destroy(); redirect('/admin/login'); }
adminSelectedSite();
if(!$isPost && in_array($path,['/admin/progress','/admin/articles','/admin/catalog','/admin/static'],true) && !array_key_exists('site_id',$_GET)) {
    redirect($path.'?'.http_build_query(array_merge($_GET,['site_id'=>$_SESSION['admin_site_id']])));
}

if (in_array($path,['/admin/promotion','/admin/promotion/download','/admin/promotion/preview'],true)) { require __DIR__.'/promotion-admin.php'; return; }
if ($path==='/admin/static' || $path==='/admin/static/download') { require __DIR__.'/static-admin.php'; return; }
if ($path==='/admin/catalog' || $path==='/admin/catalog/download') { require __DIR__.'/catalog-admin.php'; return; }
if ($path==='/admin/progress') { require __DIR__.'/progress-admin.php'; return; }
if ($path==='/admin/models') { require __DIR__.'/models-admin.php'; return; }
if ($path==='/admin/articles') { require __DIR__.'/articles-admin.php'; return; }
if ($path==='/admin/model-trial') { require __DIR__.'/model-trial-admin.php'; return; }
if ($path==='/admin/theme') { require __DIR__.'/theme-admin.php'; return; }
if ($path==='/admin/editorial') { require __DIR__.'/editorial-admin.php'; return; }
if ($path==='/admin/password') {
    if ($isPost) {
        $u=query('SELECT * FROM mvp_users WHERE id=?',[$_SESSION['admin']])->fetch();
        $password=(string)($_POST['new_password']??'');
        if (!password_verify((string)($_POST['old_password']??''),$u['password'])) $error='原密码不正确。';
        elseif(strlen($password)<12 || strlen($password)>72) $error='新密码须为 12—72 字节。';
        else { query('UPDATE mvp_users SET password=? WHERE id=?',[password_hash($password,PASSWORD_DEFAULT),$u['id']]); session_regenerate_id(true); redirect('/admin?updated=1'); }
    }
    page('修改密码',adminNav().'<section class="panel narrow"><h1>修改管理员密码</h1><p class="notice">'.h($error ?: '初始密码只保存在本机私有文件中，请改为自己的密码。').'</p><form method="post">'.csrf().field('原密码','old_password','','password').field('新密码（至少 12 字节）','new_password','','password').'<button>保存密码</button></form></section>'); return;
}
if ($path==='/admin/urls') {
    $s=query('SELECT * FROM mvp_sites WHERE id=?',[(int)($_GET['site_id']??0)])->fetch();
    if (!$s) fail('站点不存在');
    if (!indexable($s)) fail('本站仍是本地预览或未开放收录，请先配置真实域名',422);
    header('Content-Type: text/plain; charset=utf-8'); header('Content-Disposition: attachment; filename="baidu-urls-'.$s['id'].'.txt"');
    echo rtrim($s['base_url'],'/')."/\n";
    foreach(query("SELECT slug FROM mvp_articles WHERE site_id=? AND status='published' ORDER BY id",[$s['id']]) as $a) echo rtrim($s['base_url'],'/').'/article/'.$a['slug'].".html\n";
    return;
}
if ($path==='/admin/site') {
    $id=(int)($_GET['id']??0);
    $s=$id?query('SELECT * FROM mvp_sites WHERE id=?',[$id])->fetch():['name'=>'','host'=>'','base_url'=>'','description'=>'','indexable'=>0];
    if (!$s) fail('站点不存在');
    if ($isPost) {
        $s=array_merge($s,array_intersect_key($_POST,array_flip(['name','host','base_url','description','seo_title','seo_description','seo_keywords','content_topic','topic_keywords'])));
        foreach(['name','host','base_url','description','seo_title','seo_description','seo_keywords','content_topic','topic_keywords'] as $k) $s[$k]=trim((string)$s[$k]);
        $s['image_prompt']=trim((string)($_POST['image_prompt']??''));
        if(mb_strlen($s['image_prompt'])>12000)$error='转图提示词最多12000字。';
        $s['image_count']=filter_var($_POST['image_count']??5,FILTER_VALIDATE_INT);
        if($s['image_count']===false || $s['image_count']<1 || $s['image_count']>20)$error='出图数量必须为1—20的整数。';
        $s['base_url']='https://'.strtolower(trim($s['host']));
        $s['host']=strtolower($s['host']); $s['base_url']=rtrim($s['base_url'],'/'); $s['indexable']=isset($_POST['indexable'])?1:0;
        $url=parse_url($s['base_url']);
        foreach(['seo_title'=>200,'seo_description'=>500,'seo_keywords'=>500,'content_topic'=>1000,'topic_keywords'=>1000] as $key=>$limit) if(mb_strlen($s[$key])>$limit) $error='TDK 或主题字段过长，请缩短后保存。';
        if (!$s['name'] || mb_strlen($s['name'])>120 || mb_strlen($s['description'])>500) $error='站名必填（最多 120 字），简介最多 500 字。';
        elseif (!filter_var($s['host'],FILTER_VALIDATE_DOMAIN,FILTER_FLAG_HOSTNAME) || strlen($s['host'])>253) $error='请输入合法主机名，不带协议、端口和路径。';
        elseif (!$url || !in_array($url['scheme']??'',['http','https'],true) || strtolower($url['host']??'')!==$s['host'] || !empty($url['path']) || isset($url['query']) || isset($url['fragment']) || isset($url['user']) || isset($url['pass']) || strlen($s['base_url'])>300) $error='网站地址必须与域名一致，例如 http://news.localhost:8080；不带路径。';
        elseif ($s['indexable'] && (localHost($s['host']) || ($url['scheme']??'')!=='https')) $error='开放收录须填写真实域名和 HTTPS 地址；本地域名始终禁止收录。';
        elseif(!$error) {
            try {
                $args=[$s['host'],$s['base_url'],$s['name'],$s['description'],$s['indexable']];
                if ($id) { $args[]=$id; query('UPDATE mvp_sites SET host=?,base_url=?,name=?,description=?,indexable=? WHERE id=?',$args); }
                else query('INSERT INTO mvp_sites(host,base_url,name,description,indexable,created_at) VALUES(?,?,?,?,?,NOW())',$args);
                $savedId=$id?:((int)db()->lastInsertId());
                query('UPDATE mvp_sites SET seo_title=?,seo_description=?,seo_keywords=?,content_topic=?,topic_keywords=?,image_count=?,image_prompt=? WHERE id=?',[$s['seo_title'],$s['seo_description'],$s['seo_keywords'],$s['content_topic'],$s['topic_keywords'],$s['image_count'],$s['image_prompt'],$savedId]);
                themeInit($savedId);
                redirect('/admin?updated=1');
            } catch(PDOException $e) { if($e->getCode()==='23000') $error='此域名已被其他站点使用。'; else throw $e; }
        }
    }
    $body=adminNav().'<section class="panel narrow"><p class="eyebrow">SITE SETTINGS</p><h1>'.($id?'编辑站点':'新建独立站点').'</h1><p class="notice">域名保存在本站设置，打包时自动读取。每个站点的内容主题和页面文件互相独立；保存不会自动上传服务器。</p>';
    if ($error) $body.='<p class="notice error">'.h($error).'</p>';
    $body.='<form method="post">'.csrf().field('站点名称','name',$s['name']).field('域名（不带端口）','host',$s['host']).textfield('站点简介','description',$s['description']).field('首页 Title','seo_title',$s['seo_title']??'','text',false).textfield('首页 Description','seo_description',$s['seo_description']??'').field('Keywords（逗号分隔）','seo_keywords',$s['seo_keywords']??'','text',false).textfield('内容主题 / 写作方向','content_topic',$s['content_topic']??'').field('选题关键词（逗号分隔）','topic_keywords',$s['topic_keywords']??'','text',false).field('转图数量（1—20张，默认5张）','image_count',$s['image_count']??5,'number').textfield('转图提示词（本站独立配置）','image_prompt',trim((string)($s['image_prompt']??''))?:readerDefaultPrompt(),16).'<p class="hint">可用变量：{{count}} 为大图数量，{{panels}} 为总格数（数量×3）。标题、正文和来源链接会自动追加；清空提示词使用默认三格漫画方案。</p><p class="hint">文章页“转图”会复制正文和简约漫画素描提示词，不调用模型。静态站点修改数量后需重新打包。</p><label class="check"><input type="checkbox" name="indexable" value="1"'.($s['indexable']?' checked':'').'> 正式导出时允许搜索引擎收录</label><p class="hint">本地预览始终禁止收录。文章页使用文章标题和摘要；首页使用本站 TDK。</p><button>保存站点</button></form></section>';
    page('站点设置',$body); return;
}
if ($path==='/admin/article/preview') {
    $a=query('SELECT * FROM mvp_articles WHERE id=?',[(int)($_GET['id']??0)])->fetch();
    if (!$a) fail('文章不存在',404);
    header('X-Robots-Tag: noindex, nofollow');
    $meta=editorial_meta((int)$a['id']);
    page($a['title'],adminNav().'<article class="panel narrow"><p class="notice">'.h($a['status']==='draft'?'草稿预览 · 尚未发布':'文章预览').'</p><h1>'.h($a['title']).'</h1><p>'.h($a['description']).'</p><div class="story">'.render_story($a['content']).'</div>'.story_sources($meta).'<p><a href="/admin/article?id='.$a['id'].'">编辑文章</a></p></article>'); return;
}
if ($path==='/admin/article') {
    $id=(int)($_GET['id']??0);
    $a=$id?query('SELECT * FROM mvp_articles WHERE id=?',[$id])->fetch():['site_id'=>(int)adminSelectedSite()['id'],'title'=>'','slug'=>'','description'=>'','category'=>'未分类','content'=>'','status'=>'draft'];
    if (!$a) fail('文章不存在');
    if ($isPost) {
        if (($_POST['action']??'')==='delete' && $id) { query('DELETE FROM mvp_articles WHERE id=?',[$id]); redirect('/admin'); }
        $a=array_merge($a,array_intersect_key($_POST,array_flip(['site_id','title','slug','description','category','content','status'])));
        foreach(['title','slug','description','category','content','status'] as $k) $a[$k]=trim((string)$a[$k]);
        $a['site_id']=(int)$a['site_id'];
        if (!query('SELECT id FROM mvp_sites WHERE id=?',[$a['site_id']])->fetch()) $error='请选择有效站点。';
        elseif (!$a['title'] || mb_strlen($a['title'])>180 || !$a['content'] || strlen($a['content'])>1000000) $error='标题和正文必填，标题最多 180 字，正文最多 1MB。';
        elseif (!preg_match('/^[a-z0-9][a-z0-9-]{0,159}$/',$a['slug'])) $error='网址标识使用小写英文字母、数字和短横线，长度 1—160。';
        elseif (mb_strlen($a['description'])>500 || !$a['category'] || mb_strlen($a['category'])>80) $error='摘要最多 500 字；分类必填且最多 80 字。';
        elseif (!in_array($a['status'],['draft','published'],true)) $error='状态无效。';
        else {
            // Stable published URLs: edits cannot move or rename a published article.
            $old=$id?query('SELECT * FROM mvp_articles WHERE id=?',[$id])->fetch():null;
            if ($old && $old['published_at'] && ($old['slug']!==$a['slug'] || (int)$old['site_id']!==$a['site_id'])) $error='已发布文章的站点和网址保持稳定；新地址请新建文章并单独规划跳转。';
            else {
                if ($a['description']==='') $a['description']=mb_substr(preg_replace('/\s+/u',' ',$a['content']),0,140);
                $published=$old['published_at']??($a['status']==='published'?date('Y-m-d H:i:s'):null);
                $args=[$a['site_id'],$a['slug'],$a['title'],$a['description'],$a['category'],$a['content'],$a['status'],$published];
                try {
                    if ($id) { $args[]=$id; query('UPDATE mvp_articles SET site_id=?,slug=?,title=?,description=?,category=?,content=?,status=?,published_at=?,updated_at=NOW() WHERE id=?',$args); }
                    else query('INSERT INTO mvp_articles(site_id,slug,title,description,category,content,status,published_at,updated_at) VALUES(?,?,?,?,?,?,?,?,NOW())',$args);
                    redirect('/admin?updated=1');
                } catch(PDOException $e) { if($e->getCode()==='23000') $error='该站点已存在相同网址标识。'; else throw $e; }
            }
        }
    }
    $body=adminNav().'<section class="panel"><p class="eyebrow">CONTENT EDITOR</p><h1>'.($id?'编辑文章':'写一篇有价值的内容').'</h1>';
    if($error) $body.='<p class="notice error">'.h($error).'</p>';
    $body.='<p class="notice">仅人工操作：本页用于人工创建、修改、发布和删除文章，不调用 AI。AI 生成的新文章默认是草稿，请阅读后再发布。</p><form method="post">'.csrf().'<div class="form-grid"><label>所属站点<select name="site_id">';
    foreach(query('SELECT * FROM mvp_sites ORDER BY id') as $s) $body.='<option value="'.(int)$s['id'].'"'.((int)$a['site_id']===(int)$s['id']?' selected':'').'>'.h($s['name'].' · '.$s['host']).'</option>';
    $body.='</select></label>'.field('分类','category',$a['category']).'</div>'.field('文章标题','title',$a['title']).field('稳定网址标识，例如 first-guide','slug',$a['slug']).textfield('摘要（留空时从正文提取）','description',$a['description'],3).textfield('正文（纯文本，空行分段，不执行 HTML）','content',$a['content'],16).'<label>发布状态<select name="status"><option value="draft"'.($a['status']==='draft'?' selected':'').'>草稿</option><option value="published"'.($a['status']==='published'?' selected':'').'>已发布</option></select></label><button>保存文章</button></form>';
    if ($id) $body.='<details class="danger"><summary>删除文章</summary><p>删除后链接将返回 404，内容不可撤回，请先备份。</p><form method="post">'.csrf().'<input type="hidden" name="action" value="delete"><button class="delete">确认删除文章</button></form></details>';
    $body.='</section>'; page('文章编辑 · 仅人工操作',$body); return;
}
if ($path!=='/admin' && $path!=='/admin/') fail('管理页面不存在');
$sites=query('SELECT s.*, (SELECT COUNT(*) FROM mvp_articles a WHERE a.site_id=s.id) AS article_count FROM mvp_sites s ORDER BY s.id')->fetchAll();
$filter=(int)($_GET['site_id']??0);
$p=max(1,min(100000,(int)($_GET['page']??1))); $offset=($p-1)*30;
$where=$filter?' WHERE a.site_id=?':''; $args=$filter?[$filter]:[];
$total=(int)query('SELECT COUNT(*) FROM mvp_articles a'.$where,$args)->fetchColumn();
$articles=query('SELECT a.*,s.name AS site_name,s.base_url FROM mvp_articles a JOIN mvp_sites s ON s.id=a.site_id'.$where.' ORDER BY a.updated_at DESC,a.id DESC LIMIT 30 OFFSET '.$offset,$args)->fetchAll();
$published=(int)query("SELECT COUNT(*) FROM mvp_articles WHERE status='published'")->fetchColumn();
$body=adminNav().'<section class="dashboard-title"><p class="eyebrow">YOUR PUBLISHING NETWORK</p><h1>我的内容工作台</h1><p>人工后台：管理文章、确认选题、配置模型、打包上传。AI 执行：按确认目录通过脚本生成草稿，默认不会发布。</p></section>';
$body.='<section class="panel"><h2>从选题到上线</h2><p>① AI 按提示词整理目录 → ② 人工导入、批量修改与确认 → ③ AI 用已配置模型生成草稿 → ④ 人工阅读、修改、发布 → ⑤ 人工打包上传。</p><p><a href="/admin/promotion">生成宣传页面 / 下载 HTML</a> · <a href="/admin/articles">管理文章</a> · <a href="/admin/catalog">管理 AI 目录 / 复制提示词</a> · <a href="/admin/models">配置模型与 Key</a></p><details><summary>历史执行记录</summary><p><a href="/admin/model-trial">双模型试写</a> · <a href="/admin/editorial">旧自动内容记录</a></p></details></section>';
if(isset($_GET['updated'])) $body.='<p class="notice">保存成功。</p>';
$body.='<div class="stats"><div><span>独立站点</span><strong>'.count($sites).'</strong></div><div><span>已发布文章</span><strong>'.$published.'</strong></div><div><span>当前运行方式</span><strong class="small">本机 PHP + MySQL</strong></div></div><div class="section-heading"><h2>我的站点</h2><a href="/admin/site">添加站点 ＋</a></div><div class="cards">';
foreach($sites as $s) {
    $body.='<section class="card"><p class="eyebrow">'.h($s['host']).'</p><h2>'.h($s['name']).'</h2><p>'.h($s['description']).'</p><span class="badge">'.(indexable($s)?'已开启抓取':'预览模式 · 不收录').'</span><p>'.$s['article_count'].' 篇内容</p><div class="card-actions"><a href="'.h('http://site-'.$s['id'].'.localhost:8080/').'" target="_blank" rel="noopener">预览 ↗</a><a href="/admin/site?id='.$s['id'].'">设置 / TDK</a><a href="/admin/theme?site_id='.$s['id'].'">HTML / CSS / JS</a><a href="/admin/static?site_id='.$s['id'].'">打包</a><a href="/admin/articles?site_id='.$s['id'].'">文章管理</a><a href="/admin/article?site_id='.$s['id'].'">写文章</a></div>'.(indexable($s)?'<p><a href="/admin/urls?site_id='.$s['id'].'">导出百度提交链接</a></p>':'').'</section>';
}
$body.='</div><div class="section-heading"><h2>最近内容</h2><a href="/admin">查看全部</a></div><div class="panel table-wrap"><table><thead><tr><th>文章</th><th>所属站点</th><th>状态</th><th>更新日期</th><th>操作</th></tr></thead><tbody>';
foreach($articles as $a) $body.='<tr><td>'.h($a['title']).'</td><td>'.h($a['site_name']).'</td><td><span class="badge">'.($a['status']==='published'?'已发布':'草稿').'</span></td><td>'.h(substr($a['updated_at'],0,10)).'</td><td><a href="/admin/article?id='.$a['id'].'">编辑</a> · <a href="/admin/article/preview?id='.$a['id'].'">预览</a>'.($a['status']==='published'?' · <a target="_blank" rel="noopener" href="'.h('http://site-'.$a['site_id'].'.localhost:8080/article/'.$a['slug'].'.html').'">查看</a>':'').'</td></tr>';
if(!$articles) $body.='<tr><td colspan="5">暂无文章，先写第一篇内容。</td></tr>';
$body.='</tbody></table></div><div class="pagination">';
if($p>1) $body.='<a href="/admin?site_id='.$filter.'&page='.($p-1).'">上一页</a>';
if($p*30<$total) $body.='<a href="/admin?site_id='.$filter.'&page='.($p+1).'">下一页</a>';
$body.='</div><aside class="notice"><strong>关于百度收录</strong><p>本地站点不能被百度访问。上线真实域名后，检查 HTTPS、robots、sitemap 与正文可读性，再到百度搜索资源平台验证站点、提交链接。提交成功不等于收录。</p><a href="https://ziyuan.baidu.com/linksubmit/index" target="_blank" rel="noopener">打开百度搜索资源平台 ↗</a></aside>';
page('管理工作台',$body);
