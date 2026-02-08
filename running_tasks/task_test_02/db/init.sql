CREATE TABLE users (
    id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) NOT NULL,
    password VARCHAR(50) NOT NULL
);

INSERT INTO users (username, password) VALUES ('admin', 'flag{test_flag_12345}');
INSERT INTO users (username, password) VALUES ('guest', '123456');
INSERT INTO users (username, password) VALUES ('zhangsan', 'pwd789');