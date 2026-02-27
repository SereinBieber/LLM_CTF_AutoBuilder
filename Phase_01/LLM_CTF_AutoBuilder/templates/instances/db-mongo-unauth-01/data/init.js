// Type: MongoDB Unauthorized Access
// Difficulty: Medium
// Description: Find the flag in the secret collection.

db = db.getSiblingDB('ctf_secret_db');

db.createCollection('flag_collection');

db.flag_collection.insert({
    "id": 1,
    "flag": "flag{m0ng0_db_1eak_n0sql}",
    "note": "Top secret!"
});