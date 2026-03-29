<?php
// web-ssrf-php-01 | SSRF 服务端请求伪造
// 解法: ?url=file:///flag

error_reporting(0);
$flag_val = getenv('FLAG');
if ($flag_val && $flag_val !== 'FLAG_PLACEHOLDER') {
    file_put_contents('/flag', $flag_val);
}

$url = $_GET['url'] ?? '';
$result = '';
if ($url !== '') {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_HEADER, 0);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    // 漏洞点：未过滤 file:// 和内网 IP
    $result = curl_exec($ch);
    if ($result === false) $result = "请求失败：" . curl_error($ch);
    curl_close($ch);
}
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>网页内容抓取工具</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#f5f5f5;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#fff;padding:40px;border-radius:8px;
        box-shadow:0 2px 12px rgba(0,0,0,.1);width:560px}
  h2{margin:0 0 6px;color:#333;text-align:center}
  .sub{text-align:center;color:#888;font-size:13px;margin-bottom:24px}
  input[type=text]{width:100%;padding:10px;border:1px solid #ddd;
                   border-radius:4px;font-size:14px;box-sizing:border-box}
  button{width:100%;padding:10px;background:#16a085;color:#fff;border:none;
         border-radius:4px;cursor:pointer;font-size:15px;margin-top:10px}
  button:hover{background:#138d75}
  pre{background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:4px;
      margin-top:20px;overflow:auto;font-size:13px;max-height:300px;white-space:pre-wrap}
</style>
</head>
<body>
<div class="card">
  <h2>🌐 网页内容抓取工具</h2>
  <p class="sub">输入任意 URL，服务器将帮你获取内容</p>
  <form method="GET">
    <input type="text" name="url" placeholder="https://example.com"
           value="<?= htmlspecialchars($url) ?>">
    <button type="submit">抓 取</button>
  </form>
  <?php if ($result !== ''): ?>
    <pre><?= htmlspecialchars($result) ?></pre>
  <?php endif; ?>
</div>
</body>
</html>
