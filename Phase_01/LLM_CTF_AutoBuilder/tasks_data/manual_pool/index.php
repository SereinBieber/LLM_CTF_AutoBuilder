<?php
// 🛡️ CTF 漏洞环境 - 预制 SQL 注入题目
// 考点：Union Based SQL Injection

$host = "localhost";
$user = "ctf_user";
$pass = "password";
$db   = "ctf_database";

// 模拟数据库连接（在大创展示时，这里可以写死或者连真实的 Docker 数据库）
echo "<h2>用户信息查询系统</h2>";
$id = $_GET['id']; // 💡 漏洞点：直接获取参数，没有任何过滤

if (isset($id)) {
    // 模拟查询逻辑
    if (strpos($id, 'union') !== false) {
        // 模拟 flag 弹出
        echo "恭喜你！Flag 就在这里：flag{SQL_iNjecTi0n_SuCc3ss_2026}";
    } else {
        echo "正在查询 ID 为 " . htmlspecialchars($id) . " 的用户数据...<br>";
        echo "结果：未找到该用户，请尝试其他注入手段。";
    }
} else {
    echo "使用方法：?id=1";
}
?>