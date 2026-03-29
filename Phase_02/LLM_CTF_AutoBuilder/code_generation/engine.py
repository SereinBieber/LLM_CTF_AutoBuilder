"""
主生成引擎 - V5.0 蓝图调度与防幻觉清洗版
"""
from pathlib import Path
from typing import Dict, Optional, List
import json
import shutil
import re

from .llm_client import LLMClient
from .file_handler import FileHandler

class GenerationEngine:
    """代码生成引擎"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tasks_data = project_root / "tasks_data"
        self.tasks_input = project_root / "tasks_input"
        self.templates_dir = project_root / "templates" / "instances"
        self.tasks_data.mkdir(exist_ok=True)
        self.llm = LLMClient()
        self.files = FileHandler()

    def _derive_env_constraints(self, template_path: Path) -> Dict:
        """
        根据模板的物理结构推导环境约束，传给 LLM 防止幻觉。
        这是 System Prompt Wrapper 的核心数据来源。
        """
        has_db_dir      = (template_path / 'db').is_dir()
        has_dockerfile  = (template_path / 'Dockerfile').exists()
        has_src_dir     = (template_path / 'src').is_dir()

        # 判断语言
        php_files = list(template_path.rglob('*.php'))
        py_files  = list(template_path.rglob('*.py'))
        c_files   = list(template_path.rglob('*.c'))
        if php_files:
            lang = 'php'
        elif py_files:
            lang = 'python'
        elif c_files:
            lang = 'c'
        else:
            lang = 'unknown'

        # 读取 manifest 获取 compose_model
        manifest_path = template_path / 'manifest.json'
        compose_model = ''
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    m = json.load(f)
                compose_model = m.get('requirements', {}).get('compose_model', '')
            except Exception:
                pass

        # 判断是否有数据库（db目录 或 compose_model 含 mysql/mongo/postgres/redis）
        db_keywords = ['mysql', 'mongo', 'postgres', 'redis', 'db']
        has_database = has_db_dir or any(k in compose_model for k in db_keywords)

        # 构造自然语言约束描述
        constraints = []
        if not has_database:
            constraints.append("【数据库约束】当前环境是纯单容器，不包含任何数据库服务。绝对禁止编写任何 new mysqli/PDO/pymysql/SQLAlchemy 等数据库连接代码！所有数据必须硬编码在变量中或从环境变量读取，逻辑必须在内存闭环！")
        else:
            constraints.append(f"【数据库约束】当前环境包含数据库服务（compose_model: {compose_model}）。数据库连接必须使用环境变量：DB_HOST/DB_USER/DB_PASS/DB_NAME，禁止硬编码 localhost 或固定密码。")

        if lang == 'php':
            constraints.append("【语言约束】当前模板语言为 PHP，必须生成纯 PHP 代码，禁止在 PHP 文件中混入 Python/Node.js 语法。")
        elif lang == 'python':
            constraints.append("【语言约束】当前模板语言为 Python/Flask，必须生成符合 Flask 框架的 Python 代码。")
        elif lang == 'c':
            constraints.append("【语言约束】当前模板语言为 C，必须生成标准 C 代码，只能使用标准库函数。")

        if not has_dockerfile:
            constraints.append("【镜像约束】当前模板使用项目统一基础镜像，禁止在代码中安装额外依赖包（如 pip install / apt-get）。")

        return {
            'has_database':    has_database,
            'has_dockerfile':  has_dockerfile,
            'primary_language': lang,
            'compose_model':   compose_model,
            'constraint_text': "\n".join(constraints),
        }

    def generate(self, task_config: Dict, template_name: str) -> Optional[Path]:
        task_id = task_config.get('task_id', 'unknown')
        print(f"\n🔧 正在为任务 {task_id} 生成漏洞代码...")

        template_path = self.templates_dir / template_name
        if not template_path.exists():
            print(f"❌ 模板不存在: {template_name}")
            return None

        # 🔍 推导物理环境约束（System Prompt Wrapper 的数据来源）
        env_constraints = self._derive_env_constraints(template_path)
        print(f"  🔒 环境约束已推导: 语言={env_constraints['primary_language']} | "
              f"数据库={'有' if env_constraints['has_database'] else '无'} | "
              f"compose={env_constraints['compose_model']}")

        task_dir = self.tasks_data / f"{task_id}_generated"
        if task_dir.exists():
            shutil.rmtree(task_dir)
        task_dir.mkdir()

        print(f"  🤔 分析需求...")
        requirements = self.llm.understand_requirements(task_config)

        print(f"  🎨 正在设计全栈联调蓝图...")
        blueprint = self.llm.design_blueprint(requirements, env_constraints)
        print(f"    ✅ 敲定表名: {blueprint.get('db_schema', {}).get('table_name', 'N/A（无数据库）')}")

        template_files = self.files.collect_files(template_path)
        generated = []

        for template_file in template_files:
            rel_path = template_file.relative_to(template_path)
            dest_file = task_dir / rel_path

            if self.files.is_text_file(template_file):
                content_text = self.files.read_file(template_file)
                if content_text is None:
                    if self.files.copy_binary(template_file, dest_file):
                        generated.append(dest_file)
                    continue

                if self._needs_generation(template_file, requirements):
                    print(f"  ✨ 根据蓝图生成代码: {rel_path}...")
                    analysis = self.llm.analyze_code(content_text, language=template_file.suffix[1:] or 'text')
                    flag_value = task_config.get('vulnerability', {}).get('flag_value', 'FLAG_PLACEHOLDER')

                    new_code = self.llm.generate_code(
                        content_text,
                        analysis,
                        requirements,
                        language=template_file.suffix[1:] or 'text',
                        flag_value=flag_value,
                        blueprint=blueprint,
                        filename=template_file.name,
                        env_constraints=env_constraints,  # 传入物理约束
                    )

                    # 🛡️ V5.0 终极拦截器：防止 SQL 文件混入 PHP 逻辑
                    if template_file.suffix == '.sql' and '<?php' in new_code.lower():
                        print(f"  🚨 拦截到 AI 幻觉！正在从 {template_file.name} 中强行清洗 PHP 标签...")
                        new_code = re.sub(r'<\?php.*?\?>', '-- 拦截的幻觉 PHP 代码已被剔除', new_code, flags=re.DOTALL)
                        new_code = new_code.replace('<?php', '-- 拦截到 <?php').replace('?>', '-- 拦截到 ?>')

                    # 🛡️ V5.1 拦截器：防止 misc/crypto 的 Python 文件使用 Flask
                    if (template_file.suffix == '.py' and
                            env_constraints.get('primary_language') == 'python' and
                            not env_constraints.get('has_database', False) and
                            'from flask' in new_code.lower()):
                        print(f"  🚨 拦截到 Flask 幻觉！server.py 不能使用 Flask，强制重新生成...")
                        # 重新生成，在prompt里额外强调
                        extra_hint = "【紧急修正】你刚才生成的代码错误地使用了Flask！这是一个socat+python环境，绝对不能import flask！必须只用sys.stdin/stdout！"
                        new_code = self.llm.generate_code(
                            content_text, analysis, requirements,
                            language=template_file.suffix[1:] or 'text',
                            flag_value=flag_value, blueprint=blueprint,
                            filename=template_file.name,
                            env_constraints={**env_constraints,
                                           'constraint_text': extra_hint + '\n' + env_constraints.get('constraint_text', '')}
                        )

                    # 🛡️ V5.3 拦截器：防止pyjail黑名单过于严格导致无解
                    if (template_file.suffix == '.py' and
                            'jail' in (requirements.get('vulnerability_type', '') + template_file.name).lower()):
                        import re as _re
                        # 统计黑名单长度
                        blacklist_match = _re.search(r'BLACKLIST\s*=\s*\[([^\]]+)\]', new_code)
                        if blacklist_match:
                            blacklist_items = blacklist_match.group(1).count("'") // 2
                            if blacklist_items > 15:
                                print(f"  🚨 拦截到过度限制的pyjail黑名单（{blacklist_items}项），强制重新生成...")
                                extra_hint = "【紧急修正】你刚才生成的BLACKLIST有超过15个元素，而且包含了括号、引号、下划线等基础符号，导致题目完全无解！必须保持BLACKLIST在15个以内，只过滤import/eval/exec等危险函数名，绝对不能过滤括号()、方括号[]、点号.、引号、下划线_等基础Python语法符号！"
                                new_code = self.llm.generate_code(
                                    content_text, analysis, requirements,
                                    language=template_file.suffix[1:] or 'text',
                                    flag_value=flag_value, blueprint=blueprint,
                                    filename=template_file.name,
                                    env_constraints={**env_constraints,
                                                   'constraint_text': extra_hint + '\n' + env_constraints.get('constraint_text', '')}
                                )
                        # 检查__builtins__是否被设为None或空字典
                        if "'__builtins__': None" in new_code or '"__builtins__": None' in new_code or                            "'__builtins__': {}" in new_code or '"__builtins__": {}' in new_code:
                            print(f"  🚨 拦截到__builtins__=None，强制重新生成...")
                            extra_hint2 = "【紧急修正】你刚才把__builtins__设为None或空字典{}，这让题目完全无解！必须用真实的__builtins__，即exec(line, {'__builtins__': __builtins__}, {})，只用BLACKLIST字符串列表过滤！"
                            new_code = self.llm.generate_code(
                                content_text, analysis, requirements,
                                language=template_file.suffix[1:] or 'text',
                                flag_value=flag_value, blueprint=blueprint,
                                filename=template_file.name,
                                env_constraints={**env_constraints,
                                               'constraint_text': extra_hint2 + '\n' + env_constraints.get('constraint_text', '')}
                            )

                    # 额外保险：清除可能残留的 Markdown 代码块标记
                    new_code = new_code.replace('```sql\n', '').replace('```php\n', '').replace('```\n', '').replace('```', '')

                    if new_code and self.files.write_file(dest_file, new_code):
                        generated.append(dest_file)
                else:
                    if self.files.write_file(dest_file, content_text):
                        generated.append(dest_file)
            else:
                if self.files.copy_binary(template_file, dest_file):
                        generated.append(dest_file)

        flag_file = task_dir / "flag.txt"
        if not flag_file.exists():
            flag_value = task_config.get('vulnerability', {}).get('flag_value', 'FLAG_PLACEHOLDER')
            self.files.write_file(flag_file, flag_value)

        config_file = task_dir / "task_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(task_config, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 生成完成! 蓝图与物理隔离已生效！")
        return task_dir

    def _needs_generation(self, file_path: Path, requirements: Dict) -> bool:
        code_extensions = {'.py', '.php', '.c', '.cpp', '.js', '.java', '.sql'}
        if file_path.suffix in code_extensions:
            return True
        if file_path.suffix in {'.conf', '.ini', '.json', '.yml', '.yaml'}:
            return True
        return False