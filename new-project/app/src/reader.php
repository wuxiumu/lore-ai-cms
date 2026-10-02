<?php
declare(strict_types=1);
function readerNavigation(?array $previous, ?array $next): string {
    $out='<nav class="reader-navigation" aria-label="文章翻页">';
    foreach([['上一篇',$previous,'prev'],['下一篇',$next,'next']] as [$label,$a,$rel]) {
        $out.=$a?'<a rel="'.$rel.'" href="/article/'.h($a['slug']).'.html"><span>'.$label.'</span><strong>'.h($a['title']).'</strong></a>':'<div><span>'.$label.'</span><strong>已经是'.($rel==='prev'?'第一':'最后一').'篇了</strong></div>';
    }
    return $out.'</nav>';
}
function readerFooter(array $site): string {
    $about=defined('STATIC_EXPORT')?'/about.html':'/about';
    return '<section class="reader-footer" aria-label="关于我们、联系与赞助"><div class="reader-footer-inner"><div><h2>关于我们</h2><p>'.h($site['name']).'，记录城市故事，与好奇的人分享阅读的乐趣。</p><p><a href="'.$about.'">了解本站 →</a></p></div><div><h2>联系方式</h2><p>邮箱：<a href="mailto:wuxiumu@163.com">wuxiumu@163.com</a></p><p>微信：<strong>qingbao199101</strong><br>添加好友请备注来意。</p></div><div class="reader-support"><h2>赞助支持</h2><p>如果故事让你喜欢，欢迎自愿赞助。</p><div class="reader-codes"><figure><button type="button" class="reader-code-button" aria-label="放大赞助码" aria-haspopup="dialog"><img src="https://chiguashentan-test.oss-cn-beijing.aliyuncs.com/wxprogram/zan/20261002185236_31_227.png" alt="微信赞赏码，点击查看大图" loading="lazy" width="160" height="160"></button><figcaption>微信赞赏码</figcaption></figure><figure><button type="button" class="reader-code-button" aria-label="放大赞助码" aria-haspopup="dialog"><img src="https://chiguashentan-test.oss-cn-beijing.aliyuncs.com/wxprogram/zan/20261002185309_32_227.jpg" alt="支付宝收款码，点击查看大图" loading="lazy" width="160" height="160"></button><figcaption>支付宝收款码</figcaption></figure></div></div></div></section><dialog class="reader-lightbox" aria-labelledby="reader-code-title"><div class="reader-lightbox-panel"><button type="button" class="reader-lightbox-close" aria-label="关闭大图" autofocus>×</button><h2 id="reader-code-title">赞助码</h2><img class="reader-lightbox-image" alt=""><p>感谢你的支持</p></div></dialog>';
}

function readerTools(array $site): string {
    $count=max(1,min(20,(int)($site['image_count']??5)));
    return '<section class="reader-tools" data-image-count="'.$count.'" aria-label="复制分享与转图"><h2>把故事带走</h2><p>转图：复制正文与简约漫画素描提示词，按'.$count.'张图编排，粘贴到绘图模型使用。</p><div><button type="button" data-reader-action="copy">复制内容</button><button type="button" data-reader-action="share">分享</button><button type="button" data-reader-action="link">复制链接</button><button type="button" data-reader-action="image">转图 · '.$count.'张</button></div><p class="reader-tools-feedback" role="status" aria-live="polite"></p><textarea class="reader-copy-fallback" aria-label="手动复制内容" rows="8" hidden readonly></textarea></section>';
}
