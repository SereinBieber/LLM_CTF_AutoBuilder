import sys
import os
import json

# 寻路外挂：定位到真正的项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from llm_parser.deepseek_handler import DeepSeekHandler


def main():
    print("==============================================")
    print("🚀 LLM_CTF_AutoBuilder - 彭丽诚 (AI 大脑) 测试端")
    print("==============================================")

    try:
        handler = DeepSeekHandler()
        print("✅ DeepSeek API 初始化成功！可以开始对话了。\n")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    while True:
        try:
            req = input("📝 请输入出题需求 (输入 'q' 退出) \n👉 ").strip()
            if req.lower() in ['q', 'quit', 'exit']:
                print("👋 测试结束，彭丽诚下班啦。")
                break
            if not req:
                continue

            print("🤖 彭丽诚正在疯狂敲键盘生成 JSON，请稍候...")
            result = handler.generate_json(req)

            if "error" not in result:
                saved_path = handler.save_json(result)
                print(f"🎉 成功！配置已保存至: {saved_path}")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"❌ 生成失败: {result.get('error')}")

        except KeyboardInterrupt:
            print("\n👋 强制退出。")
            break
        except Exception as e:
            print(f"\n❌ 运行错误: {e}")


if __name__ == "__main__":
    main()