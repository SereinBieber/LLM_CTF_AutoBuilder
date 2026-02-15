-- Type: PostgreSQL Weak Password
-- Difficulty: Easy

CREATE DATABASE ctf_secret_db;
\c ctf_secret_db;

CREATE TABLE flag_table (
    id SERIAL PRIMARY KEY,
    flag_content VARCHAR(255)
);

INSERT INTO flag_table (flag_content) VALUES ('flag{p0stgr3s_brut3_f0rc3}');