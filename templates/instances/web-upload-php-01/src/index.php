<?php
// Type: File Upload
// Difficulty: Hard
// Description: Please upload your profile picture.

$target_dir = "uploads/";
// 自动创建上传目录
if (!file_exists($target_dir)) {
    mkdir($target_dir, 0777, true);
}

if(isset($_POST["submit"])) {
    $target_file = $target_dir . basename($_FILES["fileToUpload"]["name"]);
    $uploadOk = 1;

    // 漏洞点：只检查了 MIME 类型，没有检查文件后缀名
    // 攻击者可以上传 .php 文件，但 Content-Type 伪造成 image/jpeg
    if($_FILES["fileToUpload"]["type"] != "image/jpeg") {
        echo "Sorry, only JPG files are allowed.";
        $uploadOk = 0;
    }

    if ($uploadOk == 1) {
        if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
            echo "The file ". htmlspecialchars( basename( $_FILES["fileToUpload"]["name"])). " has been uploaded to: " . $target_file;
        } else {
            echo "Sorry, there was an error uploading your file.";
        }
    }
}
?>

<!DOCTYPE html>
<html>
<body>
    <form method="post" enctype="multipart/form-data">
        Select image to upload:
        <input type="file" name="fileToUpload" id="fileToUpload">
        <input type="submit" value="Upload Image" name="submit">
    </form>
    </body>
</html>