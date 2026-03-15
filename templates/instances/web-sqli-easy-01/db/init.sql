CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(30) NOT NULL,
    password VARCHAR(100) NOT NULL
);

INSERT INTO users (username, password) VALUES ('admin', 'FLAG_PLACEHOLDER');
INSERT INTO users (username, password) VALUES ('guest', '123456');
INSERT INTO users (username, password) VALUES ('zhangsan', 'pwd_xyz789');
