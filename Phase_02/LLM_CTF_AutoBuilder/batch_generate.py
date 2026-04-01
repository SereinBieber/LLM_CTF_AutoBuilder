"""
CTF AutoBuilder - 批量生成脚本 V2
直接复用main_pipeline内部逻辑，顺序生成35道题
运行: python batch_generate_v2.py
"""
import os, sys, json, time, random, sqlite3, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import log
from llm_parser.deepseek_handler import DeepSeekHandler
from llm_parser.template_matcher import TemplateMatcher
from llm_parser.vulnerability_generator import VulnerabilityGenerator
from validator.validate_json import load_schema, validate_json, generate_report
from validator.validate_json import validate_code_syntax
import builder.build_env as ctf_builder

TASKS = [
    "给我一道PHP命令注入题，简单难度",
    "给我一道PHP文件包含题，简单难度",
    "给我一道反射型XSS题，简单难度",
    "给我一道SQL注入题，简单难度",
    "给我一道SQL报错注入题，中等难度",
    "给我一道登录绕过题，简单难度",
    "给我一道文件上传题，中等难度",
    "给我一道SSRF题，中等难度",
    "给我一道JWT伪造题，中等难度",
    "给我一道SSTI模板注入题，中等难度",
    "给我一道PHP反序列化题，困难难度",
    "给我一道栈溢出pwn题，简单难度",
    "给我一道堆溢出UAF pwn题，中等难度",
    "给我一道格式化字符串pwn题，中等难度",
    "给我一道整数溢出pwn题，中等难度",
    "给我一道ROP链pwn题，中等难度",
    "给我一道shellcode pwn题，简单难度",
    "给我一道XOR密码题，简单难度",
    "给我一道AES-ECB加密题，中等难度",
    "给我一道RSA LSB Oracle题，困难难度",
    "给我一道Hash长度扩展攻击题，中等难度",
    "给我一道Bash受限Shell逃逸题，简单难度",
    "给我一道Python沙箱逃逸misc题，中等难度",
    "给我一道编程解题PPC数学题，简单难度",
    "给我一道动态LSB图片隐写misc题",
    "给我一道静态LSB图片隐写misc题，简单难度",
    "给我一道字符串校验逆向题，简单难度",
    "给我一道XOR加密逆向题，简单难度",
    "给我一道虚拟机逆向题，困难难度",
    "给我一道反调试逆向题，中等难度",
    "给我一道Redis未授权访问题",
    "给我一道MySQL弱口令题",
    "给我一道PostgreSQL弱口令题",
    "给我一道MongoDB未授权访问题",
]

def _assign_port(tasks_input_dir):
    used = set()
    for f in os.listdir(tasks_input_dir):
        if f.endswith('.json'):
            try:
                with open(os.path.join(tasks_input_dir, f)) as fp:
                    d = json.load(fp)
                p = d.get('architecture', {}).get('runtime_config', {}).get('exposed_port')
                if p: used.add(int(p))
            except: pass
    for _ in range(100):
        p = random.randint(10000, 60000)
        if p not in used:
            return p
    raise RuntimeError("端口分配失败")

def run_batch(repeat=1):
    current_dir     = os.path.dirname(os.path.abspath(__file__))
    tasks_input_dir = os.path.join(current_dir, 'tasks_input')
    tasks_data_dir  = os.path.join(current_dir, 'tasks_data')
    report_dir      = os.path.join(current_dir, 'tasks_report')
    os.makedirs(tasks_input_dir, exist_ok=True)
    os.makedirs(tasks_data_dir,  exist_ok=True)
    os.makedirs(report_dir,      exist_ok=True)

    # 数据库
    db_path = os.path.join(current_dir, 'ctf_tasks.db')
    db = sqlite3.connect(db_path)
    db.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        title TEXT, category TEXT, difficulty TEXT,
        vuln_type TEXT, flag TEXT, port INTEGER,
        status TEXT DEFAULT 'pending',
        instance TEXT, compose TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        description TEXT
    )""")
    db.commit()

    schema    = load_schema(os.path.join(current_dir, 'schema', 'ctf_task_schema.json'))
    handler   = DeepSeekHandler()
    matcher   = TemplateMatcher()
    generator = VulnerabilityGenerator()

    templates_dir = os.path.join(current_dir, 'templates', 'compose_models', 'single-service')
    available_templates = [d for d in os.listdir(templates_dir)
                           if os.path.isdir(os.path.join(templates_dir, d))]

    total_tasks = len(TASKS) * repeat
    print(f"\n🚀 批量生成开始！共 {total_tasks} 道题\n" + "="*60)

    current = 0
    for r in range(repeat):
        for user_input in TASKS:
            current += 1
            print(f"\n[{current}/{total_tasks}] {user_input}")
            t0 = time.time()
            task_id = None

            try:
                # Step 1: 分配端口
                assigned_port = _assign_port(tasks_input_dir)

                # Step 2: 生成蓝图
                enhanced_req = (
                    f"用户核心需求: '{user_input}'。\n"
                    f"architecture.runtime_config.exposed_port 填写整数 {assigned_port}。\n"
                    f"architecture.compose_model_ref 只能从以下列表选一个：{available_templates}。\n"
                    f"vulnerability.flag_value 填写包含 flag{{...}} 的字符串。\n"
                    f"meta.score 必须是整数。"
                )
                task_json = handler.generate_json(enhanced_req)
                if "error" in task_json:
                    raise Exception(f"蓝图生成失败")

                task_json.setdefault('architecture', {}).setdefault('runtime_config', {})
                task_json['architecture']['runtime_config']['exposed_port'] = assigned_port
                task_id = task_json.get("task_id", f"task_{int(time.time())}")
                handler.save_json(task_json)

                # 写入数据库
                meta = task_json.get('meta', {})
                arch = task_json.get('architecture', {})
                vuln = task_json.get('vulnerability', {})
                db.execute("""INSERT OR REPLACE INTO tasks
                    (task_id,title,category,difficulty,flag,port,status,instance,compose,description)
                    VALUES (?,?,?,?,?,?,'pending',?,?,?)""",
                    (task_id, meta.get('name', user_input[:50]),
                     meta.get('category',''), meta.get('difficulty',''),
                     vuln.get('flag_value',''), assigned_port,
                     arch.get('instance_ref',''), arch.get('compose_model_ref',''),
                     meta.get('description','')))
                db.commit()

                # Step 3: 质检
                errors = validate_json(task_json, schema)
                if generate_report(errors)["status"] != "success":
                    raise Exception("质检失败")

                # Step 4: 选模板+生成代码
                template_info = matcher.match_template(task_json)
                if template_info is None:
                    raise Exception("未找到模板")
                output_path = generator.generate_from_task(task_json, template_info)
                if output_path is None:
                    raise Exception("代码生成失败")

                # Step 4.5: 语法校验
                generated_dir = os.path.join(tasks_data_dir, f"{task_id}_generated")
                syntax_result = validate_code_syntax(generated_dir)
                if not syntax_result['passed']:
                    raise Exception("语法校验失败")

                # Step 5: 构建
                success = ctf_builder.build_task(task_id)
                if not success:
                    db.execute("UPDATE tasks SET status='failed' WHERE task_id=?", (task_id,))
                    db.commit()
                    print(f"  ❌ 构建失败 ({round(time.time()-t0)}s)")
                else:
                    db.execute("UPDATE tasks SET status='success',flag=?,port=? WHERE task_id=?",
                               (vuln.get('flag_value',''), assigned_port, task_id))
                    db.commit()
                    print(f"  ✅ 成功 ({round(time.time()-t0)}s) | {vuln.get('flag_value','')}")

            except Exception as e:
                print(f"  ❌ 失败 ({round(time.time()-t0)}s): {e}")
                if task_id:
                    try:
                        db.execute("UPDATE tasks SET status='failed' WHERE task_id=?", (task_id,))
                        db.commit()
                    except: pass

            time.sleep(2)

    print("\n" + "="*60 + "\n📊 批量生成完成！")
    total = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    suc   = db.execute("SELECT COUNT(*) FROM tasks WHERE status='success'").fetchone()[0]
    fail  = db.execute("SELECT COUNT(*) FROM tasks WHERE status='failed'").fetchone()[0]
    rate  = round(suc/total*100, 1) if total > 0 else 0
    print(f"  总计: {total} | 成功: {suc} ✅ | 失败: {fail} ❌ | 成功率: {rate}%")
    db.close()

if __name__ == '__main__':
    REPEAT = 1
    print("="*60)
    print(f"  CTF AutoBuilder - 批量生成脚本 V2")
    print(f"  将生成 {len(TASKS)} × {REPEAT} = {len(TASKS)*REPEAT} 道题")
    print("="*60)
    if input("\n确认开始？(y/n): ").strip().lower() == 'y':
        run_batch(repeat=REPEAT)
    else:
        print("已取消")
