"""
main_pipeline.py
总指挥 —— 串联所有模块的主流程

版本 V4.0 改动：
1. 彩色日志，绿色=成功 / 黄色=警告 / 红色=真正出错
2. 端口由服务端真随机生成，AI 给的端口直接被覆盖
3. 静态检测失败支持 AI 自动修复，最多重试3次（杨小琪模块）
4. 静态检测通过后自动匹配模板并生成漏洞代码（彭丽诚模块）
5. builder 按 task_id 精准构建
"""

import os
import json
import random
import time

from core.logger import log
from llm_parser.deepseek_handler import DeepSeekHandler
from llm_parser.template_matcher import TemplateMatcher
from llm_parser.vulnerability_generator import VulnerabilityGenerator
from validator.validate_json import load_schema, validate_json, generate_report, call_deepseek
import builder.build_env as ctf_builder


# ── 端口管理 ──────────────────────────────────────────────────────────────────
PORT_MIN = 10000
PORT_MAX = 20000


def _get_used_ports(tasks_input_dir: str) -> set:
    """扫描 tasks_input 里所有 JSON，收集已被占用的端口号"""
    used = set()
    if not os.path.isdir(tasks_input_dir):
        return used
    for fname in os.listdir(tasks_input_dir):
        if not fname.endswith('.json'):
            continue
        try:
            with open(os.path.join(tasks_input_dir, fname), 'r', encoding='utf-8') as f:
                data = json.load(f)
            port = data.get('architecture', {}).get('runtime_config', {}).get('exposed_port')
            if isinstance(port, int):
                used.add(port)
        except Exception:
            pass
    return used


def _assign_port(tasks_input_dir: str) -> int:
    """随机分配一个未被占用的端口"""
    used = _get_used_ports(tasks_input_dir)
    candidates = list(range(PORT_MIN, PORT_MAX + 1))
    random.shuffle(candidates)
    for port in candidates:
        if port not in used:
            return port
    raise RuntimeError(f"端口池 {PORT_MIN}-{PORT_MAX} 已全部占用！")


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n🏆  LLM_CTF_AutoBuilder  Pipeline V4.0\n")

    current_dir     = os.path.dirname(os.path.abspath(__file__))
    tasks_input_dir = os.path.join(current_dir, 'tasks_input')
    tasks_data_dir  = os.path.join(current_dir, 'tasks_data')
    report_dir      = os.path.join(current_dir, 'tasks_report')
    security_dir    = os.path.join(current_dir, 'security_reports')

    os.makedirs(report_dir,  exist_ok=True)
    os.makedirs(security_dir, exist_ok=True)
    os.makedirs(tasks_data_dir, exist_ok=True)

    # 加载 Schema
    schema_path = os.path.join(current_dir, 'schema', 'ctf_task_schema.json')
    if not os.path.exists(schema_path):
        log.error(f"找不到 Schema 文件: {schema_path}")
        return
    schema = load_schema(schema_path)

    # 扫描可用 compose 模板
    templates_dir = os.path.join(current_dir, 'templates', 'compose_models', 'single-service')
    available_templates = (
        [d for d in os.listdir(templates_dir)
         if os.path.isdir(os.path.join(templates_dir, d))]
        if os.path.isdir(templates_dir) else []
    )

    # 初始化各模块
    handler   = DeepSeekHandler()
    matcher   = TemplateMatcher()
    generator = VulnerabilityGenerator()

    while True:
        user_input = input("\n📝  请输入你想要的 CTF 题目类型  (q 退出): ").strip()
        if user_input.lower() in ['q', 'quit']:
            break
        if not user_input:
            continue

        # ── Step 1: 服务端分配端口 ────────────────────────────────────────
        log.step(1, "服务端分配端口（真随机，不经过 AI）")
        try:
            assigned_port = _assign_port(tasks_input_dir)
        except RuntimeError as e:
            log.error(str(e))
            continue
        log.success(f"端口已分配: {assigned_port}")

        # ── Step 2: AI 生成 JSON 蓝图 ────────────────────────────────────
        log.step(2, "AI 正在生成题目蓝图...")
        enhanced_req = (
            f"用户核心需求: '{user_input}'。\n"
            f"【最高指令】你生成的 JSON 必须严格遵守 Schema 三层架构：\n"
            f"1. architecture.runtime_config.exposed_port 填写整数 {assigned_port}（已由系统指定，不得修改）。\n"
            f"2. vulnerability.flag_value 填写包含 flag{{...}} 的字符串。\n"
            f"3. architecture.compose_model_ref 只能从以下列表选一个：{available_templates}。\n"
            f"4. architecture.instance_ref 填写与漏洞类型最匹配的 instance 名（如 web-sqli-easy-01）。\n"
            f"5. meta.score 必须是整数。"
        )

        task_json = handler.generate_json(enhanced_req)
        if "error" in task_json:
            log.error(f"AI 生成失败: {task_json['error']}")
            continue

        # 强制覆盖端口
        task_json.setdefault('architecture', {}).setdefault('runtime_config', {})
        task_json['architecture']['runtime_config']['exposed_port'] = assigned_port

        task_id = task_json.get("task_id", f"task_{int(time.time())}")
        handler.save_json(task_json)
        log.success(f"蓝图已生成并保存，task_id: {task_id}，端口已锁定为 {assigned_port}")

        # ── Step 3: 静态质检 + AI 自动修复 ──────────────────────────────
        log.step(3, "静态质检（Schema 校验）")
        errors     = validate_json(task_json, schema)
        val_result = generate_report(errors)
        MAX_FIX_RETRIES = 3

        if val_result["status"] != "success":
            log.error("静态质检未通过，发现以下问题：")
            for err in val_result.get("errors", []):
                log.error(f"  · {err}")

            # AI 自动修复，最多3次
            input_filepath = os.path.join(tasks_input_dir, f"{task_id}.json")
            fixed = False

            for attempt in range(1, MAX_FIX_RETRIES + 1):
                log.warning(f"尝试 AI 自动修复（第 {attempt}/{MAX_FIX_RETRIES} 次）...")
                try:
                    modified, _ = call_deepseek(
                        input_filepath, input_filepath,
                        val_result.get("errors", []), schema
                    )
                    if modified is None:
                        log.error("AI 修复返回空，停止修复")
                        break

                    new_errors = validate_json(modified, schema)
                    if len(new_errors) < len(errors):
                        log.success(f"修复有效，错误数 {len(errors)} → {len(new_errors)}")
                        with open(input_filepath, 'w', encoding='utf-8') as f:
                            json.dump(modified, f, indent=2, ensure_ascii=False)
                        task_json  = modified
                        errors     = new_errors
                        val_result = generate_report(errors)
                        if val_result["status"] == "success":
                            log.success("AI 修复成功，质检通过！")
                            fixed = True
                            break
                    else:
                        log.warning(f"修复未减少错误（仍有 {len(new_errors)} 个），继续尝试")

                except Exception as e:
                    log.error(f"AI 修复异常: {e}")
                    break

            if not fixed:
                fail_path = os.path.join(report_dir, f"{task_id}_static_fail.json")
                with open(fail_path, 'w', encoding='utf-8') as f:
                    json.dump({"task_id": task_id, "status": "STATIC_FAIL",
                               "errors": val_result.get("errors", [])},
                              f, indent=2, ensure_ascii=False)
                log.error(f"静态质检最终失败（已重试{MAX_FIX_RETRIES}次），"
                          f"报告: tasks_report/{task_id}_static_fail.json")
                log.warning("流程已阻断，请修改需求后重试")
                continue

        pass_path = os.path.join(report_dir, f"{task_id}_static_pass.json")
        with open(pass_path, 'w', encoding='utf-8') as f:
            json.dump({"task_id": task_id, "status": "PASS"}, f)
        log.success("静态质检通过！")

        # ── Step 4: 选择模板 + AI 生成漏洞代码（彭丽诚模块）────────────
        log.step(4, "选择 instance 模板 + AI 生成漏洞代码...")
        try:
            # 优先使用 AI 在蓝图中选好的 instance_ref
            ai_instance_ref = task_json.get('architecture', {}).get('instance_ref', '')
            instances_dir = os.path.join(current_dir, 'templates', 'instances')

            template_info = None

            if ai_instance_ref and os.path.isdir(os.path.join(instances_dir, ai_instance_ref)):
                # AI 选的模板存在，直接使用
                log.success(f"使用 AI 选择的模板: {ai_instance_ref}")
                template_path = os.path.join(instances_dir, ai_instance_ref)
                import json as _json
                manifest = {}
                manifest_path = os.path.join(template_path, 'manifest.json')
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = _json.load(f)
                template_info = {
                    'template_name': ai_instance_ref,
                    'template_path': template_path,
                    'metadata': manifest,
                    'features': matcher.template_features.get(ai_instance_ref, {}),
                    'confidence': 99,
                    'score': 999,
                }
            else:
                # AI 没选或选了不存在的，降级用关键词匹配器
                log.warning(f"AI 选择的模板 '{ai_instance_ref}' 不存在，降级使用关键词匹配器")
                template_info = matcher.match_template(task_json)

            if template_info is None:
                log.error("未找到匹配的 instance 模板，流程中止")
                continue

            log.success(f"最终使用模板: {template_info['template_name']} "
                        f"(置信度: {template_info['confidence']}%)")

            output_path = generator.generate_from_task(task_json, template_info)
            if output_path is None:
                log.error("漏洞代码生成失败，流程中止")
                continue

            log.success(f"漏洞代码已生成: tasks_data/{task_id}_generated/")

        except Exception as e:
            log.error(f"代码生成阶段异常: {e}")
            import traceback
            traceback.print_exc()
            continue

        # ── Step 4.5a: 语法校验 + 自动重试 ────────────────────────────
        log.step(4, "代码语法校验...")
        generated_dir = os.path.join(tasks_data_dir, f"{task_id}_generated")
        MAX_SYNTAX_RETRIES = 2

        from validator.validate_json import validate_code_syntax
        for syntax_attempt in range(MAX_SYNTAX_RETRIES + 1):
            syntax_result = validate_code_syntax(generated_dir)
            if syntax_result['passed']:
                log.success("语法校验通过")
                break
            else:
                for err in syntax_result['errors']:
                    log.error(f"  语法错误 [{err['file']}]: {err['error']}")
                if syntax_attempt < MAX_SYNTAX_RETRIES:
                    log.warning(f"语法校验失败，自动重新生成（第{syntax_attempt+1}/{MAX_SYNTAX_RETRIES}次）...")
                    try:
                        import shutil as _shutil
                        if os.path.exists(generated_dir):
                            _shutil.rmtree(generated_dir)
                        output_path = generator.generate_from_task(task_json, template_info)
                        if output_path is None:
                            log.error("重新生成失败，流程中止")
                            break
                    except Exception as e:
                        log.error(f"重新生成异常: {e}")
                        break
                else:
                    log.error(f"语法校验经{MAX_SYNTAX_RETRIES}次重试仍失败，流程中止")
                    continue

        if not syntax_result['passed']:
            continue

        # ── Step 4.5b: 代码安全检测（杨小琪模块）───────────────────────
        log.step(4, "代码安全检测...")
        generated_dir = os.path.join(tasks_data_dir, f"{task_id}_generated")
        security_passed = True
        try:
            from validator.validate_json import analyze_code_security
            # 扫描生成目录下所有代码文件
            CODE_EXTS = {'.py', '.php', '.c', '.cpp', '.js', '.sql'}
            code_files = []
            if os.path.isdir(generated_dir):
                for root, _, files in os.walk(generated_dir):
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in CODE_EXTS:
                            code_files.append((os.path.join(root, fname), ext[1:]))

            if not code_files:
                log.warning("未找到可检测的代码文件，跳过安全检测")
            else:
                high_risk_count = 0
                for fpath, lang in code_files:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    log.info(f"检测文件: {os.path.basename(fpath)}")
                    result = analyze_code_security(code, lang)
                    if result is None:
                        log.warning(f"  安全检测API调用失败，跳过")
                        continue
                    level = result.get('overall_risk_level', '安全')
                    summary = result.get('summary', '')
                    log.info(f"  风险等级: {level} | {summary}")

                    # 保存详细安全报告
                    sec_report_path = os.path.join(
                        security_dir, f"{task_id}_{os.path.basename(fpath)}_security.json"
                    )
                    with open(sec_report_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)

                    if level == '高危':
                        high_risk_count += 1
                        for risk in result.get('security_risks', []):
                            if risk.get('severity') == '高危':
                                log.error(f"  ⚠ 高危风险: {risk.get('description', '')}")

                if high_risk_count > 0:
                    log.error(f"发现 {high_risk_count} 个高危风险文件，流程中止")
                    log.warning(f"安全报告已保存至: security_reports/")
                    security_passed = False
                else:
                    log.success("代码安全检测通过，未发现高危风险")

        except Exception as e:
            log.warning(f"代码安全检测异常: {e}，跳过继续构建")

        if not security_passed:
            continue

        # ── Step 5: Builder 构建 Docker 环境 ─────────────────────────────
        log.step(5, "施工队开始按图纸作业...")
        success = ctf_builder.build_task(task_id)

        if not success:
            log.error(f"构建失败，详情: tasks_report/{task_id}_build_fail.json")
            continue

        # ── Step 6: 动态检测（占位）──────────────────────────────────────
        log.step(6, "动态检测（模块未接入，跳过）")
        log.warning("动态检测尚未实现，跳过此步骤")

        # ── 最终反馈 ──────────────────────────────────────────────────────
        access_url = f"http://localhost:{assigned_port}"
        success_report = os.path.join(report_dir, f"{task_id}_build_success.json")
        if os.path.exists(success_report):
            with open(success_report, 'r') as f:
                access_url = json.load(f).get("access_url", access_url)

        log.banner(
            "题目已成功上线！",
            task=task_id,
            url=access_url,
            flag=task_json['vulnerability']['flag_value']
        )


if __name__ == "__main__":
    main()
