#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试CTINexus多标签页UI
"""

import sys
from pathlib import Path

# 设置UTF-8输出编码
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 添加项目路径
project_root = Path(__file__).parent / "ctinexus"
sys.path.insert(0, str(project_root.parent))

print("=" * 80)
print("CTINexus × CSKG4APT - 多标签页UI测试")
print("=" * 80)
print("\n新UI特性:")
print("✅ Tab 1: 情报提取 - 输入控制、模型配置、JSON结果")
print("✅ Tab 2: 知识图谱 - 大界面展示实体关系图")
print("✅ Tab 3: 威胁归因 - 预留接口（开发中）")
print("\n视觉改进:")
print("✅ 科技感标签页样式（渐变、发光效果）")
print("✅ 知识图谱全宽显示（更大更清晰）")
print("✅ 层次化布局（专业演示级别）")
print("\n" + "=" * 80)
print("正在启动Gradio界面...")
print("浏览器将自动打开: http://127.0.0.1:7860")
print("=" * 80 + "\n")

# 启动应用
from ctinexus.app import main

if __name__ == "__main__":
    main()
