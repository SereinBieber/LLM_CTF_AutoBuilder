from flask import Flask, request, jsonify
import jwt
import os
import datetime

app = Flask(__name__)

# 弱密钥，可被 hashcat 爆破
SECRET_KEY = "123456"
FLAG = os.getenv("FLAG", "FLAG_PLACEHOLDER")


@app.route('/')
def home():
    return """
    <h2>JWT 练习靶场</h2>
    <p>接口说明：</p>
    <ul>
      <li>GET /login — 获取普通用户 token</li>
      <li>GET /admin?token=xxx — 用 token 访问管理员接口</li>
    </ul>
    <p>提示：token 使用了某个简单的密钥签名……</p>
    """


@app.route('/login')
def login():
    token = jwt.encode(
        {
            'user': 'guest',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        },
        SECRET_KEY,
        algorithm='HS256'
    )
    return jsonify({'token': token, 'hint': '你拿到了 guest 的 token，admin 才能看 flag'})


@app.route('/admin')
def admin():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': '需要提供 token 参数'}), 401

    try:
        # 漏洞点：弱密钥 "123456"，可用 hashcat/jwt_tool 爆破
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        if decoded.get('user') == 'admin':
            return jsonify({'message': '欢迎管理员！', 'flag': FLAG})
        else:
            return jsonify({'message': f"你好 {decoded.get('user')}，但你不是 admin"}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'token 已过期'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 403


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
