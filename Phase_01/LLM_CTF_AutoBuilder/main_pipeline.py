import os, json, time, sys

# 1. 导入彭丽诚与杨小琪
from llm_parser.deepseek_handler import DeepSeekHandler
from validator.validate_json import load_schema, validate_json, generate_report

# 2. 导入你写的构建模块
try:
    import builder.build_env as ctf_builder
except ImportError:
    print("🚨 导入失败，请确保 builder 文件夹下有 __init__.py")
    sys.exit(1)


def main():
    print("🏆 LLM_CTF_AutoBuilder - 真·全责解耦版 (Orchestrator V2.0)")
    handler = DeepSeekHandler()
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 提前加载好杨小琪的“基本法”
    schema_path = os.path.join(current_dir, 'schema', 'ctf_task_schema.json')
    if not os.path.exists(schema_path):
        print(f"🚨 致命错误：找不到 Schema 规则文件！路径: {schema_path}")
        return
    schema = load_schema(schema_path)

    while True:
        user_input = input("\n📝 队长指令 (q退出): ").strip()
        if user_input.lower() in ['q', 'quit']: break
        if not user_input: continue

        # 扫描现有模具菜单
        templates_dir = os.path.join(current_dir, 'templates', 'compose_models', 'single-service')
        available_templates = [d for d in os.listdir(templates_dir) if
                               os.path.isdir(os.path.join(templates_dir, d))] if os.path.exists(templates_dir) else []

        # 💡 [修复 2] 彻底对齐最新 Schema 的 Prompt，消灭结构分裂
        enhanced_req = (
            f"用户核心需求: '{user_input}'。\n"
            f"【最高指令】你生成的 JSON 必须严格遵守现有的 Schema 三层架构：\n"
            f"1. 端口配置：必须放在 architecture.runtime_config.exposed_port 中（10000-20000的整数）。\n"
            f"2. 漏洞旗帜：必须放在 vulnerability.flag_value 中（包含 flag{{...}} 的字符串）。\n"
            f"3. 模具选型：必须放在 architecture.compose_model_ref 中，且只能从以下列表选择：{available_templates}。"
        )

        print(f"[Step 1] 彭丽诚正在设计三层架构蓝图...")
        task_json = handler.generate_json(enhanced_req)
        if "error" in task_json: continue

        task_id = task_json.get("task_id", f"task_{int(time.time())}")
        handler.save_json(task_json)

        print("[Step 2] 杨小琪正在执行严格静态质检...")
        # 💡 [修复 1] 动真格的质检拦截
        errors = validate_json(task_json, schema)
        val_result = generate_report(errors)

        report_dir = os.path.join(current_dir, 'tasks_report')
        os.makedirs(report_dir, exist_ok=True)
        pass_report_path = os.path.join(report_dir, f"{task_id}_static_pass.json")

        if val_result["status"] == "success":
            print(f"✅ 质检通过！蓝图完全符合 Schema 规范。")
            with open(pass_report_path, 'w', encoding='utf-8') as f:
                json.dump({"task_id": task_id, "status": "PASS"}, f)
        else:
            print(f"❌ 质检拦截！彭丽诚生成的图纸不合规：")
            for err in val_result.get("errors", []):
                print(f"  - {err}")
            print("⚠️ 流程已阻断，施工队拒绝执行此残次任务。请重新下达指令。")
            continue  # 打回重做，绝不启动 Builder

        print("[Step 3] 施工队 (Builder) 开始按图纸作业...")
        ctf_builder.main()


if __name__ == "__main__":
    main()