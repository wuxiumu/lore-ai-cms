<?php
$configFile=ROOT.'/.local/editorial.json';
$config=is_file($configFile)?json_decode(file_get_contents($configFile),true):[];
$sid=(int)($_GET['site_id']??($config['site_id']??2));
$selected=query('SELECT * FROM mvp_sites WHERE id=?',[$sid])->fetch();if(!$selected) fail('站点不存在');
$config['site_id']=$sid;$config['site_name']=$selected['name'];
$reportFile=ROOT.'/.local/editorial/site-'.$sid.'/latest.json';
$report=is_file($reportFile)?json_decode(file_get_contents($reportFile),true):[];
$model=!empty($config['llm']['base_url'])&&!empty($config['llm']['model']);
$body=adminNav().'<p class="notice">当前采用站长先选题的目录流程：<a href="/admin/catalog?site_id='.$sid.'">打开我的选题目录</a>。下方保留旧自动内容记录；未启用持续生成。</p>'.'<section class="dashboard-title"><p class="eyebrow">EDITORIAL AUTOMATION</p><h1>从好奇的主题，到有出处的文章。</h1><p>选题筛选 → 资料提取 → 原创写作 → 独立审稿 → 发布或保留草稿</p></section><div class="stats"><div><span>目标站点</span><strong class="small">'.h($config['site_name']??'未配置').'</strong></div><div><span>每日文章上限</span><strong>'.(int)($config['daily_limit']??3).'</strong></div><div><span>持续自动写作</span><strong class="small">'.($model?'接口已填写，任务环境需提供密钥':'等待配置模型接口').'</strong></div></div><p class="notice">首批 3 篇为资料核实后的原创示例，已在本地发布。服务器定时任务尚未启用。当前实时热榜源为百度，其他平台通过有权使用的 RSS 接入；未接入的榜单不会假称已采集。</p><section class="panel"><h2>最近采集</h2><p>完成时间：'.h($report['completed_at']??'尚未运行').'；榜单条目：'.(int)($report['trends_count']??0).'；符合筛选的选题：'.count($report['candidates']??[]).'</p>';
foreach($report['errors']??[] as $e) $body.='<p class="notice error">来源不可用：'.h($e['source']).'（'.h($e['error']).'），本次已跳过。</p>';
foreach(array_slice($report['candidates']??[],0,8) as $t) $body.='<p>'.h($t['topic']).' <span class="badge">主题得分 '.round($t['score']).'</span></p>';
$body.='</section><div class="chips">';foreach(query('SELECT id,name FROM mvp_sites ORDER BY id') as $item) $body.='<a href="/admin/editorial?site_id='.$item['id'].'">'.h($item['name']).'</a>';
$body.='</div><p>内容方向：'.h($selected['content_topic']).' · <a href="/admin/site?id='.$sid.'">修改主题和关键词</a></p><div class="section-heading"><h2>自动内容记录</h2></div><div class="panel table-wrap"><table><thead><tr><th>文章</th><th>当前状态</th><th>创建时间</th><th>操作</th></tr></thead><tbody>';
foreach(query('SELECT j.*,a.status AS current_status FROM mvp_editorial_jobs j JOIN mvp_articles a ON a.id=j.article_id WHERE j.site_id=? ORDER BY j.id DESC LIMIT 50',[(int)($config['site_id']??0)]) as $j) $body.='<tr><td>'.h($j['title']).'</td><td>'.($j['current_status']==='published'?'已发布':'待审草稿').'</td><td>'.h($j['created_at']).'</td><td><a href="/admin/article?id='.(int)$j['article_id'].'">编辑</a></td></tr>';
$body.='</tbody></table></div><section class="notice"><h2>质量规则</h2><p>只选主题相关内容；没有可用来源则跳过；不把历史事件写成刚发生；不复制平台正文和图片；重复选题不再发布。模型审稿不通过的文章只保存草稿，机器检查不能替代所有人工判断。</p><p>模型配置在服务器私有配置中完成，不在页面展示 API 密钥。</p></section>';
page('自动内容工作台',$body);
