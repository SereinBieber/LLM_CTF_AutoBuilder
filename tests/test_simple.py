"""
简单测试文件
1. 用户输入自然语言
2. 生成JSON配置
3. 匹配instances模板
4. 生成漏洞代码到tasks_data
"""

import os
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from llm_parser.deepseek_handler import DeepSeekHandler
from llm_parser.template_matcher import TemplateMatcher
from llm_parser.vulnerability_generator import VulnerabilityGenerator

print("所有环境变量:", list(os.environ.keys()))
print("DEEPSEEK_API_KEY:", os.getenv("DEEPSEEK_API_KEY"))

def main():
    print("=" * 50)
    print("🎯 CTF自动化生成器测试")
    print("功能: 自然语言 → JSON配置 → 模板匹配 → 漏洞代码")
    print("=" * 50)

    # 1. 检查API密钥
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 请先设置环境变量 DEEPSEEK_API_KEY")
        print("\n设置方法:")
        print("  Windows: set DEEPSEEK_API_KEY=你的密钥")
        print("  Mac/Linux: export DEEPSEEK_API_KEY='你的密钥'")
        return

    # 2. 初始化处理器
    try:
        handler = DeepSeekHandler()
        matcher = TemplateMatcher()
        generator = VulnerabilityGenerator()
        print("✅ 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 3. 获取用户输入
    print("\n📝 请输入CTF需求描述 (输入空行结束，输入q退出):")

    while True:
        lines = []
        while True:
            try:
                line = input()
                if line.lower() == 'q':
                    print("\n👋 退出程序")
                    return
                if line == "":
                    break
                lines.append(line)
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 退出程序")
                return

        if not lines:
            print("❌ 需求不能为空，请重新输入")
            continue

        requirement = "\n".join(lines)

        # 第一步. 生成JSON
        print("\n" + "=" * 40)
        print("📝 第1步: 生成JSON配置")
        print("=" * 40)
        print("\n🚀 正在调用DeepSeek生成JSON...")

        try:
            result = handler.generate_json(requirement)

            #  显示结果
            print("\n📊 生成的JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            #  保存文件
            json_path = handler.save_json(result)
            print(f"\n✅ JSON已保存到: {json_path}")

        except Exception as e:
            print(f"❌ 生成失败: {e}")
            continue

        # 第二步. 匹配模板
        print("\n" + "=" * 40)
        print("🔍 第2步: 匹配instances模板")
        print("=" * 40)

        try:
            template_info = matcher.match_template(result)

            if template_info:
                print(f"✅ 匹配到模板: {template_info['template_name']}")
                print(f"📁 模板路径: {template_info['template_path']}")
            else:
                print("❌ 未找到匹配的模板")
                continue

        except Exception as e:
            print(f"❌ 模板匹配失败: {e}")
            continue

        # 第三步. 生成漏洞代码
        print("\n" + "=" * 40)
        print("🔧 第3步: 生成漏洞代码")
        print("=" * 40)

        try:
            # 接收返回值
            code_path = generator.generate_from_task(result, template_info)
            print(f"✅ 漏洞代码已生成: {code_path}")

            # 列出生成的文件
            print("\n📁 生成的文件:")
            for file in sorted(os.listdir(code_path)):
                file_path = os.path.join(code_path, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  - {file} ({size} bytes)")

        except Exception as e:
            print(f"❌ 代码生成失败: {e}")
            continue

        #完成
        print("\n" + "=" * 40)
        print("✅ 完整流程执行成功!")
        print("=" * 40)
        print(f"📄 JSON配置: {json_path}")
        print(f"📁 漏洞代码: {code_path}")
        print(f"📊 任务ID: {result.get('task_id', 'unknown')}")

        print("\n" + "-" * 40)
        print("📝 可以输入下一个需求，或输入 q 退出")


if __name__ == "__main__":
    main()