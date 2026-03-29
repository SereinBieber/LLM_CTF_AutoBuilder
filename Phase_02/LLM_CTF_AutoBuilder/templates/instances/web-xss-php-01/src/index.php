<?php
// web-xss-php-01 | 反射型 XSS
// 解法: ?name=<script>alert(document.cookie)</script>
// flag 藏在 Cookie 的 secret_flag 中

// FLAG_PLACEHOLDER 会被 builder 替换为真实 flag
header("Set-Cookie: secret_flag=FLAG_PLACEHOLDER; path=/; HttpOnly=false");

$name = $_GET['name'] ?? '';
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>留言板</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#f5f5f5;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#fff;padding:40px;border-radius:8px;
        box-shadow:0 2px 12px rgba(0,0,0,.1);width:440px}
  h2{margin:0 0 20px;color:#333;text-align:center}
  input[type=text]{width:100%;padding:10px;border:1px solid #ddd;
                   border-radius:4px;font-size:14px;box-sizing:border-box}
  button{width:100%;padding:10px;background:#8e44ad;color:#fff;border:none;
         border-radius:4px;cursor:pointer;font-size:15px;margin-top:10px}
  .output{margin-top:20px;padding:16px;background:#f9f0ff;
          border-left:4px solid #8e44ad;border-radius:4px;min-height:40px}
  .hint{font-size:12px;color:#aaa;text-align:center;margin-top:12px}
</style>
</head>
<body>
<div class="card">
  <h2>💬 留言板</h2>
  <form method="GET">
    <input type="text" name="name" placeholder="请输入你的名字"
           value="<?= htmlspecialchars($name) ?>">
    <button type="submit">提 交</button>
  </form>
  <?php if ($name !== ''): ?>
  <div class="output">
    欢迎你，<?= $name /* 漏洞点：未过滤直接输出 */ ?>！
  </div>
  <?php endif; ?>
  <p class="hint">友情提示：你的身份凭证已安全存储在 Cookie 中 😉</p>
</div>
</body>
</html>
