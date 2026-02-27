CREATE TABLE admins (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(100) NOT NULL,
    flag VARCHAR(100) NOT NULL
);

-- FLAG_PLACEHOLDER 由 builder 启动前自动替换
INSERT INTO admins (username, password, flag)
    VALUES ('administrator', 'Sup3rS3cr3tP@ss!', 'FLAG_PLACEHOLDER');
