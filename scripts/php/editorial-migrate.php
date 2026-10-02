<?php
declare(strict_types=1);
if(PHP_SAPI!=='cli') exit;
require_once __DIR__.'/../../new-project/app/src/bootstrap.php';
db()->exec("CREATE TABLE IF NOT EXISTS mvp_article_meta (article_id INT PRIMARY KEY, metadata JSON NOT NULL, CONSTRAINT mvp_meta_article FOREIGN KEY(article_id) REFERENCES mvp_articles(id) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
db()->exec("CREATE TABLE IF NOT EXISTS mvp_editorial_jobs (id INT AUTO_INCREMENT PRIMARY KEY, site_id INT NOT NULL, topic_key CHAR(64) NOT NULL, article_id INT NOT NULL, status VARCHAR(20) NOT NULL, title VARCHAR(180) NOT NULL, created_at DATETIME NOT NULL, UNIQUE KEY site_topic(site_id,topic_key), CONSTRAINT mvp_job_site FOREIGN KEY(site_id) REFERENCES mvp_sites(id), CONSTRAINT mvp_job_article FOREIGN KEY(article_id) REFERENCES mvp_articles(id) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
echo "Editorial schema ready.\n";
