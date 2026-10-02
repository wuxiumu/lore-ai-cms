<?php
if (preg_match('~^/theme/site-([1-9][0-9]*)/(style\.css|script\.js)$~',parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH),$asset)) {
    $file=__DIR__.'/../../themes/site-'.$asset[1].'/'.$asset[2];
    if(!is_file($file)) { http_response_code(404);return; }
    header('Content-Type: '.($asset[2]==='style.css'?'text/css':'application/javascript').'; charset=utf-8');header('X-Content-Type-Options: nosniff');readfile($file);return;
}
$path=parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH);
if ($path==='/style.css') { header('Content-Type: text/css; charset=utf-8'); readfile(__DIR__.'/style.css'); return; }
if (preg_match('~^/covers/([a-z-]+)\.svg$~',$path,$m) && is_file(__DIR__.'/covers/'.$m[1].'.svg')) { header('Content-Type: image/svg+xml'); header('X-Content-Type-Options: nosniff'); readfile(__DIR__.'/covers/'.$m[1].'.svg'); return; }
require __DIR__.'/index.php';
