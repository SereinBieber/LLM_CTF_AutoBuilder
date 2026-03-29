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
import secrets

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

FLAG_PLACEHOLDER = "FLAG_PLACEHOLDER"


def build_task(task_id: str) -> bool:
    task_work_dir  = os.path.join(TASKS_DATA_DIR, task_id)
    success_report = os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_success.json")
    fail_report    = os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_fail.json")

    if os.path.exists(success_report):
        log.warning(f"任务 {task_id} 已构建成功，跳过重复构建")
        return True

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

        assigned_port     = cfg['architecture']['runtime_config']['exposed_port']
        assigned_flag     = cfg['vulnerability']['flag_value']
        compose_model_ref = cfg['architecture']['compose_model_ref']
        instance_ref      = cfg['architecture'].get('instance_ref', '')

        # 从 instance manifest 读取正确的 compose_model（优先级高于AI蓝图）
        if instance_ref:
            manifest_path = os.path.join(INSTANCES_DIR, instance_ref, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                manifest_compose = manifest.get('requirements', {}).get('compose_model', '')
                if manifest_compose and manifest_compose != compose_model_ref:
                    log.warning(f"compose_model 已由 manifest 修正: "
                                f"{compose_model_ref} → {manifest_compose}")
                    compose_model_ref = manifest_compose

        # 生成数据库随机密码
        db_root_pass = secrets.token_hex(8)
        db_user_pass = secrets.token_hex(8)

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

        # ── Step C: 复制漏洞源码 ─────────────────────────────────────────
        instance_src = None

        # 优先①：AI 生成的漏洞代码
        generated_dir = os.path.join(TASKS_DATA_DIR, f"{task_id}_generated")
        if os.path.isdir(generated_dir):
            instance_src = generated_dir
            log.success(f"使用 AI 生成的漏洞代码: tasks_data/{task_id}_generated/")

        # 回退②：instance 模板目录
        if instance_src is None and instance_ref:
            candidate = os.path.join(INSTANCES_DIR, instance_ref)
            if os.path.isdir(candidate):
                instance_src = candidate
                log.warning(f"未找到 AI 生成代码，回退到 instance 模板: {instance_ref}")

        # 回退③：manual_pool
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

            # 同步复制数据库初始化文件（兼容 db/ 和 data/ 两种目录名，统一输出到 db/）
            db_src = None
            for candidate in ['db', 'data']:
                candidate_path = os.path.join(instance_src, candidate)
                if os.path.isdir(candidate_path):
                    db_src = candidate_path
                    break

            if db_src:
                db_dest = os.path.join(task_work_dir, 'db')
                if os.path.exists(db_dest):
                    shutil.rmtree(db_dest)
                shutil.copytree(db_src, db_dest)
                log.success(f"数据库初始化文件已复制: {os.path.basename(db_src)}/ → db/")
        else:
            log.warning("没有找到任何漏洞源码，src/ 为空")

        # ── Step D: Flag 注入 ────────────────────────────────────────────
        _inject_flag(task_work_dir, FLAG_PLACEHOLDER, assigned_flag)
        log.success(f"Flag 已注入: {assigned_flag}")

        # ── Step D.3: PNG图片LSB隐写flag注入 ────────────────────────────
        print(f"  [D.3] 扫描PNG文件: {task_work_dir}")
        for _dirpath, _, _filenames in os.walk(task_work_dir):
            for _fname in _filenames:
                if _fname.endswith('.png'):
                    _png_path = os.path.join(_dirpath, _fname)
                    try:
                        from PIL import Image as _PIL_Image
                        _img = _PIL_Image.open(_png_path)
                        _pixels = list(_img.getdata())
                        _bits = []
                        for _pixel in _pixels:
                            for _channel in list(_pixel)[:3]:
                                _bits.append(_channel & 1)
                        _chars = []
                        for _i in range(0, len(_bits), 8):
                            _byte = _bits[_i:_i+8]
                            if len(_byte) < 8:
                                break
                            _c = chr(int(''.join(map(str, _byte)), 2))
                            if _c == chr(0):
                                break
                            _chars.append(_c)
                        _hidden = ''.join(_chars)
                        if 'FLAG_PLACEHOLDER' in _hidden:
                            _new_msg = _hidden.replace('FLAG_PLACEHOLDER', assigned_flag)
                            _msg_bytes = _new_msg.encode('utf-8') + b'\x00'
                            _new_bits = []
                            for _b in _msg_bytes:
                                for _i in range(7, -1, -1):
                                    _new_bits.append((_b >> _i) & 1)
                            _new_pixels = []
                            _bit_idx = 0
                            for _pixel in _pixels:
                                _r, _g, _b = list(_pixel)[:3]
                                if _bit_idx < len(_new_bits):
                                    _r = (_r & 0xFE) | _new_bits[_bit_idx]; _bit_idx += 1
                                if _bit_idx < len(_new_bits):
                                    _g = (_g & 0xFE) | _new_bits[_bit_idx]; _bit_idx += 1
                                if _bit_idx < len(_new_bits):
                                    _b = (_b & 0xFE) | _new_bits[_bit_idx]; _bit_idx += 1
                                _new_pixels.append((_r, _g, _b))
                            _new_img = _PIL_Image.new('RGB', _img.size)
                            _new_img.putdata(_new_pixels)
                            _new_img.save(_png_path)
                            log.success(f"PNG LSB隐写已更新: {_fname}")
                    except Exception as _e:
                        log.warning(f"PNG LSB注入失败: {_e}")

        # ── Step D.5: 兜底修复各题型特有问题 ──────────────────────────────

        # PWN题：强制修复build.sh编译参数，关闭PIE
        if instance_ref and 'pwn' in instance_ref:
            import re as _re
            for dirpath, _, filenames in os.walk(task_work_dir):
                for fname in filenames:
                    if fname == 'build.sh':
                        fpath = os.path.join(dirpath, fname)
                        try:
                            with open(fpath, 'r', encoding='utf-8') as f:
                                sh = f.read()
                            # 如果没有-no-pie就加上
                            if '-no-pie' not in sh:
                                sh = sh.replace('gcc ', 'gcc -fno-stack-protector -z execstack -no-pie -w ')
                                sh = sh.replace('gcc  ', 'gcc ')
                            with open(fpath, 'w', encoding='utf-8') as f:
                                f.write(sh)
                            log.success("PWN build.sh已修复: 强制关闭PIE")
                        except Exception:
                            pass

        # Redis题：自动生成无认证配置
        redis_conf = os.path.join(task_work_dir, 'conf', 'redis.conf')
        if not os.path.exists(redis_conf) and 'redis' in compose_model_ref:
            os.makedirs(os.path.join(task_work_dir, 'conf'), exist_ok=True)
            with open(redis_conf, 'w', encoding='utf-8') as f:
                f.write("# Redis未授权访问配置\n")
                f.write("bind 0.0.0.0\n")
                f.write("protected-mode no\n")
                f.write("port 6379\n")
            log.success("Redis配置文件已自动生成: conf/redis.conf")

        # PostgreSQL题：移除MySQL语法
        if 'postgres' in compose_model_ref:
            import re as _re
            for dirpath, _, filenames in os.walk(task_work_dir):
                for fname in filenames:
                    if fname.endswith('.sql'):
                        fpath = os.path.join(dirpath, fname)
                        try:
                            with open(fpath, 'r', encoding='utf-8') as f:
                                sql = f.read()
                            sql = _re.sub(r'CREATE DATABASE IF NOT EXISTS \w+;\s*', '', sql)
                            sql = _re.sub(r'USE \w+;\s*', '', sql)
                            sql = sql.replace('`', '"')
                            with open(fpath, 'w', encoding='utf-8') as f:
                                f.write(sql)
                            log.success("PostgreSQL init.sql已修复: 移除MySQL语法")
                        except Exception:
                            pass

        # MongoDB题：修复init.js里的process.env变量
        if 'mongo' in compose_model_ref:
            import re as _re
            for dirpath, _, filenames in os.walk(task_work_dir):
                for fname in filenames:
                    if fname.endswith('.js'):
                        fpath = os.path.join(dirpath, fname)
                        try:
                            with open(fpath, 'r', encoding='utf-8') as f:
                                js = f.read()
                            js = _re.sub(r"process\.env\.[A-Z_]+\s*\|\|\s*'([^']+)'", r"''", js)
                            js = _re.sub(r'process\.env\.[A-Z_]+\s*\|\|\s*"([^"]+)"', r'""', js)
                            js = js.replace("process.env.DB_NAME", "'ctf_db'")
                            with open(fpath, 'w', encoding='utf-8') as f:
                                f.write(js)
                            log.success("MongoDB init.js已修复: 移除process.env变量")
                        except Exception:
                            pass

        # ── Step E: 修正 docker-compose.yml ──────────────────────────────
        compose_path = os.path.join(task_work_dir, 'docker-compose.yml')
        if not os.path.exists(compose_path):
            raise FileNotFoundError("compose 模板中缺少 docker-compose.yml")
        _patch_compose(compose_path, assigned_flag, BASE_DIR,
                       db_root_pass, db_user_pass)
        log.success("docker-compose.yml 路径和占位符已修正")

        # ── Step F: 启动 Docker ──────────────────────────────────────────
        env = os.environ.copy()
        env.update({
            'TASK_ID':      task_id,
            'EXPOSED_PORT': str(assigned_port),
            'FLAG':         assigned_flag,
            'DB_ROOT_PASS': db_root_pass,
            'DB_USER_PASS': db_user_pass,
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

        # ── 竣工 ─────────────────────────────────────────────────────────
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
                 '.sh', '.yml', '.yaml', '.json', '.conf', '.c', '.cpp', '.sql'}
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


def _patch_compose(compose_path: str, flag: str, base_dir: str,
                   db_root_pass: str = '', db_user_pass: str = ''):
    with open(compose_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 绝对路径替换
    base_images_abs = os.path.join(base_dir, 'templates', 'base_images').replace('\\', '/')
    content = re.sub(r'(\.\./)+base_images', base_images_abs, content)

    # flag 占位符替换
    content = content.replace('flag{test_flag_default}', flag)
    content = content.replace(FLAG_PLACEHOLDER, flag)

    # 数据库密码占位符替换（直接写死到yml，不依赖环境变量展开）
    if db_root_pass:
        content = content.replace('${DB_ROOT_PASS}', db_root_pass)
    if db_user_pass:
        content = content.replace('${DB_USER_PASS}', db_user_pass)

    with open(compose_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
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
