<?php
declare(strict_types=1);
function editorial_meta(int $id): array {
    $value=query('SELECT metadata FROM mvp_article_meta WHERE article_id=?',[$id])->fetchColumn();
    return $value ? json_decode($value,true) : [];
}
function cover_html(array $meta,string $title,bool $lazy=false):string {
    $name=$meta['cover']??'';
    if(!preg_match('/^[a-z-]+$/',$name) || !is_file(__DIR__.'/../public/covers/'.$name.'.svg')) return '';
    return '<figure class="story-cover"><img src="/covers/'.h($name).'.svg" width="1200" height="640" alt="'.h($title).'：原创示意插画"'.($lazy?' loading="lazy"':' fetchpriority="high"').'><figcaption>原创示意插画 · 非现场照片</figcaption></figure>';
}
function render_story(string $content):string {
    $html='';
    foreach(preg_split('/\R\s*\R/',trim($content)) as $p) {
        if(preg_match('/^## (.+)$/u',trim($p),$m)) $html.='<h2>'.h($m[1]).'</h2>';
        else $html.='<p>'.nl2br(h($p)).'</p>';
    }
    return $html;
}
function story_sources(array $meta):string {
    if(empty($meta['sources'])) return '';
    $kind=$meta['story_type']??'nonfiction';
    $notice=$kind==='fiction'?'本文为原创虚构鬼故事，人物和情节虚构。下列链接仅供场景背景参考，不是故事发生过的证据。':($kind==='folklore'?'本文整理城市民间传说，并使用 AI 辅助写作。资料记录的是传说，不证明超自然事件发生。':'本文依据公开资料原创整理，AI 辅助写作。历史报道的时间见下方；文中分析不代表受访者原话。');
    $html='<aside class="sources"><h2>'.($kind==='fiction'?'写作背景与资料':'资料与出处').'</h2><p>'.h($notice).'</p><ul>';
    foreach($meta['sources'] as $s) {
        $url=(string)($s['url']??'');
        if(!filter_var($url,FILTER_VALIDATE_URL)||!in_array(parse_url($url,PHP_URL_SCHEME),['https','http'],true)) continue;
        $html.='<li><a href="'.h($url).'" target="_blank" rel="noopener noreferrer">'.h($s['publisher'].'｜'.$s['title']).'</a><span> '.h(($s['date']??'').(!empty($s['role'])?' · '.$s['role']:'')).'</span></li>';
    }
    $html.='</ul>';
    if(!empty($meta['context_note'])) $html.='<p>'.h($meta['context_note']).'</p>';
    return $html.'</aside>';
}

function jingcheng_about(array $site):string {
    return '<article class="reading"><p class="eyebrow">BEIJING · AFTER DARK</p><h1>夜深了，聊一段北京故事。</h1><p class="lead">'.h($site['description']).'</p><div class="prose"><h2>我们写什么</h2><p>胡同、四合院、末班车、夜班和旧物，是京城夜谈的故事背景。用人物、细节和悬念，讲一段愿意分享给朋友的鬼故事。</p><h2>故事与出处</h2><p>原创故事会明确标注虚构，可以没有外部出处；人物和情节不作为真实亲历。民间传说会标明传说，有可核验资料时附上出处。资料只支持背景，不证明鬼故事发生过。</p><h2>复制与分享</h2><p>文章末尾可复制全文或链接，并使用系统分享。复制时保留虚构标注。浏览器不支持系统分享时，会复制标题和链接。</p></div></article>';
}

function hushang_about(array $site):string {
return '<article class="reading"><p class="eyebrow">SHANGHAI · AFTER DARK</p><h1>熟悉的上海，陌生的夜。</h1><p class="lead">'.h($site['description']).'</p><div class="prose"><h2>我们写什么</h2><p>地铁、弄堂、老楼、滨江与高校周边，是原创恐怖故事的背景。用日常生活的声音、气味、对话与悬念，营造令人不安的阅读体验。</p><h2>真实感与虚构</h2><p>城市地名真实，人物、房间、设施细节和超自然情节虚构，不表示相关地点发生过灵异事件，不冒充真实案件或亲历。原创故事可以没有外部出处；有资料的传说另行注明性质和来源。</p><h2>复制与分享</h2><p>文章末尾支持复制全文与分享链接，请保留原创虚构标注。</p></div></article>';
}

function shancheng_about(array $site):string {
return '<article class="reading"><p class="eyebrow">CHONGQING · AFTER DARK</p><h1>熟悉的重庆，陌生的夜。</h1><p class="lead">'.h($site['description']).'</p><div class="prose"><h2>我们写什么</h2><p>轨道、老街、坡楼、江岸与高校周边，是原创恐怖故事的背景。用日常生活的声音、气味、对话与悬念，营造令人不安的阅读体验。</p><h2>真实感与虚构</h2><p>城市地名真实，人物、房间、设施细节和超自然情节虚构，不表示相关地点发生过灵异事件，不冒充真实案件或亲历。原创故事可以没有外部出处；有资料的传说另行注明性质和来源。</p><h2>复制与分享</h2><p>文章末尾支持复制全文与分享链接，请保留原创虚构标注。</p></div></article>';
}
