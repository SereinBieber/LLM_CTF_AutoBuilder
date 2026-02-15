<?php
// Type: SSRF (Server-Side Request Forgery)
// Difficulty: Medium
// Description: URL Fetcher service.

if (isset($_GET['url'])) {
    $url = $_GET['url'];
    
    // 初始化 curl
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_HEADER, 0);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    
    // 漏洞点：没有过滤内网 IP (127.0.0.1) 或 协议 (file:///)
    $result = curl_exec($ch);
    curl_close($ch);
    
    echo $result;
} else {
    echo "<h1>Image/Page Fetcher</h1>";
    echo "<form>URL: <input type='text' name='url'><input type='submit'></form>";
}
?>