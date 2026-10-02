<?php
require_once __DIR__.'/../../new-project/app/src/bootstrap.php';
foreach(['image_count'=>"INT NOT NULL DEFAULT 5",'seo_title'=>"VARCHAR(200) NOT NULL DEFAULT ''",'seo_description'=>"VARCHAR(500) NOT NULL DEFAULT ''",'seo_keywords'=>"VARCHAR(500) NOT NULL DEFAULT ''",'content_topic'=>"VARCHAR(1000) NOT NULL DEFAULT ''",'topic_keywords'=>"VARCHAR(1000) NOT NULL DEFAULT ''"] as $column=>$type) {
    if(!query("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='mvp_sites' AND COLUMN_NAME=?",[$column])->fetch()) db()->exec("ALTER TABLE mvp_sites ADD COLUMN $column $type");
}
echo "Site settings ready.\n";
