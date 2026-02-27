import json
import os
import jsonschema
from jsonschema import validate


def load_schema(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_json(data, schema):
    errors = []
    try:
        validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        errors.append(str(e))
    return errors


def generate_report(errors):
    if not errors:
        return {
            "status": "success",
            "message": "All checks passed."
        }
    else:
        return {
            "status": "error",
            "errors": errors
        }


def process_files(input_dir, output_dir, schema):
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(input_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 校验
            errors = validate_json(data, schema)
            report = generate_report(errors)

            # 生成报告
            report_filename = f"{os.path.splitext(filename)[0]}_report.json"
            report_filepath = os.path.join(output_dir, report_filename)
            with open(report_filepath, 'w', encoding='utf-8') as report_file:
                json.dump(report, report_file, ensure_ascii=False, indent=4)

            # 在控制台打印一下结果，方便观察
            if report["status"] == "success":
                print(f"✅ [{filename}] 校验通过！格式完美！")
            else:
                print(f"❌ [{filename}] 校验失败！发现了格式错误。")


def main():
    print("==============================================")
    print("🛡️ LLM_CTF_AutoBuilder - 格式校验模块 (Validator)")
    print("==============================================\n")

    # 【核心升级】动态获取项目根目录，再也不怕 E 盘 C 盘的冲突了！
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 当前 validator 目录
    project_root = os.path.dirname(current_dir)  # 上一级的项目根目录

    input_dir = os.path.join(project_root, 'tasks_input')
    output_dir = os.path.join(project_root, 'tasks_report')
    schema_file = os.path.join(project_root, 'schema', 'ctf_task_schema.json')

    # 检查文件夹是否存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 检查 Schema 文件存不存在
    if not os.path.exists(schema_file):
        print(f"🚨 找不到 Schema 规则文件！请确认 {schema_file} 存在。")
        return

    print("🔍 正在扫描 tasks_input 文件夹中彭丽诚生成的 JSON...")
    schema = load_schema(schema_file)
    process_files(input_dir, output_dir, schema)
    print("\n🏁 校验任务结束！详情请查看 tasks_report 文件夹。")


if __name__ == "__main__":
    main()