<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') exit;
require __DIR__.'/../../new-project/app/src/bootstrap.php';
$lock=fopen(ROOT.'/.local/install.lock','c'); flock($lock,LOCK_EX);
db()->exec("CREATE TABLE IF NOT EXISTS mvp_users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(80) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, login_failures INT NOT NULL DEFAULT 0, locked_until DATETIME NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
db()->exec("CREATE TABLE IF NOT EXISTS mvp_sites (id INT AUTO_INCREMENT PRIMARY KEY, host VARCHAR(253) NOT NULL UNIQUE, base_url VARCHAR(300) NOT NULL, name VARCHAR(120) NOT NULL, description VARCHAR(500) NOT NULL, indexable BOOLEAN NOT NULL DEFAULT 0, created_at DATETIME NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
db()->exec("CREATE TABLE IF NOT EXISTS mvp_articles (id INT AUTO_INCREMENT PRIMARY KEY, site_id INT NOT NULL, slug VARCHAR(160) NOT NULL, title VARCHAR(180) NOT NULL, description VARCHAR(500) NOT NULL, category VARCHAR(80) NOT NULL, content MEDIUMTEXT NOT NULL, status ENUM('draft','published') NOT NULL DEFAULT 'draft', published_at DATETIME NULL, updated_at DATETIME NOT NULL, UNIQUE KEY site_slug(site_id,slug), KEY site_status_date(site_id,status,published_at), CONSTRAINT mvp_article_site FOREIGN KEY(site_id) REFERENCES mvp_sites(id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
if (!(int)query('SELECT COUNT(*) FROM mvp_users')->fetchColumn()) {
    $password=bin2hex(random_bytes(10));
    query('INSERT INTO mvp_users(username,password) VALUES(?,?)',['admin',password_hash($password,PASSWORD_DEFAULT)]);
    file_put_contents(ROOT.'/.local/admin-credentials.txt',"本地管理后台：http://localhost:8080/admin\n用户名：admin\n初始密码：$password\n首次登录后请在后台修改密码；此文件不会同步更新。\n");
    chmod(ROOT.'/.local/admin-credentials.txt',0600);
}
if (!(int)query('SELECT COUNT(*) FROM mvp_sites')->fetchColumn()) {
    db()->beginTransaction();
    try {
        foreach ([['localhost','http://localhost:8080','知识与工具','记录实用工具、工作方法与经过验证的操作指南。'],['127.0.0.1','http://127.0.0.1:8080','生活与手记','从日常问题出发，整理有用的经验与观察。']] as $s) {
            query('INSERT INTO mvp_sites(host,base_url,name,description,created_at) VALUES(?,?,?,?,NOW())',$s);
            $id=(int)db()->lastInsertId();
            $first=$s[0]==='localhost';
            query('INSERT INTO mvp_articles(site_id,slug,title,description,category,content,status,published_at,updated_at) VALUES(?,?,?,?,?,?,?,NOW(),NOW())',[$id,$first?'build-a-useful-tool-library':'organize-your-daily-notes',$first?'如何整理一个真正有用的工具库':'把零散记录整理成可查找的生活手记',$first?'用任务分类、使用记录和定期检查，让工具收藏变得可用。':'从具体问题开始记录，保留日期与结果，让经验可以再次使用。',$first?'工作方法':'日常整理',$first?"收藏工具前，先写下自己要解决的具体问题。以任务为分类，例如图片处理、文档整理、数据核对，通常比按工具厂商分类更容易找到需要的内容。\n\n为每个工具保留用途、适用条件、实际测试日期和限制。只记录自己验证过的结果，不把宣传语当作结论。\n\n每月检查常用链接是否仍有效。遇到工具变化，补充变更说明；无法继续访问的条目可以暂时下架，避免让读者反复遇到失效页面。\n\n这是一篇用于验证站点展示的示例文章，正式上线前请替换为自己有实测依据的内容。":"每天的记录可以从一个具体问题开始，例如怎样安排一次采购，或怎样保存常用资料。标题尽量写清楚问题，正文记录条件、做法和结果。\n\n给记录添加稳定的分类。不要为每一篇新建一个分类；先用少量主题，积累之后再拆分。\n\n重新使用一条旧记录时，核对其中的时间和条件是否仍然适用。补充自己的新发现，让记录随着实际经验持续更新。\n\n这是一篇本地展示用示例文章，正式上线前请替换为自己的真实记录。",'published']);
        }
        db()->commit();
    } catch(Throwable $e) { db()->rollBack(); throw $e; }
}
echo "Native station manager initialized. Credentials: .local/admin-credentials.txt\n";

require __DIR__.'/editorial-migrate.php';

require __DIR__.'/site-settings-migrate.php';
