-- 样例：初始化数据库并插入 Flag
CREATE DATABASE IF NOT EXISTS ctf_secret_db;
USE ctf_secret_db;

CREATE TABLE IF NOT EXISTS top_secret_flag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flag_value VARCHAR(255) NOT NULL,
    description VARCHAR(255)
);

-- 这就是选手连上数据库后要找的 Flag
INSERT INTO top_secret_flag (flag_value, description) 
VALUES ('flag{mysql_bRut3_f0rc3_m4ster}', 'Do not leak this!');