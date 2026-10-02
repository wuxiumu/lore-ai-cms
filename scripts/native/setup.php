<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$root=dirname(__DIR__,2); $dir=$root.'/.local';
if (!is_dir($dir)) mkdir($dir,0700,true);
if (is_file($dir.'/native.json')) { echo "Existing database configuration retained.\n"; exit; }
// Provisioning credentials are independent of the legacy project.
$dbhost=getenv('MVP_DB_ADMIN_HOST') ?: '127.0.0.1';
$dbuser=getenv('MVP_DB_ADMIN_USER') ?: 'root';
$dbpassword=getenv('MVP_DB_ADMIN_PASSWORD') ?: '';
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
try {
    $db=new mysqli($dbhost,$dbuser,$dbpassword);
    $name='zdmsl_native_'.bin2hex(random_bytes(4));
    $user='native_'.bin2hex(random_bytes(4));
    $password=bin2hex(random_bytes(24));
    $db->query("CREATE DATABASE `$name` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci");
    $db->query("CREATE USER '$user'@'localhost' IDENTIFIED BY '$password'");
    $db->query("GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,ALTER,INDEX,REFERENCES ON `$name`.* TO '$user'@'localhost'");
    file_put_contents($dir.'/native.json',json_encode(['host'=>$dbhost,'database'=>$name,'user'=>$user,'password'=>$password],JSON_PRETTY_PRINT));
    chmod($dir.'/native.json',0600);
    echo "Isolated local database and runtime account created.\n";
} catch(Throwable $e) {
    fwrite(STDERR,"Database provisioning failed (code ".$e->getCode()."). Check MySQL and provisioning credentials. No existing database was reset.\n");
    exit(1);
}
