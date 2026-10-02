<?php
declare(strict_types=1);
$prompt=readerGlobalPrompt();$error='';
if($isPost){
    $prompt=trim((string)($_POST['image_prompt']??''));
    if(mb_strlen($prompt)>12000)$error='全局提示词最多12000字。';
    else {
        $file=ROOT.'/.local/reader-settings.json';$tmp=tempnam(dirname($file),'reader-');
        file_put_contents($tmp,json_encode(['image_prompt'=>$prompt,'updated_at'=>date(DATE_ATOM)],JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));chmod($tmp,0600);rename($tmp,$file);
        redirect('/admin/reader-settings?saved=1');
    }
}
$body=adminNav().'<section class="panel"><h1>全局转图提示词</h1><p>人工配置：所有站点默认继承这里的规则。站点设置中的提示词可留空，或补充城市特色、人物风格等要求。</p>'.($error?'<p class="notice error">'.h($error).'</p>':'').(isset($_GET['saved'])?'<p class="notice">全局提示词已保存；线上静态站点需重新打包。</p>':'').'<form method="post">'.csrf().textfield('全局提示词（留空恢复内置默认）','image_prompt',$prompt,20).'<p class="hint">变量：{{count}} 大图数量，{{panels}} 总格数。程序自动追加顺序清单、三格编号、文章标题正文和来源链接，无需重复填写。</p><button>保存全局提示词</button></form></section>';
page('全局转图设置',$body);
