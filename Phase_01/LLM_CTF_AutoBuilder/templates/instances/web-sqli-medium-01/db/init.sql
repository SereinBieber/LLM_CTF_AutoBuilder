CREATE TABLE products (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50) NOT NULL
);

CREATE TABLE secret (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    val VARCHAR(100) NOT NULL
);

INSERT INTO products (name, price, category) VALUES ('商品A', 9.90, 'daily');
INSERT INTO products (name, price, category) VALUES ('商品B', 19.90, 'daily');
INSERT INTO products (name, price, category) VALUES ('商品C', 99.00, 'premium');

-- FLAG_PLACEHOLDER 由 builder 启动前自动替换
INSERT INTO secret (val) VALUES ('FLAG_PLACEHOLDER');
