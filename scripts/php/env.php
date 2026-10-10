<?php
declare(strict_types=1);
function load_env_file(string $path): void {
    if(!is_file($path)) return;
    $lines=file($path, FILE_IGNORE_NEW_LINES);
    if($lines===false) return;
    foreach($lines as $line){
        $line=trim($line);
        if($line==='' || str_starts_with($line,'#')) continue;
        if(str_starts_with($line,'export ')) $line=trim(substr($line,7));
        if(!preg_match('/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/',$line,$m)) continue;
        if(getenv($m[1])!==false) continue;
        $value=trim($m[2]);
        if(strlen($value)>=2 && ($value[0]==='"' || $value[0]==="'") && $value[0]===$value[strlen($value)-1]) $value=substr($value,1,-1);
        putenv($m[1].'='.$value);
        $_ENV[$m[1]]=$value;
    }
}
