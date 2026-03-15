<?php
// web-unserialize-php-01 | PHP 反序列化漏洞
// 解法: ?data=O:4:"User":2:{s:8:"username";s:5:"admin";s:7:"isAdmin";b:1;}

error_reporting(0);

class User {
    public $username = 'guest';
    public $isAdmin  = false;

    public function __wakeup() {
        // 反序列化时自动触发
        if ($this->isAdmin === true) {
            $this->showFlag();
        }
    }

    private function showFlag() {
        $flag = getenv('FLAG') ?: 'FLAG_PLACEHOLDER';
        echo "<div class='flag-box'>🚩 " . htmlspecialchars($flag) . "</div>";
    }
}

$data   = $_GET['data'] ?? '';
$result = '';
if ($data !== '') {
    // 漏洞点：直接反序列化用户输入
    $obj = unserialize($data);
}
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>用户中心</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#f0f2f5;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#fff;padding:40px;border-radius:8px;
        box-shadow:0 2px 12px rgba(0,0,0,.1);width:500px}
  h2{margin:0 0 20px;color:#333;text-align:center}
  .info{background:#f9f9f9;padding:16px;border-radius:6px;
        border-left:4px solid #4a90e2;margin-bottom:20px;font-size:14px;color:#555}
  .info code{background:#eee;padding:2px 6px;border-radius:3px;font-size:13px}
  input[type=text]{width:100%;padding:10px;border:1px solid #ddd;
                   border-radius:4px;font-size:13px;box-sizing:border-box;font-family:monospace}
  button{width:100%;padding:10px;background:#8e44ad;color:#fff;border:none;
         border-radius:4px;cursor:pointer;font-size:15px;margin-top:10px}
  button:hover{background:#7d3c98}
  .flag-box{margin-top:20px;background:#0a1628;border:1px dashed #f5a623;padding:16px;
            border-radius:6px;color:#f5a623;font-family:monospace;font-size:15px;
            word-break:break-all;text-align:center}
  .welcome{margin-top:20px;padding:12px;background:#eafaf1;
           border:1px solid #2ecc71;border-radius:6px;color:#1e8449;text-align:center}
</style>
</head>
<body>
<div class="card">
  <h2>👤 用户中心</h2>
  <div class="info">
    <p>本系统通过序列化数据识别用户身份。</p>
    <p>普通用户 data 示例：<br>
    <code>O:4:"User":1:{s:8:"username";s:5:"guest";}</code></p>
    <p>管理员才能看到 flag。</p>
  </div>
  <form method="GET">
    <input type="text" name="data" placeholder="请粘贴序列化数据"
           value="<?= htmlspecialchars($data) ?>">
    <button type="submit">验 证</button>
  </form>
  <?php
  if ($data !== '' && isset($obj)) {
      if (!($obj instanceof User) || !$obj->isAdmin) {
          echo "<div class='welcome'>欢迎，" . htmlspecialchars($obj->username ?? 'unknown') . "（普通用户）</div>";
      }
  }
  ?>
</div>
</body>
</html>
