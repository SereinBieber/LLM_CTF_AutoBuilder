<?php
// Type: RCE (Remote Command Execution)
// Difficulty: Easy
// Description: A simple ping tool that lacks input validation.

error_reporting(0);

// 获取 Flag 的逻辑：从环境变量写入文件，模拟真实 CTF 环境
if (getenv('FLAG')) {
    file_put_contents('/flag', getenv('FLAG'));
}

$target = $_REQUEST['ip'];

if (isset($target)) {
    // 漏洞点：未过滤直接拼接命令
    $cmd = "ping -c 2 " . $target;
    echo "<pre>Executing: $cmd\n\n";
    system($cmd);
    echo "</pre>";
} else {
    echo "<h1>Network Ping Tool</h1>";
    echo "<form>IP Address: <input type='text' name='ip' value='127.0.0.1'><input type='submit'></form>";
    echo "";
}
?>