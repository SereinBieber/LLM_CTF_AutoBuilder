<?php
// Type: Reflected XSS
// Difficulty: Easy

// 设置 HttpOnly 为 false (为了演示能偷 Cookie)
header("Set-Cookie: session_id=secret_token_123; path=/; HttpOnly=false");

$name = $_GET['name'];

if (isset($name)) {
    // 漏洞点：无 htmlspecialchars 过滤
    echo "<h1>Hello, " . $name . "</h1>";
} else {
    echo "<form>Your Name: <input type='text' name='name'><input type='submit'></form>";
}
?>