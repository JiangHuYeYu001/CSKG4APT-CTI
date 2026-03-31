#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSKG4APT with CSKG4APT - 快速启动脚本

测试CSKG4APT集成是否成功
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

print("=" * 70)
print("CSKG4APT × CSKG4APT 融合版本")
print("=" * 70)
print("\n正在启动Gradio界面...")
print("功能特性:")
print("✅ CSKG4APT模式（12实体+7关系约束）")
print("✅ PDF多模态处理")
print("✅ 白盒可解释（原文证据链）")
print("✅ 深色科技主题UI")
print("\n" + "=" * 70)

# 启动应用
from cskg4apt.app import main

if __name__ == "__main__":
    main()
