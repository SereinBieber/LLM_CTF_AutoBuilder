<?php
// 🛡️ CTF 漏洞环境 - 预制 SQL 注入题目
// 考点：Union Based SQL Injection

echo "<h2>用户信息查询系统</h2>";
$id = $_GET['id']; // 💡 漏洞点：直接获取参数，没有任何过滤

if (isset($id)) {
    if (strpos($id, 'union') !== false) {
        // flag{php_vulnerability_challenge} 会在 builder 注入时被替换为真实 flag
        echo "恭喜你！Flag 就在这里：flag{php_vulnerability_challenge}";
    } else {
        echo "正在查询 ID 为 " . htmlspecialchars($id) . " 的用户数据...<br>";
        echo "结果：未找到该用户，请尝试其他注入手段。";
    }
} else {
    echo "使用方法：?id=1";
}
?>