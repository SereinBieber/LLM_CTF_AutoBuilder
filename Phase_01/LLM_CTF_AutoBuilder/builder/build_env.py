"""
builder/build_env.py
施工队核心模块
"""

import os
import json
import subprocess
import shutil
import re
import sys

# 彩色日志
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.logger import log

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_INPUT_DIR = os.path.join(BASE_DIR, 'tasks_input')
TASKS_DATA_DIR  = os.path.join(BASE_DIR, 'tasks_data')
TASKS_REPORT_DIR= os.path.join(BASE_DIR, 'tasks_report')
COMPOSE_SINGLE  = os.path.join(BASE_DIR, 'templates', 'compose_models', 'single-service')
COMPOSE_DUAL    = os.path.join(BASE_DIR, 'templates', 'compose_models', 'dual-service')
INSTANCES_DIR   = os.path.join(BASE_DIR, 'templates', 'instances')

# 所有源码/compose 模板里统一用这个字符串作为 flag 占位符
FLAG_PLACEHOLDER = "FLAG_PLACEHOLDER"


def build_task(task_id: str) -> bool:
    """
    构建指定 task_id 的题目环境。
    返回 True=成功，False=失败。
    """
    task_work_dir      = os.path.join(TASKS_DATA_DIR, task_id)
    success_report     = os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_success.json")
    fail_report        = os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_fail.json")

    if os.path.exists(success_report):
        log.warning(f"任务 {task_id} 已构建成功，跳过重复构建")
        return True

    # 清理旧的脏目录
    if os.path.exists(task_work_dir):
        shutil.rmtree(task_work_dir)
    os.makedirs(task_work_dir)

    try:
        # ── Step A: 读取蓝图 ─────────────────────────────────────────────
        task_json_path = os.path.join(TASKS_INPUT_DIR, f"{task_id}.json")
        if not os.path.exists(task_json_path):
            raise FileNotFoundError(f"找不到蓝图文件: {task_json_path}")

        with open(task_json_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)

        assigned_port      = cfg['architecture']['runtime_config']['exposed_port']
        assigned_flag      = cfg['vulnerability']['flag_value']
        compose_model_ref  = cfg['architecture']['compose_model_ref']
        instance_ref       = cfg['architecture'].get('instance_ref', '')

        log.info(f"端口 {assigned_port}  |  模型 {compose_model_ref}  |  实例 {instance_ref}")

        # ── Step B: 复制 compose 模板 ────────────────────────────────────
        compose_tmpl = os.path.join(COMPOSE_SINGLE, compose_model_ref)
        if not os.path.isdir(compose_tmpl):
            compose_tmpl = os.path.join(COMPOSE_DUAL, compose_model_ref)
        if not os.path.isdir(compose_tmpl):
            raise FileNotFoundError(
                f"找不到 compose 模板 '{compose_model_ref}'，"
                f"请检查 templates/compose_models 目录"
            )
        shutil.copytree(compose_tmpl, task_work_dir, dirs_exist_ok=True)
        log.success(f"compose 模板已复制: {compose_model_ref}")

        # ── Step C: 复制漏洞源码到 src/ ──────────────────────────────────
        instance_src = None
        if instance_ref:
            candidate = os.path.join(INSTANCES_DIR, instance_ref)
            if os.path.isdir(candidate):
                instance_src = candidate

        if instance_src is None:
            manual_pool = os.path.join(TASKS_DATA_DIR, 'manual_pool')
            if os.path.isdir(manual_pool):
                instance_src = manual_pool
                log.warning(f"未找到实例 '{instance_ref}'，回退到 manual_pool")

        if instance_src:
            dest = os.path.join(task_work_dir, 'src')
            if os.path.exists(dest):
                shutil.rmtree(dest)
            sub = os.path.join(instance_src, 'src')
            shutil.copytree(sub if os.path.isdir(sub) else instance_src, dest)
            log.success(f"漏洞源码已复制: {os.path.basename(instance_src)} → src/")
        else:
            log.warning("没有找到任何漏洞源码，src/ 为空，题目可能无法访问")

        # ── Step D: Flag 注入 ─────────────────────────────────────────────
        _inject_flag(task_work_dir, FLAG_PLACEHOLDER, assigned_flag)
        log.success(f"Flag 已注入: {assigned_flag}")

        # ── Step E: 修正 docker-compose.yml ──────────────────────────────
        compose_path = os.path.join(task_work_dir, 'docker-compose.yml')
        if not os.path.exists(compose_path):
            raise FileNotFoundError("compose 模板中缺少 docker-compose.yml")
        _patch_compose(compose_path, assigned_flag, BASE_DIR)
        log.success("docker-compose.yml 路径和占位符已修正")

        # ── Step F: 启动 Docker ───────────────────────────────────────────
        env = os.environ.copy()
        env.update({
            'TASK_ID':      task_id,
            'EXPOSED_PORT': str(assigned_port),
            'FLAG':         assigned_flag,
        })
        log.info("正在执行 docker-compose up --build ...")
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            cwd=task_work_dir, env=env,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"docker-compose 退出码 {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

        # ── 竣工 ──────────────────────────────────────────────────────────
        access_url = f"http://localhost:{assigned_port}"
        os.makedirs(TASKS_REPORT_DIR, exist_ok=True)
        with open(success_report, 'w', encoding='utf-8') as f:
            json.dump({"task_id": task_id, "status": "SUCCESS",
                       "access_url": access_url, "flag": assigned_flag},
                      f, indent=2, ensure_ascii=False)

        log.banner("靶场构建成功！", task=task_id, url=access_url, flag=assigned_flag)
        return True

    except Exception as e:
        log.fail_banner("构建失败", reason=str(e),
                        report_path=os.path.basename(fail_report))
        os.makedirs(TASKS_REPORT_DIR, exist_ok=True)
        with open(fail_report, 'w', encoding='utf-8') as f:
            json.dump({"task_id": task_id, "status": "FAILED", "reason": str(e)},
                      f, indent=2, ensure_ascii=False)
        if os.path.exists(task_work_dir):
            shutil.rmtree(task_work_dir)
        return False


# ── 内部工具 ──────────────────────────────────────────────────────────────────

def _inject_flag(root_dir: str, placeholder: str, flag_value: str):
    TEXT_EXTS = {'.php', '.py', '.js', '.html', '.htm', '.txt',
                 '.sh', '.yml', '.yaml', '.json', '.conf', '.c', '.cpp'}
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() not in TEXT_EXTS:
                continue
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if placeholder in content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content.replace(placeholder, flag_value))
            except (UnicodeDecodeError, PermissionError):
                pass


def _patch_compose(compose_path: str, flag: str, base_dir: str):
    with open(compose_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 把相对路径 ../../../base_images/xxx 改成绝对路径
    base_images_abs = os.path.join(base_dir, 'templates', 'base_images').replace('\\', '/')
    content = re.sub(r'(\.\./)+base_images', base_images_abs, content)
    # 向后兼容旧占位符
    content = content.replace('flag{test_flag_default}', flag)
    content = content.replace(FLAG_PLACEHOLDER, flag)
    with open(compose_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """独立运行时扫描全量待构建任务"""
    if not os.path.exists(TASKS_REPORT_DIR):
        log.warning("tasks_report 目录不存在，无任务可构建")
        return
    reports = [f for f in os.listdir(TASKS_REPORT_DIR) if f.endswith('_static_pass.json')]
    if not reports:
        log.info("没有等待构建的任务")
        return
    for report_file in reports:
        with open(os.path.join(TASKS_REPORT_DIR, report_file), 'r', encoding='utf-8') as f:
            report = json.load(f)
        task_id = report.get('task_id')
        if task_id:
            build_task(task_id)


if __name__ == '__main__':
    main()