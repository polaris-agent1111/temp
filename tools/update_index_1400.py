from pathlib import Path

index_file = Path("hourly/INDEX.md")
content = index_file.read_text("utf-8")

# 更新头部时间
content = content.replace(
    "最后更新：2026-11-07 09:00 (Asia/Shanghai)\n最近报告：[2026-11-07_0900.md](2026-11-07_0900.md)",
    "最后更新：2026-11-07 14:00 (Asia/Shanghai)\n最近报告：[2026-11-07_1400.md](2026-11-07_1400.md)"
).replace(
    "最后更新：2026-11-07 09:00 (Asia/Shanghai)\r\n最近报告：[2026-11-07_0900.md](2026-11-07_0900.md)",
    "最后更新：2026-11-07 14:00 (Asia/Shanghai)\r\n最近报告：[2026-11-07_1400.md](2026-11-07_1400.md)"
)

# 追加末尾历史报告
new_entry = "- [2026-11-07 13:00–14:00](2026-11-07_1400.md)：**下午科研攻坚与逐发闭环打榜控制器全面上线**；贯彻「打一发看一发」最高指示，独立研发 `tools/sequential_adaptive_1108.py` 并通过全链路仿真演练；日间逆向对手 Catnet（开环盲打3发停滞119.8s）与大肥鱼（2分半内轰4发耗尽额度停滞122.4s）；zcode 连续交付 0107~0118 共 12 项重负荷数理与系统审计文档，调度守护持续推进\n"

if "2026-11-07_1400.md" not in content.split("## 历史报告")[1]:
    content = content.rstrip() + "\n" + new_entry

index_file.write_text(content, encoding="utf-8")
print("hourly/INDEX.md updated successfully!")
