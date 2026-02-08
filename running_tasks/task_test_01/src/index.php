<?php
// 数据库连接配置
$servername = "db_service";
$username = "root";
$password = getenv('DB_PASS'); // 注意：这里用的是正确的环境变量名
$dbname = "ctf_game";

// 创建连接
$conn = new mysqli($servername, $username, $password, $dbname);

// 检查连接
if ($conn->connect_error) {
    die("连接失败，请联系管理员"); // 生产环境不应该输出详细错误信息
}

// 获取 ID，默认为 1
$id = isset($_GET['id']) ? $_GET['id'] : '1';

?>

<!DOCTYPE html>
<html>
<head>
    <title>用户查询系统</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; }
        .box { border: 1px solid #ccc; padding: 20px; display: inline-block; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .result { color: green; font-weight: bold; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🔍 内部人员查询系统</h1>
        <p>请输入员工 ID 进行查询:</p>
        <form method="GET">
            <input type="text" name="id" value="<?php echo htmlspecialchars($id); ?>">
            <button type="submit">查询</button>
        </form>
        <hr>
        <div class="result">
            <?php
            // --- 漏洞点在这里 ---
            // 我只查询了 'username' 这一列，没有查 'password'
            // 正常用户只能看到名字，看不到密码（Flag）
            $sql = "SELECT username FROM users WHERE id = $id";
            
            // 执行查询
            // 如果你懂 SQL 注入，你可以用 UNION SELECT 把 password 拼接到 username 的位置显示出来
            $result = $conn->query($sql);

            if ($result && $result->num_rows > 0) {
                while($row = $result->fetch_assoc()) {
                    // 只显示用户名
                    echo "Hello, " . $row["username"];
                }
            } else {
                echo "未找到该用户";
            }
            $conn->close();
            ?>
        </div>
    </div>
</body>
</html>