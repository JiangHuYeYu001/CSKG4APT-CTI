#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CTINexus 前端改进完整演示
包含：多标签页UI + 完善的错误处理
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
print("     CTINexus × CSKG4APT - 前端改进完整演示")
print("=" * 80)
print("\n🎨 UI改进亮点：")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("1️⃣  多标签页层次化布局")
print("   ├─ 🔍 情报提取：输入、配置、运行、JSON结果")
print("   ├─ 🕸️ 知识图谱：全宽大界面展示（750px × 95%宽度）")
print("   └─ 🎯 威胁归因：预留接口（功能开发中）")
print()
print("2️⃣  科技感视觉设计")
print("   ├─ 标签页按钮：渐变背景 + 发光效果")
print("   ├─ 选中状态：青紫渐变 + 强烈高亮")
print("   ├─ 内容区域：深色背景 + 青色边框")
print("   └─ 淡入动画：流畅的视觉过渡")
print()
print("3️⃣  完善的错误处理系统")
print("   ├─ 6种错误类型自动识别")
print("   │  ├─ 🌐 URL输入错误")
print("   │  ├─ 📄 PDF处理错误")
print("   │  ├─ 🤖 模型调用错误")
print("   │  ├─ 📡 网络连接错误")
print("   │  ├─ ⚠️ 通用错误")
print("   │  └─ 🔧 图谱生成错误（橙色警告）")
print("   ├─ 友好的错误卡片UI")
print("   │  ├─ 大图标 + 清晰标题")
print("   │  ├─ 深色背景错误详情框")
print("   │  └─ 针对性解决建议")
print("   └─ 10+错误代码定义")
print("      ├─ [input_missing] - 未提供输入")
print("      ├─ [url_invalid] - URL格式无效")
print("      ├─ [pdf_empty] - PDF无文本")
print("      └─ [processing_failed] - 处理失败")
print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("\n📊 效果对比：")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("  图谱显示面积：   2/3宽度  →  全宽（+50%）")
print("  屏幕利用率：     60%      →  95%（+58%）")
print("  视觉层次：       单页扁平  →  多标签立体")
print("  错误处理：       简单文本  →  友好卡片UI")
print("  专业感：         中等      →  演示级别")
print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("\n🧪 测试建议：")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("✅ 正常流程：")
print("   1. 在"情报提取"标签页输入URL或上传PDF")
print("   2. 选择模型并点击"运行"")
print("   3. 查看JSON结果和性能指标")
print("   4. 切换到"知识图谱"标签页查看全宽图谱")
print()
print("⚠️ 错误测试：")
print("   1. 不输入任何内容直接运行 → 触发 [input_missing]")
print("   2. 输入无效URL \"test\" → 触发 [url_invalid]")
print("   3. 上传损坏的PDF → 触发 [pdf_*]")
print("   4. 使用无效API密钥 → 触发 [processing_failed]")
print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("\n🚀 正在启动 Gradio 界面...")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("   浏览器将自动打开: http://127.0.0.1:7860")
print()
print("   提示：请在浏览器中体验以下功能：")
print("   • 点击不同标签页感受层次化布局")
print("   • 查看"知识图谱"标签页的全宽大界面")
print("   • 尝试触发错误查看友好的错误提示")
print()
print("=" * 80)
print()

# 启动应用
from ctinexus.app import main

if __name__ == "__main__":
    main()
