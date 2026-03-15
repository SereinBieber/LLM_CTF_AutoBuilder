"""
主生成引擎 - 协调整个代码生成流程
"""
from pathlib import Path
from typing import Dict, Optional, List
import json
import shutil
from datetime import datetime

from .llm_client import LLMClient
from .file_handler import FileHandler


class GenerationEngine:
    """代码生成引擎"""

    def __init__(self, project_root: Path):
        """初始化引擎"""
        self.project_root = project_root
        self.tasks_data = project_root / "tasks_data"
        self.tasks_input = project_root / "tasks_input"
        self.templates_dir = project_root / "templates" / "instances"

        # 确保目录存在
        self.tasks_data.mkdir(exist_ok=True)

        # 初始化组件
        self.llm = LLMClient()
        self.files = FileHandler()

        print(f"🚀 生成引擎初始化完成")
        print(f"  📁 模板目录: {self.templates_dir}")
        print(f"  📁 输出目录: {self.tasks_data}")

    def generate(self, task_config: Dict, template_name: str) -> Optional[Path]:
        """生成漏洞代码"""

        task_id = task_config.get('task_id', 'unknown')
        print(f"\n🔧 正在为任务 {task_id} 生成漏洞代码...")

        # 1. 查找模板
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            print(f"❌ 模板不存在: {template_name}")
            return None

        print(f"  📁 使用模板: {template_name}")

        # 2. 创建任务目录
        task_dir = self.tasks_data / task_id
        if task_dir.exists():
            shutil.rmtree(task_dir)
        task_dir.mkdir()

        # 3. 理解需求
        print(f"  🤔 分析需求...")
        requirements = self.llm.understand_requirements(task_config)

        # 显示需求分析结果
        vuln_type = requirements.get('vulnerability_type', 'unknown')
        language = requirements.get('target_language', 'unknown')
        features = requirements.get('required_features', [])
        print(f"    漏洞类型: {vuln_type}")
        print(f"    目标语言: {language}")
        print(f"    特殊功能: {features}")

        # 4. 收集模板文件
        template_files = self.files.collect_files(template_path)
        print(f"  📦 找到 {len(template_files)} 个模板文件")

        # 5. 处理每个文件
        generated = []
        for template_file in template_files:
            rel_path = template_file.relative_to(template_path)
            dest_file = task_dir / rel_path

            # 判断是否为文本文件
            if self.files.is_text_file(template_file):
                # 读取内容
                content = self.files.read_file(template_file)
                if content is None:
                    # 读取失败，按二进制处理
                    if self.files.copy_binary(template_file, dest_file):
                        generated.append(dest_file)
                        print(f"  📄 复制二进制: {rel_path}")
                    continue

                # 判断是否需要大模型生成
                if self._needs_generation(template_file, requirements):
                    print(f"  ✨ 生成代码: {rel_path}")

                    # 分析代码
                    analysis = self.llm.analyze_code(
                        content,
                        language=template_file.suffix[1:] or 'text'
                    )

                    # 获取flag值
                    flag_value = task_config.get('vulnerability', {}).get(
                        'flag_value', 'flag{default}'
                    )

                    # 生成新代码
                    new_code = self.llm.generate_code(
                        content,
                        analysis,
                        requirements,
                        language=template_file.suffix[1:] or 'text',
                        flag_value=flag_value
                    )

                    # 保存
                    if new_code and self.files.write_file(dest_file, new_code):
                        generated.append(dest_file)
                else:
                    # 直接复制文本
                    if self.files.write_file(dest_file, content):
                        generated.append(dest_file)
                        print(f"  📄 复制: {rel_path}")
            else:
                # 二进制文件直接复制
                if self.files.copy_binary(template_file, dest_file):
                    generated.append(dest_file)
                    print(f"  📄 复制二进制: {rel_path}")

        # 6. 生成flag文件（如果还没有）
        flag_file = task_dir / "flag.txt"
        if not flag_file.exists():
            flag_value = task_config.get('vulnerability', {}).get('flag_value', 'flag{default}')
            self.files.write_file(flag_file, flag_value)
            print(f"  🚩 生成flag: flag.txt")

        # 7. 保存配置
        config_file = task_dir / "task_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(task_config, f, indent=2, ensure_ascii=False)
        print(f"  📄 保存配置: task_config.json")

        print(f"\n✅ 生成完成! 共 {len(generated)} 个文件")
        print(f"  📁 输出目录: {task_dir}")

        return task_dir

    def _needs_generation(self, file_path: Path, requirements: Dict) -> bool:
        """判断是否需要大模型生成"""

        # 代码文件需要生成
        code_extensions = {'.py', '.php', '.c', '.cpp', '.js', '.java', '.sql'}

        if file_path.suffix in code_extensions:
            return True

        # 配置文件如果包含敏感信息，也需要生成
        if file_path.suffix in {'.conf', '.ini', '.json', '.yml', '.yaml'}:
            return True

        # README等说明文件直接复制
        return False