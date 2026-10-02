<?php
$file=ROOT.'/.local/model-providers.json';$models=is_file($file)?json_decode(file_get_contents($file),true):[];$error='';
if($isPost){
 $next=$models;
 foreach(['qwen','glm'] as $key){
  $row=$_POST['models'][$key]??[];$url=trim((string)($row['base_url']??''));$model=trim((string)($row['model']??''));$protocol=$row['protocol']??'';
  $parsed=parse_url($url);
  if(!$parsed || ($parsed['scheme']??'')!=='https' || empty($parsed['host']) || isset($parsed['user']) || isset($parsed['pass']) || isset($parsed['query']) || isset($parsed['fragment']) || !$model || strlen($model)>160 || !in_array($protocol,['anthropic','openai'],true)){$error='请输入 HTTPS 接口地址、有效模型名称和协议。所有配置均未保存。';break;}
  $next[$key]=['provider'=>$key==='qwen'?'千问':'智谱','model'=>$model,'protocol'=>$protocol,'base_url'=>rtrim($url,'/'),'api_key'=>$models[$key]['api_key']??''];
  $secret=trim((string)($row['api_key']??''));if($secret!=='')$next[$key]['api_key']=$secret;
 }
 if(!$error){$temp=tempnam(dirname($file),'.models-');chmod($temp,0600);file_put_contents($temp,json_encode($next,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));rename($temp,$file);redirect('/admin/models?saved=1');}
}
$body=adminNav().'<section class="panel"><h1>大模型配置 · 仅人工操作</h1><p class="notice">这里由站长修改配置。保存只更新本机设置，不测试接口、不调用模型、不生成文章。生成脚本会读取同一份配置。</p>'.($error?'<p class="notice error">'.h($error).'</p>':'').(isset($_GET['saved'])?'<p class="notice">全部配置已保存。</p>':'').'<form method="post">'.csrf();
foreach(['qwen'=>'千问','glm'=>'智谱'] as $key=>$label){$m=$models[$key]??[];$body.='<fieldset><legend>'.h($label).'（'.$key.'）</legend>'.field('模型名称','models['.$key.'][model]',$m['model']??'').field('API 基础地址','models['.$key.'][base_url]',$m['base_url']??'').'<label>接口协议<select name="models['.$key.'][protocol]"><option value="anthropic"'.(($m['protocol']??'')==='anthropic'?' selected':'').'>Anthropic Messages</option><option value="openai"'.(($m['protocol']??'')==='openai'?' selected':'').'>OpenAI Chat Completions</option></select></label>'.field('替换 Key（留空保留；已有 Key '.(!empty($m['api_key'])?'已配置':'未配置').'）','models['.$key.'][api_key]','','password',false).'</fieldset>';}
$body.='<button>人工批量保存模型配置</button></form><p>Key 不回显，保存在本机私有配置中，不进入静态网站包。此页不会校验服务商是否支持所填模型。</p></section>';page('大模型配置',$body);
