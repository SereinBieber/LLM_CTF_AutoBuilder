import os, json, logging, subprocess, shutil, time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_INPUT_DIR = os.path.join(BASE_DIR, 'tasks_input')
TASKS_DATA_DIR = os.path.join(BASE_DIR, 'tasks_data')
TASKS_REPORT_DIR = os.path.join(BASE_DIR, 'tasks_report')
TEMPLATES_ROOT = os.path.join(BASE_DIR, 'templates', 'compose_models', 'single-service')
MANUAL_POOL_DIR = os.path.join(TASKS_DATA_DIR, 'manual_pool')


def main():
    logging.info("=== 🛠️ 构建引擎：火力覆盖纯净版启动 ===")

    reports = [f for f in os.listdir(TASKS_REPORT_DIR) if f.endswith('_static_pass.json')]
    for report_file in reports:
        with open(os.path.join(TASKS_REPORT_DIR, report_file), 'r', encoding='utf-8') as f:
            report = json.load(f)
        task_id = report.get('task_id')
        if os.path.exists(os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_success.json")): continue

        task_work_dir = os.path.join(TASKS_DATA_DIR, task_id)
        if os.path.exists(task_work_dir): shutil.rmtree(task_work_dir)
        os.makedirs(task_work_dir)

        try:
            # 1. 严格读取蓝图
            with open(os.path.join(TASKS_INPUT_DIR, f"{task_id}.json"), 'r', encoding='utf-8') as f:
                task_config = json.load(f)

            # 💡 [解耦核心] 严格按照队长最新的“三层架构 Schema”提取图纸数据
            assigned_port = task_config['architecture']['runtime_config']['exposed_port']
            assigned_flag = task_config['vulnerability']['flag_value']
            template_name = task_config['architecture']['compose_model_ref']

            # 2. 搬运材料 (火力覆盖版：防 Docker 空挂载)
            shutil.copytree(os.path.join(TEMPLATES_ROOT, template_name), task_work_dir, dirs_exist_ok=True)
            if os.path.exists(MANUAL_POOL_DIR):
                # 覆盖根目录
                shutil.copytree(MANUAL_POOL_DIR, task_work_dir, dirs_exist_ok=True)
                # 覆盖 src 目录 (防止 compose 里写的是 - ./src:/var/www/html)
                shutil.copytree(MANUAL_POOL_DIR, os.path.join(task_work_dir, 'src'), dirs_exist_ok=True)
                # 覆盖 html 目录 (防止 compose 里写的是 - ./html:/var/www/html)
                shutil.copytree(MANUAL_POOL_DIR, os.path.join(task_work_dir, 'html'), dirs_exist_ok=True)

            # 3. [Flag 注入 & 强制更名 index.php]
            for root, _, files in os.walk(task_work_dir):
                for file in files:
                    if file.endswith('.php'):
                        p = os.path.join(root, file)

                        # 注入 AI 决定的真 Flag
                        with open(p, 'r', encoding='utf-8') as f:
                            content = f.read()
                        new_content = content.replace("flag{SQL_iNjecTi0n_SuCc3ss_2026}", assigned_flag)
                        with open(p, 'w', encoding='utf-8') as f:
                            f.write(new_content)

                        # 强行把所有 php 文件改名为 index.php (解决白板/403问题)
                        if file != 'index.php':
                            new_p = os.path.join(root, 'index.php')
                            try:
                                os.rename(p, new_p)
                                logging.info(f"🔄 自动更名: {file} -> index.php (路径: {root})")
                            except FileExistsError:
                                pass  # 如果已经有 index.php 就不管了

            # 4. 环境装配 (渲染 docker-compose.yml)
            compose_path = os.path.join(task_work_dir, 'docker-compose.yml')
            if os.path.exists(compose_path):
                with open(compose_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = content.replace('flag{test_flag_default}', assigned_flag)
                content = content.replace('../../../base_images', '../../templates/base_images')
                with open(compose_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # 5. 施工 (启动 Docker)
            env = os.environ.copy()
            env.update({'TASK_ID': str(task_id), 'EXPOSED_PORT': str(assigned_port)})
            subprocess.run(["docker-compose", "up", "-d", "--build"], cwd=task_work_dir, env=env, check=True)

            # 6. 提权 (彻底粉碎 403 权限问题)
            time.sleep(2)
            subprocess.run(["docker", "exec", f"{task_id}_web", "chmod", "-R", "777", "/var/www/html"], check=False)

            # 竣工存档
            access_url = f"http://localhost:{assigned_port}"
            with open(os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_success.json"), 'w') as f:
                json.dump({"status": "SUCCESS", "access_url": access_url}, f)

            # 🖥️ 终端高亮展示网站链接
            logging.info("=" * 45)
            logging.info(f"🎉 靶场构建圆满成功！")
            logging.info(f"🔗 请直接点击或访问网站: {access_url}")
            logging.info("=" * 45)

        except Exception as e:
            logging.error(f"❌ 施工失败: {e}")


if __name__ == '__main__':
    main()