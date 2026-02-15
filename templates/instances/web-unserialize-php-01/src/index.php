<?php
// Type: Unserialize
// Difficulty: Hard

class User {
    public $username;
    public $isAdmin = false;

    public function __wakeup() {
        if ($this->isAdmin) {
            echo "Welcome Admin! Flag is: " . getenv('FLAG');
        } else {
            echo "Welcome User.";
        }
    }
}

$data = $_GET['data'];

if (isset($data)) {
    // 漏洞点：直接反序列化用户输入
    // Payload: O:4:"User":2:{s:8:"username";s:5:"admin";s:7:"isAdmin";b:1;}
    unserialize($data);
} else {
    echo "<h1>User Login System</h1>";
    echo "";
}
?>