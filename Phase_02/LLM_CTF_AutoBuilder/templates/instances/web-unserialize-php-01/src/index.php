<?php
// web-unserialize-php-01 | PHP 反序列化漏洞
// 解法: ?data=O:4:"User":2:{s:8:"username";s:5:"admin";s:7:"isAdmin";b:1;}

error_reporting(0);

class User {
    public $username = 'guest';
    public $isAdmin  = false;

    public function __wakeup() {
        if ($this->isAdmin === true) {
            $this->showFlag();
        }
    }

    private function showFlag() {
        // 从/flag文件读取flag（由compose写入）
        $flag = @file_get_contents('/flag');
        if (!$flag) {
            $flag = getenv('FLAG') ?: 'FLAG_PLACEHOLDER';
        }
        echo "<div class='flag-box'>🚩 " . htmlspecialchars(trim($flag)) . "</div>";
    }
}

$data   = $_GET['data'] ?? '';
$result = '';
if ($data !== '') {
    $obj = unserialize($data);
}
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>用户反序列化挑战</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#1a1a2e;color:#eee;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#16213e;padding:40px;border-radius:8px;width:560px;
        box-shadow:0 4px 20px rgba(0,0,0,.4)}
  h2{color:#e94560;margin:0 0 20px}
  .hint{background:#0f3460;padding:14px;border-radius:4px;margin-bottom:20px;
        font-family:monospace;font-size:13px;color:#a8c0d6}
  .flag-box{background:#0a2d0a;border:1px solid #2ecc71;color:#2ecc71;
            padding:14px;border-radius:4px;margin-top:20px;
            font-family:monospace;font-size:15px;word-break:break-all}
  form{display:flex;gap:10px}
  input{flex:1;padding:10px;background:#0f3460;border:1px solid #2a4a7a;
        color:#eee;border-radius:4px;font-family:monospace;font-size:13px}
  button{padding:10px 20px;background:#e94560;color:#fff;border:none;
         border-radius:4px;cursor:pointer}
</style>
</head>
<body>
<div class="card">
  <h2>🔓 PHP 反序列化挑战</h2>
  <div class="hint">
    提示：构造一个序列化字符串，使 User 对象的 isAdmin 为 true<br>
    示例：<code>O:4:"User":2:{s:8:"username";s:5:"admin";s:7:"isAdmin";b:1;}</code>
  </div>
  <form method="GET">
    <input type="text" name="data" placeholder="输入序列化数据..." value="<?= htmlspecialchars($data) ?>">
    <button type="submit">提交</button>
  </form>
  <?php if ($data !== '' && isset($obj)): ?>
    <p>当前用户: <?= htmlspecialchars($obj->username ?? 'unknown') ?></p>
  <?php endif; ?>
</div>
</body>
</html>
