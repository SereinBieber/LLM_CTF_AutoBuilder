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
        """构建提示词"""
        return f"""请根据用户的需求，生成一个JSON格式的CTF配置。

用户需求：
{requirement}

你必须严格按照以下JSON Schema生成配置：

{{
    "task_id": "自动生成的任务ID（格式：task_年月日_时分秒）",
    "status": "pending（固定值）",
    
    "meta": {{
        "name": "题目名称",
        "category": "题目类别（web/pwn/reverse/crypto/misc/forensics）",
        "difficulty": "难度（easy/medium/hard/expert）",
        "score": "分数（10-1000之间的整数）",
        "description": "题目详细描述（从用户需求中提取）"
    }},

    "architecture": {{
        "base_image_ref": "基础镜像引用（如ubuntu:20.04, mysql:8.0等）",
        "compose_model_ref": "compose模板名称（根据题目类型自动选择）",
        "instance_ref": "实例模板名称（根据题目类型自动选择）",
        "runtime_config": {{
            "exposed_port": "对外暴露的端口号",
            "env_vars": {{}}
        }}
    }},

    "vulnerability": {{
        "flag_value": "flag格式（如flag{{...}}）",
        "check_script": "/check/script.sh"
    }}
}}

具体要求：
1. task_id 格式：task_年月日_时分秒（如 task_20250213_143022）
2. status 固定为 "pending"
3. category 必须是：web, pwn, reverse, crypto, misc, forensics 之一
4. difficulty 必须是：easy, medium, hard, expert 之一
5. score 在10-1000之间
6. description 从用户需求中提取详细描述
7. base_image_ref 使用合理的Docker镜像名
8. compose_model_ref 和 instance_ref 根据题目类型生成（如 sqli_basic, xss_basic 等）
9. flag_value 格式为 flag{{...}}

请只输出JSON，不要额外解释："""

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