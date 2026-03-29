"""
大模型客户端 - V5.1 蓝图架构 + 防白给机制
"""
import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI

class LLMClient:
    def __init__(self, model: str = "deepseek-chat"):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model

    def understand_requirements(self, task_config: Dict) -> Dict[str, Any]:
        meta = task_config.get('meta', {})
        prompt = f"""你是一个CTF题目需求分析专家。请分析以下需求，输出纯JSON。
名称：{meta.get('name', '未知')}
描述：{meta.get('description', '')}
类别：{meta.get('category', 'unknown')}

请输出JSON包含：vulnerability_type, target_language, difficulty_level, required_features, security_level, environment, flag_location
只输出纯JSON，以{{开头，}}结尾。"""
        response = self._call_llm(prompt)
        result = self._extract_json(response)
        return result if result else self._get_default_requirements(task_config)

    def design_blueprint(self, requirements: Dict, env_constraints: Dict = None) -> Dict:
        """
        设计蓝图。如果有环境约束（无数据库），蓝图只需要描述内存逻辑，不需要数据库结构。
        """
        has_database = (env_constraints or {}).get('has_database', True)
        constraint_text = (env_constraints or {}).get('constraint_text', '')

        if not has_database:
            prompt = f"""你是一个高级 CTF 架构师。当前是纯单容器无数据库环境，请为以下需求设计后端逻辑蓝图。

【环境约束】
{constraint_text}

【需求】
{json.dumps(requirements, indent=2, ensure_ascii=False)}

请输出纯JSON：
{{
    "db_schema": {{"table_name": "无", "columns": []}},
    "web_logic": {{
        "vuln_parameter": "漏洞参数名(如cmd, page, url)",
        "flag_location": "env_var或file，说明flag如何获取",
        "logic_description": "用一句话描述漏洞逻辑"
    }}
}}
【重要】只输出纯JSON，不要任何其他文字。"""
        else:
            prompt = f"""你是一个高级 CTF 架构师。请为以下需求设计一套严密的数据库与后端代码对齐蓝图。

【环境约束】
{constraint_text}

【需求】
{json.dumps(requirements, indent=2, ensure_ascii=False)}

请输出纯JSON，包含以下结构（必须保证前后端字段名绝对一致）：
{{
    "db_schema": {{
        "table_name": "数据库表名(如users, products)",
        "columns": ["列名1", "列名2", "存放flag的列名"]
    }},
    "web_logic": {{
        "query_table": "必须与db_schema.table_name完全一致",
        "vuln_parameter": "漏洞参数名(如id)",
        "query_columns": "PHP中SELECT出来的列名，必须存在于db_schema.columns中"
    }}
}}
【重要】只输出纯JSON，不要任何其他文字。"""

        response = self._call_llm(prompt)
        blueprint = self._extract_json(response)
        if not blueprint:
            return {
                "db_schema": {"table_name": "users", "columns": ["id", "username", "password"]},
                "web_logic": {"query_table": "users", "vuln_parameter": "id", "query_columns": ["username", "password"]}
            }
        return blueprint

    def analyze_code(self, code: str, language: str = "unknown") -> Dict[str, Any]:
        prompt = f"分析代码并输出纯JSON。语言:{language}\n代码:\n{code}\n字段: purpose, vulnerability_type, vulnerability_points, key_functions, complexity"
        return self._extract_json(self._call_llm(prompt))

    def generate_code(self, template_code: str, analysis: Dict,
                      requirements: Dict, language: str = "unknown",
                      flag_value: str = "FLAG_PLACEHOLDER", blueprint: Dict = None,
                      filename: str = "unknown", env_constraints: Dict = None) -> str:
        bp_json = json.dumps(blueprint, indent=2, ensure_ascii=False) if blueprint else "无"
        constraint_text = (env_constraints or {}).get('constraint_text', '')

        prompt = f"""你是一个顶级的 CTF 题目生成专家。

【⚡ 最高优先级：物理环境约束（违反即报错）⚡】
{constraint_text if constraint_text else "无特殊约束"}

【当前正在生成的文件】: {filename} (语言类型: {language})

【全局架构蓝图（必须严格遵守）】
{bp_json}

【用户需求】
{json.dumps(requirements, indent=2, ensure_ascii=False)}

【模板代码参考】
{template_code}

【🔥 V5.1 文件物理隔离与游戏规则铁律，违反直接导致系统崩溃 🔥】

1. 文件职责绝对隔离：
   - 你现在正在写的是 `{filename}`！
   - 如果它是 `.sql` 文件：你现在的身份是数据库管理员（DBA）！你的代码里【只能】出现纯 SQL 语句！【绝对禁止】出现任何 `<?php`、HTML 或 PHP 业务逻辑！【必须】在文件最开头加上这两行：`CREATE DATABASE IF NOT EXISTS ctf_db; USE ctf_db;` 然后再写 CREATE TABLE 和 INSERT INTO 语句！
   - 如果它是 `.php`、`.py` 或其它后端文件：你现在的身份是后端开发！专心写网页漏洞逻辑，【绝对禁止】出现 `CREATE DATABASE` 或 `CREATE TABLE` 等建库建表操作！

2. 蓝图强制约束：
   - 无论写哪个文件，表名、列名必须和【全局架构蓝图】里的一模一样！

3. Flag 占位符与数据库连接：
   - 所有预埋 Flag 的地方必须写 `FLAG_PLACEHOLDER`（大写，不带大括号）。SQL 题必须通过 INSERT 预埋在数据库表里。
   - PHP/Python 等后端代码连接数据库时，必须使用环境变量连接（如 `getenv('DB_HOST')` 等）。绝对禁止写 `file_get_contents('/flag')` 作弊！

4. CTF 游戏规则绝对铁律（防白给机制）：
   - 【绝对禁止】在正常的业务展示、HTML 页面、普通 API 响应或注释中直接明文输出 Flag！
   - Flag 的隐藏方式必须严格契合当前【模板代码】的运行环境。例如：带数据库的题目存放在表中，纯后端 Web 题存放在环境变量或隐藏配置文件中，PWN/Reverse/Crypto 类题目按常规逻辑预埋。
   - 选手【必须且只能】通过利用当前【用户需求】中指定的特定漏洞，结合黑客手段才能获取 Flag。正常交互时，连 Flag 的影子都不许看到！

5. Flag路径强制约束：
   - 所有题目flag统一在容器的 /flag 文件，【绝对禁止】使用 /home/ctf/flag.txt 或其他路径
   - pwn/reverse类C代码读flag必须用 fopen("/flag", "r")

6. 运行环境强制约束：
   - crypto/misc类socket题目的server.py【必须只用】sys.stdin和sys.stdout交互，【绝对禁止】自己创建socket或bind端口
   - crypto类server.py只能用Python标准库和pycryptodome，【绝对禁止】import flask
   - pwn类C代码编译注释里必须注明：gcc -o pwn main.c -fno-stack-protector -z execstack -no-pie -w

7. Hash/签名类crypto题必须提供签名查询功能：
   - 服务启动时必须自动输出一个初始消息（如"user=guest"）及其合法签名
   - 或提供命令让选手查询任意消息的签名，否则攻击无从下手

8. 代码质量强制约束：
   - 生成的数组或列表长度严格不超过20项，严禁出现重复元素
   - 所有代码块语法必须完整闭合，括号、引号、缩进全部配对
   - misc/pwn沙箱题【绝对禁止】将Exception等基础异常类覆盖为None，必须保留至少一条可解路径
   
9. 针对 PPC（编程题）的逻辑加固
修复目标：防止 AI 生成只要发固定数字（如 1）就能过关的题目。
强制随机挑战：严禁接收静态或固定的输入作为通关条件。
动态验证逻辑：服务端必须包含一个随机题目生成器（如随机算式），并且必须对用户的输入进行实时的数学或逻辑匹配验证。
状态机完整性：必须在用户通过挑战后才增加计数器，严禁仅凭“收到输入”就增加进度。

10. 针对 Pwn（堆溢出/UAF）的逻辑加固
修复目标：防止 AI 在源码里自编自导自演，自己改指针自己调 win()。
交互式菜单要求：必须生成一个包含 Add, Edit, Delete, Show 等功能的交互式菜单。
严禁自动触发：禁止在 main 函数或任何初始化流程中包含触发漏洞、修改函数指针为 win 或直接调用敏感函数的代码。
漏洞被动化：所有内存破坏行为必须由用户通过菜单功能的特定组合（如“删除后再编辑”）手动触发。

11. 针对 Reverse（虚拟机）的逻辑加固
修复目标：防止用户输入字节码“反客为主”，把逆向题变成编程题。
字节码硬编码：VM 执行的指令序列（Bytecode）必须硬编码在源码的静态数组中，严禁从用户输入中读取并执行指令。
输入隔离：用户的输入（Passphrase）只能作为 VM 执行时的外部数据源进行读取（如通过 IN 指令），用于与硬编码的逻辑进行比对。
12. 针对 Python 沙箱题（pyjail）的逻辑加固
修复目标：保留至少一条逃逸路径，题目必须可解。
【绝对禁止】将 __builtins__ 设为 None 或空字典，这会导致题目完全无解。
必须保留 __builtins__ 为真实的内置模块，只用黑名单字符串列表过滤关键词。
逃逸路径必须存在：选手应能通过 ().__class__.__bases__[0].__subclasses__() 或类似方式找到可执行系统命令的类。

13. 针对 C 语言题目的头文件完整性要求
所有 C 代码必须包含完整的头文件，不得遗漏：
- 使用 fork/waitpid/WEXITSTATUS 必须包含 sys/wait.h
- 使用 ptrace 必须包含 sys/ptrace.h
- 使用 mmap/mprotect 必须包含 sys/mman.h
- 使用 socket/bind/listen 必须包含 sys/socket.h
- 使用 open/read/write 必须包含 fcntl.h 和 unistd.h
【绝对禁止】生成会产生 implicit declaration of function 编译错误的代码。

14. 针对 PHP 反序列化题的逻辑加固
修复目标：不得依赖 phar:// 协议，因为 phar.readonly 默认开启会导致题目失败。
必须使用 __wakeup() 或 __destruct() 魔术方法直接触发漏洞。
flag 存放在容器的 /flag 文件中，在 showFlag() 等方法里用 file_get_contents('/flag') 读取。
选手只需构造正确的序列化字符串通过 GET/POST 参数传入即可触发漏洞获取 flag。

15. 针对 PPC 编程题的时间控制约束
【绝对禁止】在题目循环中使用 time.sleep()，这会导致30秒内无法完成50道题。
必须使用 signal.alarm(30) 设置全局超时，题目循环本身不加任何延时。
必须包含随机运算符（+、-、*），不能只有加法，防止固定答案绕过。
答题成功的判断必须逐题验证，不能仅凭收到输入就算通过。

【输出要求】
直接输出纯代码，不要用 ``` 包裹代码，不要任何解释性文字！
"""
        return self._call_llm(prompt).strip()

    def verify_and_refine(self, code: str, requirements: Dict, filename: str) -> str:
        """
        这就是“质检环节”：把生成的代码再丢给大模型审一遍，防止逻辑白给。
        """
        category = requirements.get('vulnerability_type', '').lower()

        # 这里的 prompt 是专门用来“查错”的
        audit_prompt = f"""你是一个冷酷的 CTF 题目审核员。
    请检查下面这段代码是否违反了【防白给】原则：
    ---
    {code}
    ---
    检查标准：
    1. 绝对不许在 HTML/注释/正常响应里出现 Flag。
    2. PPC 必须有随机题目，不能发固定字符就通关。
    3. Pwn/UAF 绝对不许自动调用 win()。
    4. Reverse/VM 绝对不许运行用户输入的指令。

    如果你发现逻辑有问题，请直接修正并输出【完整的修复后的代码】。
    如果代码很完美，请原样输出。
    只输出代码，不许废话！"""

        # 再次调用大模型进行修正
        refined_code = self._call_llm(audit_prompt).strip()

        # 防止质检函数输出JSON或非代码内容
        # 如果返回的是JSON格式，说明AI误解了任务，直接返回原代码
        if refined_code.startswith('{') or refined_code.startswith('['):
            print(f"  ⚠️ 质检返回了JSON格式，跳过质检，使用原代码")
            return code

        # 如果返回内容比原代码短很多，可能被截断，返回原代码
        if len(refined_code) < len(code) * 0.5:
            print(f"  ⚠️ 质检返回内容过短，跳过质检，使用原代码")
            return code

        return refined_code if refined_code else code

    def _call_llm(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个无情的代码生成机器，只输出代码或JSON，绝对不讲废话，不用代码块包裹。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"  ❌ LLM调用失败: {e}")
            return ""

    def _extract_json(self, text: str) -> Dict:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except:
                pass
        return {}

    def _get_default_requirements(self, task_config: Dict) -> Dict:
        meta = task_config.get('meta', {})
        return {
            "vulnerability_type": meta.get('category', 'sqli'),
            "target_language": "php",
            "difficulty_level": meta.get('difficulty', 'medium')
        }