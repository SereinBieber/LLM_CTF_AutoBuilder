"""
core/logger.py
全项目统一彩色日志模块

用法：
    from core.logger import log
    log.step(1, "AI 正在生成题目蓝图")
    log.info("正在处理文件...")
    log.success("构建成功！")
    log.warning("找不到实例，回退到 manual_pool")
    log.error("docker-compose 启动失败")
    log.banner("靶场上线", url="http://localhost:18080", flag="flag{xxx}")
"""

import sys
import logging
from colorama import Fore, Style, init

init(autoreset=True)  # Windows 兼容


class ColorLogger:
    def __init__(self, name: str = "CTF_Builder"):
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.DEBUG)
            # 阻止传播到 root logger，避免红色重复输出
            self._logger.propagate = False

    def step(self, num: int, text: str):
        """流程步骤 —— 青蓝色加粗"""
        self._logger.info(
            f"{Fore.CYAN}{Style.BRIGHT}[Step {num}] ▶  {text}{Style.RESET_ALL}"
        )

    def info(self, text: str):
        """普通信息 —— 默认白色"""
        self._logger.info(f"  {text}")

    def success(self, text: str):
        """成功 —— 绿色"""
        self._logger.info(f"{Fore.GREEN}{Style.BRIGHT}  ✅ {text}{Style.RESET_ALL}")

    def warning(self, text: str):
        """警告 —— 黄色（不是错误，别怕）"""
        self._logger.warning(f"{Fore.YELLOW}  ⚠️  {text}{Style.RESET_ALL}")

    def error(self, text: str):
        """真正的错误 —— 红色加粗"""
        self._logger.error(f"{Fore.RED}{Style.BRIGHT}  ❌ {text}{Style.RESET_ALL}")

    def banner(self, title: str, **kwargs):
        """最终成功横幅 —— 绿色大框"""
        width = 54
        self._logger.info(f"{Fore.GREEN}{Style.BRIGHT}{'=' * width}")
        self._logger.info(f"  🎉  {title}")
        labels = {"url": "🔗 访问地址", "flag": "🚩 Flag", "task": "📋 任务ID"}
        for k, v in kwargs.items():
            self._logger.info(f"  {labels.get(k, k)}: {v}")
        self._logger.info(f"{'=' * width}{Style.RESET_ALL}")

    def fail_banner(self, title: str, reason: str = "", report_path: str = ""):
        """失败横幅 —— 红色"""
        width = 54
        self._logger.error(f"{Fore.RED}{Style.BRIGHT}{'=' * width}")
        self._logger.error(f"  💥  {title}")
        if reason:
            self._logger.error(f"  原因: {reason.splitlines()[0]}")
        if report_path:
            self._logger.error(f"  详情: {report_path}")
        self._logger.error(f"{'=' * width}{Style.RESET_ALL}")


# 全局单例，所有模块 from core.logger import log 即可
log = ColorLogger()