<?php
$dir=ROOT.'/.local/comparison';
if(isset($_GET['original'])) {
 $key=(string)$_GET['original'];if(!preg_match('/^[a-z0-9-]{1,160}$/',$key)) fail('原稿不存在');
 $file=$dir.'/'.$key.'-model-original.json';if(!is_file($file)) fail('原稿不存在');
 $x=json_decode(file_get_contents($file),true);$a=$x['article'];
 page('模型原稿',adminNav().'<p class="notice">这是未经来源复核修订的模型原稿，可能含错误。正式文章已做修订。</p><article class="reading"><h1>'.h($a['title']).'</h1><p>'.h($x['metadata']['generation']['model_returned']).'</p><div class="prose">'.render_story($a['content']).'</div></article>');return;
}
$report=is_file($dir.'/report.json')?json_decode(file_get_contents($dir.'/report.json'),true):null;
$body=adminNav().'<section class="dashboard-title"><p class="eyebrow">MODEL COMPARISON</p><h1>街巷奇闻 · 双模型 6 篇试写</h1><p>统一文章字段、写作要求和审核流程；不同选题各 3 篇。用量来自接口返回，不含人工资料准备和本次助手会话。</p></section>';
if($report) {
 $body.='<div class="panel table-wrap"><table><thead><tr><th>模型实际返回</th><th>文章</th><th>输入 Token</th><th>输出 Token</th><th>合计（含失败和探测）</th><th>模型调用累计秒数</th></tr></thead><tbody>';
 foreach($report['providers'] as $name=>$r) $body.='<tr><td>'.h(implode(', ',$r['returned_models'])).'</td><td>'.(int)$r['articles'].'</td><td>'.number_format($r['input_tokens']).'</td><td>'.number_format($r['output_tokens']).'</td><td>'.number_format($r['total_with_probe']??$r['total_tokens']).'</td><td>'.h($r['model_call_seconds']).'</td></tr>';
 $body.='</tbody></table></div><p>两轮模型执行合计：'.h($report['model_run_wall_seconds']??$report['wall_seconds']).' 秒；含适配修正的生成阶段经过：'.h($report['elapsed_including_adapter_fix_seconds']??$report['wall_seconds']).' 秒。资料准备与来源复核另计；累计调用时间会因并发重叠，计费以服务商账单为准。</p>';
} else $body.='<p class="notice">正在试写，完成后会显示接口用量。</p>';
$body.='<div class="cards">';
foreach(query("SELECT a.*,m.metadata FROM mvp_articles a JOIN mvp_article_meta m ON a.id=m.article_id WHERE a.site_id=2 ORDER BY a.id DESC") as $a) {
 $meta=json_decode($a['metadata'],true);if(($meta['generation']['experiment']??'')!=='six-model-trial-20260930') continue;
 $body.='<article class="card"><p class="eyebrow">'.h($meta['generation']['provider'].' · '.$meta['generation']['model_returned']).'</p><h2>'.h($a['title']).'</h2><p>'.h($a['description']).'</p><p>'.mb_strlen($a['content']).' 字符 · '.($a['status']==='published'?'已发布':'草稿').'</p><a href="/admin/article?id='.$a['id'].'">查看 / 编辑</a> · <a href="/admin/model-trial?original='.h($a['slug']).'">模型原稿</a>'.($a['status']==='published'?' · <a target="_blank" href="http://site-2.localhost:8080/article/'.h($a['slug']).'.html">阅读文章 ↗</a>':'').'</article>';
}
$body.='</div><p><a href="/admin/static?site_id=2">生成与下载本站静态包 →</a></p>';
page('双模型试写对比',$body);
