<?php
// web-sqli-easy-01 | UNION 联合查询注入
// 解法: ?id=1 UNION SELECT password FROM users--+

$conn = new mysqli(
    getenv('DB_HOST') ?: 'db',
    getenv('DB_USER') ?: 'ctf_user',
    getenv('DB_PASS') ?: '',
    getenv('DB_NAME') ?: 'ctf_db'
);
if ($conn->connect_error) die("服务暂时不可用");

$id = isset($_GET['id']) ? $_GET['id'] : '1';
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>员工信息查询</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#f0f2f5;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#fff;padding:40px;border-radius:8px;
        box-shadow:0 2px 12px rgba(0,0,0,.1);width:420px}
  h2{margin:0 0 20px;color:#1a1a2e;text-align:center}
  input[type=text]{width:100%;padding:10px;border:1px solid #ddd;
                   border-radius:4px;font-size:14px;box-sizing:border-box}
  button{width:100%;padding:10px;background:#4a90e2;color:#fff;border:none;
         border-radius:4px;cursor:pointer;font-size:15px;margin-top:10px}
  button:hover{background:#357abd}
  .result{margin-top:20px;padding:15px;background:#f9f9f9;
          border-left:4px solid #4a90e2;border-radius:4px;min-height:40px}
  .hint{margin-top:12px;font-size:12px;color:#aaa;text-align:center}
</style>
</head>
<body>
<div class="card">
  <h2>🔍 员工信息查询系统</h2>
  <form method="GET">
    <input type="text" name="id" placeholder="请输入员工 ID"
           value="<?= htmlspecialchars($id) ?>">
    <button type="submit">查 询</button>
  </form>
  <div class="result">
    <?php
    // 漏洞点：$id 未过滤直接拼入 SQL，只查 username
    // flag 藏在 password 列，需 UNION SELECT 带出
    $r = $conn->query("SELECT username FROM users WHERE id = $id");
    if ($r && $r->num_rows > 0) {
        while ($row = $r->fetch_assoc())
            echo "员工姓名：<strong>" . $row['username'] . "</strong><br>";
    } else {
        echo "未找到该员工";
    }
    $conn->close();
    ?>
  </div>
  <p class="hint">本系统仅展示员工姓名，其余字段受权限保护</p>
</div>
</body>
</html>
