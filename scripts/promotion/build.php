<?php
declare(strict_types=1);
require __DIR__.'/../../new-project/app/src/bootstrap.php';
require __DIR__.'/../../new-project/app/src/promotion.php';
$config=promotionConfig();promotionSave($config);
$dir=ROOT.'/dist/promotion';if(!is_dir($dir))mkdir($dir,0755,true);
copy(ROOT.'/.local/promotion/index.html',$dir.'/index.html');
echo "已生成 dist/promotion/index.html\n";
