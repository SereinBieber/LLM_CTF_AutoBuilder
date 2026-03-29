<?php
// web-sqli-medium-01 | 报错注入（Error-based）
// 解法: ?category=daily' AND extractvalue(1,concat(0x7e,(SELECT val FROM secret LIMIT 1)))--+

$conn = new mysqli(
    getenv('DB_HOST') ?: 'db',
    getenv('DB_USER') ?: 'ctf_user',
    getenv('DB_PASS') ?: '',
    getenv('DB_NAME') ?: 'ctf_db'
);
if ($conn->connect_error) die("服务暂时不可用");

$category = isset($_GET['category']) ? $_GET['category'] : 'daily';
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>商品分类浏览</title>
<style>
  *{box-sizing:border-box}
  body{font-family:"Microsoft YaHei",sans-serif;background:#1a1a2e;color:#eee;margin:0;padding:30px}
  h2{color:#e94560}
  .bar{display:flex;gap:10px;margin-bottom:24px}
  .bar input{padding:10px 14px;border:1px solid #444;background:#16213e;
             color:#eee;border-radius:4px;font-size:14px;width:280px}
  .bar button{padding:10px 20px;background:#e94560;color:#fff;border:none;
              border-radius:4px;cursor:pointer}
  .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
  .card{background:#16213e;padding:20px;border-radius:6px;border:1px solid #0f3460}
  .card h4{margin:0 0 8px;color:#e94560}
  .price{font-size:18px;font-weight:bold;color:#f5a623}
  .err{background:#2d0a0a;border:1px solid #e94560;color:#ff6b6b;
       padding:14px;border-radius:4px;margin-top:20px;font-family:monospace;font-size:13px}
  .count{color:#aaa;font-size:13px;margin-bottom:12px}
</style>
</head>
<body>
<h2>🛒 商品分类浏览</h2>
<form class="bar" method="GET">
  <input type="text" name="category" placeholder="输入分类（如 daily）"
         value="<?= htmlspecialchars($category) ?>">
  <button type="submit">筛 选</button>
</form>
<?php
// 漏洞点：$category 未过滤，直接拼入 SQL
// 查询结果仅显示数量，不回显具体内容
// flag 在 secret 表，需通过 MySQL 报错信息带出
$sql = "SELECT id, name, price FROM products WHERE category = '$category'";
$r = $conn->query($sql);
if ($r) {
    echo "<p class='count'>共 {$r->num_rows} 件商品</p><div class='grid'>";
    while ($row = $r->fetch_assoc()) {
        echo "<div class='card'><h4>" . htmlspecialchars($row['name']) . "</h4>"
           . "<span class='price'>¥{$row['price']}</span></div>";
    }
    echo "</div>";
} else {
    // 直接输出 MySQL 报错 —— 这就是漏洞所在
    echo "<div class='err'>⚠️ 查询出错：" . $conn->error . "</div>";
}
$conn->close();
?>
</body>
</html>
