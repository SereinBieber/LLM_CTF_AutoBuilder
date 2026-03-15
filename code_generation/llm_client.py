"""
大模型客户端 - 提示词直接写在代码中
"""
import os
import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI


class LLMClient:
    """大模型客户端（提示词内嵌）"""

    def __init__(self, model: str = "deepseek-chat"):
        """初始化客户端"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model

    def understand_requirements(self, task_config: Dict) -> Dict[str, Any]:
        """理解需求 - 提示词直接写在代码中"""
        meta = task_config.get('meta', {})

        # ===== 提示词直接在这里 =====
        prompt = f"""你是一个CTF题目需求分析专家。请分析以下题目需求，输出JSON格式的参数。

【题目信息】
名称：{meta.get('name', '未知')}
描述：{meta.get('description', '')}
难度：{meta.get('difficulty', 'medium')}
类别：{meta.get('category', 'unknown')}

请输出JSON，包含以下字段：
- vulnerability_type: 漏洞类型 (sqli/xss/rce/stack/aes/jail等)
- target_language: 目标编程语言 (python/php/c/任意)
- difficulty_level: 难度等级 (easy/medium/hard)
- required_features: 需要的特殊功能列表 (可选: backdoor, anti_debug, network, database)
- security_level: 安全机制强度 (none/low/medium/high)
- environment: 环境要求 (docker/static/network)
- flag_location: flag存放位置 (file/variable/db)

【重要】
只输出纯JSON，不要任何其他文字，不要用```json```包裹。
直接以 {{ 开头，以 }} 结尾。

输出格式示例：
{{"vulnerability_type":"sqli","target_language":"php","difficulty_level":"medium","required_features":["database"],"security_level":"low","environment":"docker","flag_location":"db"}}
"""

        response = self._call_llm(prompt)

        if not response:
            print("  ⚠️ 大模型返回空，使用默认值")
            return self._get_default_requirements(task_config)

        # 提取JSON
        result = self._extract_json(response)

        if not result:
            print("  ⚠️ JSON解析失败，使用默认值")
            return self._get_default_requirements(task_config)

        return result

    def analyze_code(self, code: str, language: str = "unknown") -> Dict[str, Any]:
        """分析代码 - 提示词直接写在代码中"""

        # ===== 提示词直接在这里 =====
        prompt = f"""你是一个CTF代码分析专家。请分析以下代码，理解其结构和漏洞。

【代码内容】（{language}）
        {code}

        请输出JSON，包含以下字段：
        - purpose: 代码的主要功能
        - vulnerability_type: 漏洞类型
        - vulnerability_points: 漏洞点列表，每个包含 line 和 description
        - key_functions: 关键函数列表
        - security_mechanisms: 已有的安全机制
        - dependencies: 代码依赖
        - complexity: 复杂度 (1-10)
        - flag_location: flag的位置

        【重要】
        只输出纯JSON，不要任何其他文字。

        输出格式示例：
        {{"purpose":"登录验证程序","vulnerability_type":"sqli","vulnerability_points":[{{"line":15,"description":"直接拼接SQL"}}]}}
        """

        response = self._call_llm(prompt)

        if not response:
            return {}

        return self._extract_json(response)

    def generate_code(self, template_code: str, analysis: Dict,
                      requirements: Dict, language: str = "unknown",
                      flag_value: str = "flag{default}") -> str:
        """生成代码 - 提示词直接写在代码中"""

        # ===== 提示词直接在这里 =====
        prompt = f"""你是一个CTF题目生成专家。请根据模板代码和用户需求，生成新的漏洞代码。

        【模板代码】（{language}）
        {template_code}

        【模板分析】
        {json.dumps(analysis, indent=2, ensure_ascii=False)}

        【用户需求】
        {json.dumps(requirements, indent=2, ensure_ascii=False)}

        【生成要求】
        1. 保持核心漏洞类型，根据难度调整复杂度
        2. 根据需求添加/删除功能
        3. 插入flag，flag值为：{flag_value}
        4. 添加注释说明漏洞点

        【重要】
        直接输出纯代码，不要用```包裹，不要任何解释文字。
        """

        response = self._call_llm(prompt)
        return response.strip()

    def _call_llm(self, prompt: str) -> str:
        """调用大模型"""
        try:
            print("  🤖 正在调用DeepSeek...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个CTF题目生成专家，只输出要求的格式，不要额外解释。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            return content if content else ""

        except Exception as e:
            print(f"  ❌ LLM调用失败: {type(e).__name__}: {e}")
            return ""

    def _extract_json(self, text: str) -> Dict:
        """从响应中提取JSON"""
        if not text:
            return {}

        # 直接找第一个{和最后一个}
        start = text.find('{')
        end = text.rfind('}') + 1

        if start != -1 and end > start:
            json_str = text[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 尝试修复常见问题
                try:
                    # 替换单引号
                    json_str = json_str.replace("'", '"')
                    return json.loads(json_str)
                except:
                    pass

        return {}

    def _get_default_requirements(self, task_config: Dict) -> Dict:
        """获取默认需求参数"""
        meta = task_config.get('meta', {})
        return {
            "vulnerability_type": meta.get('category', 'unknown'),
            "target_language": "unknown",
            "difficulty_level": meta.get('difficulty', 'medium'),
            "required_features": [],
            "security_level": "medium",
            "environment": "docker",
            "flag_location": "file",
            "special_requirements": ""
        }