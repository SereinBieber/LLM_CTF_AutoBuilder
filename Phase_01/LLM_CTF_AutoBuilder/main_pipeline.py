"""
main_pipeline.py
总指挥 —— 串联所有模块的主流程

关键改动：
1. 彩色日志，绿色=成功 / 黄色=警告 / 红色=真正出错
2. 端口由服务端真随机生成，AI 给的端口直接被覆盖，杜绝"AI 偏爱固定端口"问题
3. builder 改为 build_task(task_id) 精准调用
4. 静态检测失败写报告，预留自动修复 TODO
"""

import os
import json
import random
import time
import sys

from core.logger import log
from llm_parser.deepseek_handler import DeepSeekHandler
from validator.validate_json import load_schema, validate_json, generate_report
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
    """
    在 PORT_MIN~PORT_MAX 范围内随机挑一个未被占用的端口。
    使用 random.sample 从候选池里一次性随机打乱再逐个尝试，
    保证均匀分布、不重复、不偏爱任何特定数字。
    """
    used = _get_used_ports(tasks_input_dir)
    candidates = list(range(PORT_MIN, PORT_MAX + 1))
    random.shuffle(candidates)          # 真随机打乱，不依赖 AI
    for port in candidates:
        if port not in used:
            return port
    raise RuntimeError(f"端口池 {PORT_MIN}-{PORT_MAX} 已全部占用！")


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n🏆  LLM_CTF_AutoBuilder  Pipeline V3.0\n")

    current_dir      = os.path.dirname(os.path.abspath(__file__))
    tasks_input_dir  = os.path.join(current_dir, 'tasks_input')
    report_dir       = os.path.join(current_dir, 'tasks_report')
    os.makedirs(report_dir, exist_ok=True)

    # 加载 Schema
    schema_path = os.path.join(current_dir, 'schema', 'ctf_task_schema.json')
    if not os.path.exists(schema_path):
        log.error(f"找不到 Schema 文件: {schema_path}")
        return
    schema = load_schema(schema_path)

    # 扫描可用 compose 模板，告诉 AI 只能选这些
    templates_dir = os.path.join(current_dir, 'templates', 'compose_models', 'single-service')
    available_templates = (
        [d for d in os.listdir(templates_dir) if os.path.isdir(os.path.join(templates_dir, d))]
        if os.path.isdir(templates_dir) else []
    )

    handler = DeepSeekHandler()

    while True:
        user_input = input("\n📝  请输入你想要的 CTF 题目类型  (q 退出): ").strip()
        if user_input.lower() in ['q', 'quit']:
            break
        if not user_input:
            continue

        # ── Step 1: 服务端先分配端口，AI 不参与 ─────────────────────────
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

        # 无论 AI 填了什么端口，服务端强制覆盖
        task_json.setdefault('architecture', {}).setdefault('runtime_config', {})
        task_json['architecture']['runtime_config']['exposed_port'] = assigned_port

        task_id = task_json.get("task_id", f"task_{int(time.time())}")
        handler.save_json(task_json)
        log.success(f"蓝图已生成并保存，task_id: {task_id}，端口已锁定为 {assigned_port}")

        # ── Step 3: 静态质检 ─────────────────────────────────────────────
        log.step(3, "静态质检（Schema 校验）")
        errors    = validate_json(task_json, schema)
        val_result = generate_report(errors)

        if val_result["status"] != "success":
            log.error("静态质检未通过，发现以下问题：")
            for err in val_result.get("errors", []):
                log.error(f"  · {err}")

            fail_path = os.path.join(report_dir, f"{task_id}_static_fail.json")
            with open(fail_path, 'w', encoding='utf-8') as f:
                json.dump({"task_id": task_id, "status": "STATIC_FAIL",
                           "errors": val_result.get("errors", [])},
                          f, indent=2, ensure_ascii=False)
            log.warning(f"失败报告已写入: tasks_report/{task_id}_static_fail.json")

            # TODO: 此处接自动修复逻辑（杨小琪负责）
            log.warning("流程已阻断，请修改需求后重试")
            continue

        pass_path = os.path.join(report_dir, f"{task_id}_static_pass.json")
        with open(pass_path, 'w', encoding='utf-8') as f:
            json.dump({"task_id": task_id, "status": "PASS"}, f)
        log.success("静态质检通过！")

        # ── Step 4: Builder 构建 Docker 环境 ─────────────────────────────
        log.step(4, "施工队开始按图纸作业...")
        success = ctf_builder.build_task(task_id)

        if not success:
            log.error(f"构建失败，详情: tasks_report/{task_id}_build_fail.json")
            continue

        # ── Step 5: 动态检测（占位，杨小琪接入）─────────────────────────
        log.step(5, "动态检测（模块未接入，跳过）")
        log.warning("动态检测尚未实现，跳过此步骤")
        # TODO: dynamic_checker.check(task_id, access_url)

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