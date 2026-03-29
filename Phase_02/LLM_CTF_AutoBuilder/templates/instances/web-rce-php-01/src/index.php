<?php
// web-rce-php-01 | RCE 远程命令执行（命令注入）
// 解法: ?ip=127.0.0.1; cat /flag
// 或: ?ip=127.0.0.1|cat /flag

error_reporting(0);

// 启动时把 FLAG 环境变量写入 /flag 文件，模拟真实 CTF 环境
$flag_val = getenv('FLAG');
if ($flag_val && $flag_val !== 'FLAG_PLACEHOLDER') {
    file_put_contents('/flag', $flag_val);
}

$target = $_REQUEST['ip'] ?? '';
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>网络诊断工具</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#f5f5f5;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#fff;padding:40px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.1);width:500px}
  h2{margin:0 0 20px;color:#333;text-align:center}
  input[type=text]{width:100%;padding:10px;border:1px solid #ddd;
                   border-radius:4px;font-size:14px;box-sizing:border-box}
  button{width:100%;padding:10px;background:#27ae60;color:#fff;border:none;
         border-radius:4px;cursor:pointer;font-size:15px;margin-top:10px}
  button:hover{background:#219150}
  pre{background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:4px;
      margin-top:20px;overflow-x:auto;font-size:13px;min-height:60px}
</style>
</head>
<body>
<div class="card">
  <h2>🌐 网络诊断工具</h2>
  <form method="GET">
    <input type="text" name="ip" placeholder="请输入目标 IP（如 127.0.0.1）"
           value="<?= htmlspecialchars($target) ?>">
    <button type="submit">开始诊断</button>
  </form>
  <?php if ($target !== ''): ?>
  <pre><?php
    // 漏洞点：$target 未过滤，直接拼入 shell 命令
    $cmd = "ping -c 2 " . $target;
    echo "$ " . htmlspecialchars($cmd) . "\n\n";
    system($cmd);
  ?></pre>
  <?php endif; ?>
</div>
</body>
</html>
