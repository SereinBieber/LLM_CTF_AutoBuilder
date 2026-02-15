from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

# 获取 Flag
FLAG = os.getenv("FLAG", "flag{default}")


@app.route('/')
def index():
    name = request.args.get('name', 'Guest')

    # 漏洞点：使用 format 或 + 拼接字符串进入模板渲染
    # Payload: {{ config }} 或 {{ ''.__class__.__mro__[1].__subclasses__() }}
    template = '''
        <div class="center-content">
            <h1>Hello, %s!</h1>
            <p>Welcome to our secure python site.</p>
        </div>
    ''' % name

    return render_template_string(template)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)