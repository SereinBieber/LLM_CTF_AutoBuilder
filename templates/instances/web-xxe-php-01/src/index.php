<?php
// Type: XXE (XML External Entity)
// Difficulty: Medium
// Description: XML Data Processor.

// 允许加载外部实体 (这是漏洞的核心)
libxml_disable_entity_loader(false);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // 获取 POST 的原始数据 (XML)
    $xmlfile = file_get_contents('php://input');
    
    if (isset($xmlfile)) {
        // 漏洞点：直接解析 XML，未禁用 DOCTYPE
        // Payload: 
        // <!DOCTYPE foo [ <!ELEMENT foo ANY > <!ENTITY xxe SYSTEM "file:///etc/passwd" > ]>
        // <user><name>&xxe;</name></user>
        $dom = new DOMDocument();
        $dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);
        $creds = simplexml_import_dom($dom);
        
        echo "Hello, " . $creds->name;
    }
} else {
    echo "<h1>XML API Endpoint</h1>";
    echo "<p>Send POST request with XML body: &lt;user&gt;&lt;name&gt;Guest&lt;/name&gt;&lt;/user&gt;</p>";
}
?>