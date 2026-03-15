// MongoDB 未授权访问 - 初始化数据
db = db.getSiblingDB('ctf_secret_db');
db.createCollection('flag_collection');

// FLAG_PLACEHOLDER 由 builder 启动前自动替换
db.flag_collection.insert({
    "id": 1,
    "flag": "FLAG_PLACEHOLDER",
    "note": "Top secret!"
});
