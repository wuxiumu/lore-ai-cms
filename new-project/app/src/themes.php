<?php
function themeFiles(): array { return ['layout.html','home.html','article.html','category.html','simple.html','style.css','script.js']; }
function themeDir(int $id):string { return ROOT.'/new-project/themes/site-'.$id; }
function themeInit(int $id):void {
    $dir=themeDir($id); if(!is_dir($dir)) mkdir($dir,0755,true);
    $defaults=['layout.html'=>'<!doctype html><html lang="zh-CN"><head>{{head}}</head><body class="urban"><header><a class="brand" href="/">{{site_name}}<span class="dot"></span></a><nav><a href="/">网站首页</a><a href="{{about_url}}">关于本站</a><a href="/sitemap.xml">站点地图</a></nav></header><main>{{content}}</main><footer><span>{{site_name}} © {{year}}</span><span>好奇有据 · 阅读有趣</span></footer><script src="{{js_url}}" defer nonce="{{nonce}}"></script></body></html>', 'style.css'=>file_get_contents(ROOT.'/new-project/app/public/style.css'),'script.js'=>"// 当前站点独立 JavaScript。保存后刷新本地页面；上线需重新打包。\n"];
    foreach(themeFiles() as $name) if(!is_file($dir.'/'.$name)) file_put_contents($dir.'/'.$name,$defaults[$name]??"{{content}}\n");
}
function themeRead(int $id):array {
    themeInit($id); $files=[];foreach(themeFiles() as $name) $files[$name]=file_get_contents(themeDir($id).'/'.$name);return $files;
}
