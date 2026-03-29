<?php
// web-lfi-php-01 | 本地文件包含（LFI）
// 解法1: ?page=../../../../etc/passwd
// 解法2: ?page=php://filter/read=convert.base64-encode/resource=index.php
// 解法3: ?page=../../../../flag  (flag 写在 /flag)

error_reporting(0);

// 启动时把 FLAG 写入 /flag
$flag_val = getenv('FLAG');
if ($flag_val && $flag_val !== 'FLAG_PLACEHOLDER') {
    file_put_contents('/flag', $flag_val);
}

$page = $_GET['page'] ?? '';
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>企业内网门户</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;margin:0;background:#f7f8fa}
  nav{background:#2c3e50;padding:14px 30px;color:#fff;display:flex;gap:20px;align-items:center}
  nav a{color:#ecf0f1;text-decoration:none;font-size:15px}
  nav a:hover{color:#3498db}
  .content{padding:40px;max-width:800px;margin:0 auto}
  h2{color:#2c3e50}
  .page-body{background:#fff;padding:30px;border-radius:6px;
             box-shadow:0 1px 4px rgba(0,0,0,.1);margin-top:20px}
</style>
</head>
<body>
<nav>
  <strong>🏢 企业内网门户</strong>
  <a href="?page=home.php">首页</a>
  <a href="?page=about.php">关于我们</a>
</nav>
<div class="content">
  <?php if ($page !== ''): ?>
    <div class="page-body">
      <?php
      // 漏洞点：直接 include 用户输入，未做路径限制
      include($page);
      ?>
    </div>
  <?php else: ?>
    <h2>欢迎访问企业内网门户</h2>
    <p>请从顶部导航选择页面，或直接通过 <code>?page=</code> 参数加载内容。</p>
  <?php endif; ?>
</div>
</body>
</html>
