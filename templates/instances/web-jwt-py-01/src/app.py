from flask import Flask, request, jsonify
import jwt  # 需要在 requirements.txt 里加 pyjwt
import os
import datetime

app = Flask(__name__)
# 弱密钥，容易被爆破
SECRET_KEY = "123456"


@app.route('/')
def home():
    return "Welcome to JWT Lab. Go to /login to get a token, and /admin to get the flag."


@app.route('/login')
def login():
    # 发放一个普通用户的 Token
    token = jwt.encode({
        'user': 'guest',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, SECRET_KEY, algorithm='HS256')
    return jsonify({'token': token})


@app.route('/admin')
def admin():
    token = request.args.get('token')
    if not token:
        return "Missing token", 401

    try:
        # 漏洞点：CTF常见考点是 'None' 算法攻击，或者爆破 '123456' 弱密钥
        # 这里演示弱密钥，攻击者可以用工具生成一个 user=admin 的 token 签名
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        if decoded.get('user') == 'admin':
            return f"Success! Flag is: {os.getenv('FLAG', 'flag{test}')}"
        else:
            return "You are not admin. You are: " + decoded.get('user')

    except Exception as e:
        return str(e), 403


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)