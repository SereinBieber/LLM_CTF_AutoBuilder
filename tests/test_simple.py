"""
简单测试文件
直接运行这个文件测试功能
"""

import os
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from llm_parser.deepseek_handler import DeepSeekHandler

print("所有环境变量:", list(os.environ.keys()))
print("DEEPSEEK_API_KEY:", os.getenv("DEEPSEEK_API_KEY"))

def main():
    print("=" * 50)
    print("🎯 DeepSeek JSON生成器测试")
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

        # 4. 生成JSON
        print("\n🚀 正在调用DeepSeek生成JSON...")
        try:
            result = handler.generate_json(requirement)

            # 5. 显示结果
            print("\n📊 生成的JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 6. 保存文件
            filepath = handler.save_json(result)
            print(f"\n✅ JSON已保存到: {filepath}")

        except Exception as e:
            print(f"❌ 生成失败: {e}")

        print("\n" + "-" * 40)
        print("📝 可以输入下一个需求，或输入 q 退出")


if __name__ == "__main__":
    import json  # 添加json导入

    main()