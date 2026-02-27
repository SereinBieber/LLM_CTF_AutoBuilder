"""
validator/validate_json.py

改进点：
1. 改用 Draft7Validator 迭代模式，一次收集所有错误，不再首错即停
2. 错误信息格式化为人类可读（字段路径 + 原因），方便 AI 修复
"""

import json
import os
import jsonschema
from jsonschema import Draft7Validator


def load_schema(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_json(data: dict, schema: dict) -> list:
    """
    校验 data 是否符合 schema。
    返回错误列表，格式为可读字符串。空列表表示通过。
    """
    validator = Draft7Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(data), key=str):
        # 拼出字段路径，例如 "architecture.runtime_config.exposed_port"
        field_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"字段 [{field_path}]: {error.message}")
    return errors


def generate_report(errors: list) -> dict:
    if not errors:
        return {"status": "success", "message": "All checks passed."}
    return {"status": "error", "errors": errors}


def process_files(input_dir: str, output_dir: str, schema: dict):
    """独立批量校验，供 validator 单独运行时使用"""
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        errors = validate_json(data, schema)
        report = generate_report(errors)

        report_filename = f"{os.path.splitext(filename)[0]}_report.json"
        with open(os.path.join(output_dir, report_filename), 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)

        if report["status"] == "success":
            print(f"✅ [{filename}] 校验通过")
        else:
            print(f"❌ [{filename}] 校验失败，发现 {len(errors)} 个错误：")
            for err in errors:
                print(f"   - {err}")


def main():
    print("🛡️ LLM_CTF_AutoBuilder - 格式校验模块 (Validator)\n")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    input_dir = os.path.join(project_root, 'tasks_input')
    output_dir = os.path.join(project_root, 'tasks_report')
    schema_file = os.path.join(project_root, 'schema', 'ctf_task_schema.json')

    if not os.path.exists(schema_file):
        print(f"🚨 找不到 Schema 文件: {schema_file}")
        return

    schema = load_schema(schema_file)
    process_files(input_dir, output_dir, schema)
    print("\n🏁 校验完毕，详情见 tasks_report 文件夹。")


if __name__ == "__main__":
    main()