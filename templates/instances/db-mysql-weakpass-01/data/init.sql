CREATE DATABASE IF NOT EXISTS ctf_secret_db;
USE ctf_secret_db;

CREATE TABLE IF NOT EXISTS top_secret_flag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flag_value VARCHAR(255) NOT NULL,
    description VARCHAR(255)
);

-- FLAG_PLACEHOLDER 由 builder 启动前自动替换
INSERT INTO top_secret_flag (flag_value, description)
VALUES ('FLAG_PLACEHOLDER', 'Do not leak this!');
