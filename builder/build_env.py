#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTF AutoBuilder Engine (软著工程级版)
核心功能：事件驱动构建。监听静态检测报告，结合 AI 产出配置与代码，调度底层模具实现容器化部署。
"""

import os
import json
import logging
import datetime
import subprocess

# 配置工业级日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

# 1. 定义核心目录的绝对路径 (基于当前脚本位置往上一级)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_INPUT_DIR = os.path.join(PROJECT_ROOT, 'tasks_input')
TASKS_DATA_DIR = os.path.join(PROJECT_ROOT, 'tasks_data')
TASKS_REPORT_DIR = os.path.join(PROJECT_ROOT, 'tasks_report')
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates', 'compose_models', 'single-service')


def main():
    logging.info("=== CTF AutoBuilder Engine 启动 ===")
    logging.info("正在扫描 tasks_report 目录，等待杨小琪的静态检测通过报告...")

    # 遍历报告目录，寻找以 _static_pass.json 结尾的文件
    for report_file in os.listdir(TASKS_REPORT_DIR):
        if not report_file.endswith('_static_pass.json'):
            continue

        report_path = os.path.join(TASKS_REPORT_DIR, report_file)
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        # 【校验点 1】只处理状态为 PASS 的任务
        if report.get('status') != 'PASS':
            continue

        task_id = report.get('task_id')
        build_report_path = os.path.join(TASKS_REPORT_DIR, f"{task_id}_build_success.json")

        # 【校验点 2】幂等性设计：如果已经构建过了，直接跳过，防止重复启动
        if os.path.exists(build_report_path):
            continue

        logging.info(f"🎯 发现已过审任务: {task_id}，开始进入构建流水线...")

        try:
            # 2. 读取彭丽诚的配置文件 (tasks_input)
            input_file = os.path.join(TASKS_INPUT_DIR, f"{task_id}.json")
            with open(input_file, 'r', encoding='utf-8') as f:
                task_config = json.load(f)

            template_name = task_config.get('template')
            port = task_config.get('port')
            flag = task_config['meta']['flag']

            # 3. 定位生产车间 (tasks_data) 和 图纸模具 (templates)
            task_data_dir = os.path.join(TASKS_DATA_DIR, task_id)
            template_compose_path = os.path.join(TEMPLATES_DIR, template_name, 'docker-compose.yml')

            if not os.path.exists(template_compose_path):
                raise FileNotFoundError(f"严重错误：找不到对应的模具 {template_name}")

            # 4. 【核心工程设计：Manifest 渲染】
            # 读取原始模具，动态替换镜像路径和 FLAG，并将其生成到 tasks_data 目录下
            logging.info(f"正在渲染 {template_name} 模具...")
            with open(template_compose_path, 'r', encoding='utf-8') as f:
                compose_content = f.read()

            # 修正 Docker 相对路径：因为 compose 被挪到了 tasks_data/<task_id> 下
            # 从 tasks_data/task_test_rce 寻找 base_images 需要 ../../templates/base_images
            compose_content = compose_content.replace('../../../base_images', '../../templates/base_images')

            # 动态注入真实的 Flag
            compose_content = compose_content.replace('flag{test_flag_default}', flag)

            # 将渲染后的“施工图纸”存入实战目录
            target_compose = os.path.join(task_data_dir, 'docker-compose.yml')
            with open(target_compose, 'w', encoding='utf-8') as f:
                f.write(compose_content)

            # 5. 设置环境变量并启动 Docker
            logging.info(f"🚀 开始启动 Docker 容器 (端口: {port})...")
            env = os.environ.copy()
            env['TASK_ID'] = task_id
            env['EXPOSED_PORT'] = str(port)

            # 执行 docker-compose up -d --build
            subprocess.run(
                ["docker-compose", "up", "-d", "--build"],
                cwd=task_data_dir,
                env=env,
                check=True
            )

            # 6. 生成竣工报告 (写回 tasks_report)
            success_report = {
                "task_id": task_id,
                "stage": "build_deploy",
                "status": "SUCCESS",
                "access_url": f"http://localhost:{port}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            with open(build_report_path, 'w', encoding='utf-8') as f:
                json.dump(success_report, f, indent=4, ensure_ascii=False)

            logging.info(f"✅ 构建成功！可以通过 {success_report['access_url']} 访问靶场。\n")

        except Exception as e:
            logging.error(f"❌ 任务 {task_id} 构建失败: {str(e)}")


if __name__ == '__main__':
    main()