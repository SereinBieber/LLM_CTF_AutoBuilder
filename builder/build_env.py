import os
import json
import time
import shutil
import subprocess
import datetime

# 尝试导入 jsonschema，如果没有安装则提示
try:
    import jsonschema
except ImportError:
    print("❌ 严重错误: 缺少 'jsonschema' 库！请运行: pip install jsonschema")
    exit(1)

# === 1. 核心路径配置 (必须最先定义) ===
# 获取当前脚本的上级目录的上级目录，即项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 各个功能区的绝对路径
TASKS_INPUT_DIR = os.path.join(BASE_DIR, "tasks_input")  # 宪法/菜单
TASKS_DATA_DIR = os.path.join(BASE_DIR, "tasks_data")  # 仓库/食材
TASKS_REPORT_DIR = os.path.join(BASE_DIR, "tasks_report")  # 档案室/体检单
RUNNING_TASKS_DIR = os.path.join(BASE_DIR, "running_tasks")  # 工地/厨房
SCHEMA_PATH = os.path.join(BASE_DIR, "schema", "protocol.json")  # 协议文件

# 模板目录 (目前 MVP 阶段写死，未来可动态获取)
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates", "compose_models", "dual-service", "web-db-linked")


# === 2. 加载协议层 (Protocol Layer) ===
def load_protocol():
    """加载 JSON Schema 协议定义，如果失败返回 None"""
    # === 👇 加上这两行调试代码 👇 ===
    print(f"🔎 正在寻找宪法文件，路径是: {SCHEMA_PATH}")
    print(f"🔎 该路径是否存在? {os.path.exists(SCHEMA_PATH)}")
    # ============================

    if not os.path.exists(SCHEMA_PATH):
        return None
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 协议文件损坏: {e}")
        return None


# 全局变量：加载一次协议
PROTOCOL = load_protocol()


def main():
    print(f"👨‍✈️ [Builder System] 启动初始化...")
    print(f"📂 监控目录: {TASKS_REPORT_DIR}")
    print(f"📜 协议状态: {'✅ 已加载' if PROTOCOL else '❌ 未找到 (进入降级模式)'}")

    # 确保报告目录存在
    if not os.path.exists(TASKS_REPORT_DIR):
        os.makedirs(TASKS_REPORT_DIR)

    while True:
        # === 3. 协议层熔断保护 ===
        if PROTOCOL is None:
            print("⚠️ [警告] 协议层缺失！Builder 已暂停工作，请检查 schemas/protocol.json")
            time.sleep(5)
            continue

        # 扫描文件
        try:
            files = os.listdir(TASKS_REPORT_DIR)
        except Exception:
            files = []

        for filename in files:
            # 过滤：只处理静态检测报告
            if "static_check" in filename and filename.endswith(".json"):
                process_report(filename)

        # 轮询休眠 (Poling Interval)
        # 答辩话术：当前采用轮询模型，生产环境可升级为文件系统事件监听 (Inotify)
        time.sleep(2)


def process_report(filename):
    """处理单个报告文件：校验 -> 判断 -> 构建"""
    report_path = os.path.join(TASKS_REPORT_DIR, filename)

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        print(f"⚠️ 文件读取失败 {filename}: {e}")
        return

    # === 4. 协议校验 (Schema Validation) ===
    try:
        schema_def = PROTOCOL["definitions"]["static_check_report"]
        jsonschema.validate(instance=report, schema=schema_def)
    except jsonschema.ValidationError as e:
        print(f"🛡️ [安全拦截] 发现非法格式报告 {filename}: {e.message}")
        return  # 直接丢弃，不崩坏系统

    # 提取关键字段
    task_id = report.get("task_id")
    status = report.get("status")

    # === 5. 业务逻辑决策 ===
    if status == "PASS":
        if is_task_running(task_id):
            return  # 已运行，跳过

        print(f"\n✅ [指令接收] 任务 {task_id} 静态检测通过，开始构建...")

        # 💡 未来扩展点：这里应该读取 tasks_input/task_id.json 来决定 template_name
        # template_name = load_task_config(task_id).get("template")

        build_and_run(task_id)

    elif status == "FAIL":
        # 可以在这里记录日志
        pass


def is_task_running(task_id):
    """检查任务是否已经在运行"""
    return os.path.exists(os.path.join(RUNNING_TASKS_DIR, task_id))


def build_and_run(task_id):
    """执行 Docker 构建流程"""
    target_dir = os.path.join(RUNNING_TASKS_DIR, task_id)

    # 清理旧环境
    if os.path.exists(target_dir):
        try:
            shutil.rmtree(target_dir)
        except Exception as e:
            print(f"❌ 清理失败: {e}")
            return

    os.makedirs(target_dir)
    print(f"📦 [1/3] 初始化构建环境: {target_dir}")

    # 搬运模板
    if not os.path.exists(TEMPLATE_DIR):
        print(f"❌ 模板丢失: {TEMPLATE_DIR}")
        return
    shutil.copy(os.path.join(TEMPLATE_DIR, "Dockerfile"), target_dir)
    shutil.copy(os.path.join(TEMPLATE_DIR, "docker-compose.yml"), target_dir)

    # 搬运源码
    source_code_dir = os.path.join(TASKS_DATA_DIR, task_id)
    if not os.path.exists(source_code_dir):
        print(f"❌ 源码丢失: {source_code_dir}")
        return
    shutil.copytree(os.path.join(source_code_dir, "src"), os.path.join(target_dir, "src"))
    shutil.copytree(os.path.join(source_code_dir, "db"), os.path.join(target_dir, "db"))

    # 启动 Docker
    print(f"🚀 [2/3] 启动容器编排...")

    # 注入环境变量
    env_vars = os.environ.copy()
    env_vars["TASK_ID"] = task_id
    env_vars["DB_ROOT_PASS"] = "root"
    env_vars["EXPOSED_PORT"] = "20002"  # 暂时写死，未来从 input json 读

    try:
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            cwd=target_dir,
            env=env_vars,
            check=True
        )
        print(f"🎉 [3/3] 任务 {task_id} 部署成功！")

        # 生成成功报告 (符合协议标准)
        success_report = {
            "task_id": task_id,
            "stage": "build_deploy",
            "status": "SUCCESS",
            "access_url": "http://localhost:20002",
            "container_id": f"{task_id}_web",
            "timestamp": datetime.datetime.now().isoformat()
        }

        with open(os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_success.json"), "w") as f:
            json.dump(success_report, f, indent=2)

    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")


if __name__ == "__main__":
    main()