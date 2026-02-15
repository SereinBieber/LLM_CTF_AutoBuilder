<?php
// Type: LFI (Local File Inclusion)
// Difficulty: Medium
// Description: Dynamic page loader vulnerability.

$page = $_GET['page'];

if (isset($page)) {
    // 漏洞点：直接 include 用户传入的路径
    // Payload: ?page=../../../../etc/passwd
    // Payload: ?page=php://filter/read=convert.base64-encode/resource=index.php
    include($page);
} else {
    echo "<h1>Welcome</h1>";
    echo "<a href='?page=home.php'>Home</a> | <a href='?page=about.php'>About</a>";
    echo "";
}
?>