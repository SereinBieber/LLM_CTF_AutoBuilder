# LLM-Driven CTF Environment Auto-Builder
大模型驱动的轻量化 CTF 环境自动化构建系统

## 项目简介
本项目旨在利用大语言模型（LLM）理解自然语言需求，自动化构建、部署并验证 CTF 靶场环境。
核心技术对标申报书 **1.2.3.1 参数化对象分层设计**。

## 目录结构
- `schema/`: 全局通信协议 (JSON Schema)
- `llm_parser/`: 需求分析与参数提取 (LLM Agent)
- `builder/`: 镜像构建与容器编排 (Docker Control)
- `validator/`: 自动化验证与动态攻防 (Verify Agent)
- `templates/`: 标准化环境模板库