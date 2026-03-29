"""
DeepSeek处理器 - 理解自然语言生成JSON
根据项目Schema生成标准格式
"""

import os
import json
import re
from datetime import datetime
from openai import OpenAI

class DeepSeekHandler:
    """DeepSeek处理器：将自然语言转为JSON"""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = "deepseek-chat"

        # 动态扫描 instances 目录，生成模板目录供 AI 选择
        self._instance_catalog = self._scan_instance_catalog()

    def _scan_instance_catalog(self) -> str:
        """动态扫描 templates/instances/ 目录，生成 AI 可读的模板目录字符串"""
        import os as _os
        # 从当前文件位置推导项目根目录
        project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        instances_dir = _os.path.join(project_root, 'templates', 'instances')

        if not _os.path.isdir(instances_dir):
            return "（模板库未找到）"

        lines = []
        for name in sorted(_os.listdir(instances_dir)):
            manifest_path = _os.path.join(instances_dir, name, 'manifest.json')
            if not _os.path.exists(manifest_path):
                continue
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    m = json.load(f)
                category   = m.get('category', '?')
                difficulty = m.get('difficulty', '?')
                desc       = m.get('description', '')[:60]
                lines.append(f"{name:<30} | {category:<7} | {difficulty:<6} | {desc}")
            except Exception:
                continue

        return "\n".join(lines) if lines else "（模板库为空）"

    def generate_json(self, user_requirement: str) -> dict:
        print("🤖 正在调用DeepSeek...")
        try:
            # 构建提示词
            prompt = self._build_prompt(user_requirement)

            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个JSON生成器，根据用户需求输出JSON格式的配置。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )

            # 提取内容
            content = response.choices[0].message.content
            json_str = self._extract_json(content)

            # 解析JSON
            try:
                result = json.loads(json_str)
                # 添加自动生成的字段
                result = self._add_auto_fields(result)
                return result
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                return {"error": "解析失败", "raw_content": content}

        except Exception as e:
            print(f"❌ API调用失败: {type(e).__name__}")
            print(f"错误详情: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"响应内容: {e.response.text}")
            return {"error": str(e)}

    def _build_prompt(self, requirement: str) -> str:
        """构建提示词，让AI同时完成蓝图生成和instance选择"""
        return f"""你是一个CTF题目配置生成专家。请根据用户需求，完成两件事：
1. 生成标准JSON蓝图
2. 从instance模板库中选出最匹配的模板

【用户需求】
{requirement}

【可用的instance模板库】（格式：模板ID | 类别 | 难度 | 描述）
{self._instance_catalog}

【输出要求】
请严格按以下JSON格式输出，只输出JSON不要任何解释：

{{
    "task_id": "task_占位（系统会自动覆盖）",
    "status": "pending",
    "meta": {{
        "name": "根据用户需求起一个合适的题目名称",
        "category": "web/pwn/reverse/crypto/misc 之一",
        "difficulty": "easy/medium/hard 之一",
        "score": 100,
        "description": "题目描述，从用户需求中提取"
    }},
    "architecture": {{
        "base_image_ref": "合适的Docker基础镜像",
        "compose_model_ref": "占位（系统会根据instance_ref自动修正）",
        "instance_ref": "从上方模板库中选择最匹配的模板ID，必须是模板库中存在的ID",
        "runtime_config": {{
            "exposed_port": 8080,
            "env_vars": {{}}
        }}
    }},
    "vulnerability": {{
        "flag_value": "flag{{根据题目类型起一个有意义的flag内容}}",
        "check_script": "/check/script.sh"
    }}
}}

【选择instance_ref的原则】
- 用户说"命令注入/命令执行/RCE" → web-rce-php-01
- 用户说"SQL注入/万能密码/登录绕过" + 提到数据库 → web-sqli-easy-01
- 用户说"登录绕过/万能密码" → web-login-bypass-01
- 用户说"文件包含/LFI" → web-lfi-php-01
- 用户说"文件上传" → web-upload-php-01
- 用户说"XSS/跨站脚本" → web-xss-php-01
- 用户说"SSRF" → web-ssrf-php-01
- 用户说"XXE" → web-xxe-php-01
- 用户说"反序列化" → web-unserialize-php-01
- 用户说"模板注入/SSTI" → web-ssti-py-01
- 用户说"JWT" → web-jwt-py-01
- 用户说"栈溢出/ret2xxx" → pwn-stack-overflow-01
- 用户说"格式化字符串" → pwn-format-string-01
- 用户说"堆溢出/UAF" → pwn-heap-uaf-01
- 用户说"ROP链" → pwn-rop-01
- 用户说"shellcode" → pwn-shellcode-01
- 用户说"整数溢出" → pwn-int-overflow-01
- 用户说"逆向/字符串校验" → reverse-check-str-01
- 用户说"反调试" → reverse-anti-debug-01
- 用户说"虚拟机保护/VM" → reverse-vm-01
- 用户说"XOR加密逆向" → reverse-xor-enc-01
- 用户说"AES/ECB" → crypto-aes-ecb-01
- 用户说"RSA" → crypto-rsa-lsb-01
- 用户说"XOR密码/流密码" → crypto-xor-01
- 用户说"Hash扩展" → crypto-hash-ext-01
- 用户说"Redis未授权" → db-redis-unauth-01
- 用户说"MongoDB未授权" → db-mongo-unauth-01
- 用户说"MySQL弱口令" → db-mysql-weakpass-01
- 用户说"PostgreSQL弱口令" → db-postgres-weakpass-01
- 用户说"隐写/LSB" → misc-stego-lsb-dynamic
- 用户说"Python沙箱/pyjail" → misc-pyjail-01
- 用户说"Bash沙箱/shell限制" → misc-bash-jail-01
- 用户说"编程题/数学题/PPC" → misc-ppc-math-01

instance_ref 必须从模板库中选一个存在的ID，不能自己发明。"""

    def _add_auto_fields(self, result: dict) -> dict:
        """添加自动生成的字段"""
        # 1. ✅ 强制生成新的task_id（覆盖AI返回的）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result['task_id'] = f"task_{timestamp}"

        # 2. 确保status是pending
        result['status'] = "pending"

        # 3. 确保所有必要字段存在
        if 'meta' not in result:
            result['meta'] = {}

        # 4. 确保meta包含description（如果用户需求有描述）
        if 'description' not in result['meta']:
            # 如果没有description，可以用默认值
            result['meta']['description'] = "无详细描述"

        if 'architecture' not in result:
            result['architecture'] = {}
        if 'vulnerability' not in result:
            result['vulnerability'] = {}

        return result

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        # 方法1：找```json代码块
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 方法2：找{}之间的内容
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            return text[start:end].strip()

        # 方法3：返回原文本
        return text.strip()

    def save_json(self, data: dict, filename: str = None):
        """保存JSON到tasks_input文件夹"""
        import os

        os.makedirs("tasks_input", exist_ok=True)

        if filename is None:
            # 使用task_id作为文件名
            task_id = data.get('task_id', 'unknown')
            filename = f"{task_id}.json"

        filepath = os.path.join("tasks_input", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON已保存到: {filepath}")
        return filepath