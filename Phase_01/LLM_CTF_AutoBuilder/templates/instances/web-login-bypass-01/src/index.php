<?php
// web-login-bypass-01 | 登录表单 SQL 注入（万能密码）
// 解法: username = admin' OR '1'='1'--+   password = 任意

session_start();
$conn = new mysqli(
    getenv('DB_HOST') ?: 'db',
    getenv('DB_USER') ?: 'ctf_user',
    getenv('DB_PASS') ?: '',
    getenv('DB_NAME') ?: 'ctf_db'
);
if ($conn->connect_error) die("服务暂时不可用");

$error = $success = $flag = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $user = $_POST['username'] ?? '';
    $pass = $_POST['password'] ?? '';
    // 漏洞点：username 和 password 均未过滤
    $sql = "SELECT * FROM admins WHERE username='$user' AND password='$pass'";
    $r = $conn->query($sql);
    if ($r && $r->num_rows > 0) {
        $row     = $r->fetch_assoc();
        $flag    = $row['flag'];
        $success = "登录成功！欢迎，" . htmlspecialchars($row['username']);
    } else {
        $error = "用户名或密码错误";
    }
    $conn->close();
}
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>后台管理登录</title>
<style>
  *{box-sizing:border-box}
  body{font-family:"Microsoft YaHei",sans-serif;background:#0f0f23;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .box{background:#1a1a2e;padding:44px 40px;border-radius:10px;width:380px;
       box-shadow:0 0 30px rgba(233,69,96,.2)}
  h2{color:#e94560;text-align:center;margin:0 0 28px;letter-spacing:2px}
  label{color:#aaa;font-size:13px;display:block;margin-bottom:6px}
  input[type=text],input[type=password]{width:100%;padding:11px 14px;background:#0f3460;
    border:1px solid #1a4a7a;color:#eee;border-radius:5px;font-size:14px;margin-bottom:18px}
  input:focus{outline:none;border-color:#e94560}
  button{width:100%;padding:12px;background:#e94560;color:#fff;border:none;
         border-radius:5px;font-size:15px;cursor:pointer;letter-spacing:1px}
  button:hover{background:#c73652}
  .msg{margin-top:18px;padding:12px;border-radius:5px;font-size:14px;text-align:center}
  .err{background:#2d0a0a;color:#ff6b6b;border:1px solid #e94560}
  .ok{background:#0a2d0a;color:#6bff6b;border:1px solid #2ecc71}
  .flag{margin-top:14px;background:#0a1628;border:1px dashed #f5a623;padding:14px;
        border-radius:5px;color:#f5a623;font-family:monospace;font-size:15px;
        word-break:break-all;text-align:center}
  .foot{color:#555;font-size:11px;text-align:center;margin-top:20px}
</style>
</head>
<body>
<div class="box">
  <h2>🔐 后台管理系统</h2>
  <form method="POST">
    <label>用户名</label>
    <input type="text" name="username" placeholder="管理员账号" autocomplete="off">
    <label>密码</label>
    <input type="password" name="password" placeholder="密码">
    <button type="submit">登 录</button>
  </form>
  <?php if ($error): ?>
    <div class="msg err"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>
  <?php if ($success): ?>
    <div class="msg ok"><?= $success ?></div>
    <div class="flag">🚩 <?= htmlspecialchars($flag) ?></div>
  <?php endif; ?>
  <p class="foot">内部系统，禁止未授权访问</p>
</div>
</body>
</html>
