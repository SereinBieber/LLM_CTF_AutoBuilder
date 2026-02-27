<?php
// web-upload-php-01 | 文件上传绕过（MIME 类型校验）
// 解法: 上传 .php 文件，Content-Type 设为 image/jpeg

error_reporting(0);
$flag_val = getenv('FLAG');
if ($flag_val && $flag_val !== 'FLAG_PLACEHOLDER') {
    file_put_contents('/flag', $flag_val);
}

$target_dir = "uploads/";
if (!file_exists($target_dir)) mkdir($target_dir, 0777, true);

$msg = $msg_type = '';

if (isset($_POST["submit"])) {
    $target_file = $target_dir . basename($_FILES["fileToUpload"]["name"]);
    // 漏洞点：只校验 MIME，不校验后缀名
    if ($_FILES["fileToUpload"]["type"] != "image/jpeg") {
        $msg = "❌ 只允许上传 JPG 图片！";
        $msg_type = "err";
    } else {
        if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
            $msg = "✅ 文件已上传至：" . htmlspecialchars($target_file);
            $msg_type = "ok";
        } else {
            $msg = "❌ 上传失败，请重试";
            $msg_type = "err";
        }
    }
}
?>
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>头像上传</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#f0f2f5;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#fff;padding:40px;border-radius:8px;
        box-shadow:0 2px 12px rgba(0,0,0,.1);width:460px}
  h2{margin:0 0 6px;color:#333;text-align:center}
  .sub{text-align:center;color:#888;font-size:13px;margin-bottom:24px}
  .upload-box{border:2px dashed #ddd;border-radius:8px;padding:30px;
              text-align:center;cursor:pointer;margin-bottom:16px;color:#aaa}
  input[type=file]{display:none}
  button{width:100%;padding:10px;background:#2980b9;color:#fff;border:none;
         border-radius:4px;cursor:pointer;font-size:15px}
  button:hover{background:#2471a3}
  .msg{margin-top:16px;padding:12px;border-radius:4px;font-size:14px}
  .ok{background:#eafaf1;color:#1e8449;border:1px solid #2ecc71}
  .err{background:#fdedec;color:#c0392b;border:1px solid #e74c3c}
</style>
</head>
<body>
<div class="card">
  <h2>🖼️ 用户头像上传</h2>
  <p class="sub">仅支持 JPG 格式，文件大小不超过 2MB</p>
  <form method="POST" enctype="multipart/form-data">
    <label for="fileToUpload">
      <div class="upload-box">📁 点击选择文件</div>
    </label>
    <input type="file" name="fileToUpload" id="fileToUpload">
    <button type="submit" name="submit">上 传</button>
  </form>
  <?php if ($msg): ?>
    <div class="msg <?= $msg_type ?>"><?= $msg ?></div>
  <?php endif; ?>
</div>
</body>
</html>
