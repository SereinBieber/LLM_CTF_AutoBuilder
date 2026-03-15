CREATE TABLE flag_table (
    id SERIAL PRIMARY KEY,
    flag_content VARCHAR(255)
);

-- FLAG_PLACEHOLDER 由 builder 启动前自动替换
INSERT INTO flag_table (flag_content) VALUES ('FLAG_PLACEHOLDER');
