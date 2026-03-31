#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试CSKG4APT前端错误处理功能
"""

import sys
from pathlib import Path

# 设置UTF-8输出编码
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 添加项目路径
project_root = Path(__file__).parent / "cskg4apt"
sys.path.insert(0, str(project_root.parent))

print("=" * 80)
print("CSKG4APT 前端错误处理测试")
print("=" * 80)
print("\n新增功能:")
print("1. 6种错误类型自动识别（URL、PDF、模型、网络、通用、图谱）")
print("2. 友好的错误卡片UI（图标+标题+详情+建议）")
print("3. 10+错误代码定义（便于追踪）")
print("4. 针对性解决建议（帮助用户快速定位问题）")
print("5. 分层错误展示（错误/建议/状态）")
print("\n测试方法:")
print("1. 启动应用后，尝试以下操作：")
print("   - 不输入任何内容，直接点击\"运行\" → 触发 [input_missing]")
print("   - 输入无效URL \"test\" → 触发 [url_invalid]")
print("   - 上传损坏的PDF文件 → 触发 [pdf_*]")
print("   - 使用无效的API密钥 → 触发 [processing_failed]")
print("2. 观察知识图谱标签页的错误展示效果")
print("3. 查看指标表格区域的错误状态提示")
print("\n" + "=" * 80)
print("正在启动Gradio界面...")
print("浏览器将自动打开: http://127.0.0.1:7860")
print("=" * 80 + "\n")

# 启动应用
from cskg4apt.app import main

if __name__ == "__main__":
    main()
