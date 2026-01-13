# ui_code.py
from typing import Tuple, List, TYPE_CHECKING
from matplotlib import pyplot as plt

# 只在类型检查时导入，运行时避免循环引用
if TYPE_CHECKING:
    from search_core import SchemeNode, SchemeShell
else:
    SchemeNode = object
    SchemeShell = object


def explore_plans_ui(
    plans: List[Tuple["SchemeNode", "SchemeShell"]],
    print_scheme_tree,
    base_ergo: float,
    base_recoil_ver: float,
    base_recoil_hor: float,
) -> None:
    """
    用 matplotlib 展示所有方案的散点分布图，并提供交互：
      - 鼠标悬停：气泡显示 cost / 垂直后座 / 水平后座 / 人机 / 改变量 / 预设摘要
      - 鼠标点击：在终端打印该方案的完整配装树
      - 键盘：
          r = Y 轴显示最终垂直后座
          e = Y 轴显示最终人机
      - 终端：可多次输入编号查看方案
    """
    if not plans:
        print("没有任何方案可供显示。")
        return

    shells = [sh for _, sh in plans]

    # 当前 Y 轴模式："recoil" 或 "ergo"
    mode = "recoil"

    # 用于保存当前散点坐标（X/Y）
    xs: List[float] = []
    ys: List[float] = []

    fig, ax = plt.subplots()
    scatter = None  # type: ignore
    annot = None    # 悬停提示用的 annotation，每次 redraw 后重建

    # ========= 坐标计算 =========

    def make_xy():
        """
        根据当前 mode 生成 X/Y 坐标和 Y 轴标签。
        X: total_cost
        Y:
          - recoil 模式：最终水平后座 = base_recoil_hor - total_recoil_benefit
          - ergo   模式：最终人机     = base_ergo       + total_ergo
        """
        nonlocal xs, ys
        xs = [sh.total_cost for sh in shells]

        if mode == "recoil":
            ys = [
                base_recoil_hor - sh.total_recoil_benefit*base_recoil_hor
                for sh in shells
            ]
            y_label = "最终水平后座（越小越好）"
        else:
            ys = [
                base_ergo + sh.total_ergo
                for sh in shells
            ]
            y_label = "最终人机（越大越好）"

        return xs, ys, y_label

    # ========= 重绘函数 =========

    def redraw():
        """
        根据当前 mode 重画整个散点图。
        注意：这里会 ax.clear()，所以需要重新创建 annot。
        """
        nonlocal scatter, xs, ys, annot
        ax.clear()
        xs, ys, y_label = make_xy()
        # picker=5：鼠标附近 5 像素内都算命中，方便悬停/点击
        scatter = ax.scatter(xs, ys, picker=5)
        ax.set_xlabel("总成本（卢布）")
        ax.set_ylabel(y_label)
        ax.set_title("方案散点图（Y: r=后座 / e=人机）")

        # 每次清空后重新创建 annotation，挂到当前坐标轴上
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
            arrowprops=dict(arrowstyle="->")
        )
        annot.set_visible(False)

        fig.canvas.draw_idle()

    # ========= 悬停提示 =========

    def update_annot(idx: int) -> None:
        """
        根据点索引 idx，更新 annotation 的位置和文字。
        """
        nonlocal annot
        if annot is None:
            return
        # 防御：索引越界直接忽略
        if idx < 0 or idx >= len(plans):
            return

        x = xs[idx]
        y = ys[idx]
        annot.xy = (x, y)

        _, sh = plans[idx]

        # 真实值
        final_ergo = base_ergo + sh.total_ergo
        final_recoil_ver = base_recoil_ver - sh.total_recoil_benefit
        # 水平后座我们也用同一 benefit 简单近似
        final_recoil_hor = base_recoil_hor - sh.total_recoil_benefit

        lines = [
            f"方案 #{idx}",
            f"cost:   {sh.total_cost:.0f}",
            f"verR:   {final_recoil_ver:.1f} (Δ {-sh.total_recoil_benefit:+.2f})",
            f"horR:   {final_recoil_hor:.1f}",
            f"ergo:   {final_ergo:.1f} (Δ {sh.total_ergo:+.2f})",
        ]
        origin_name = getattr(sh, "origin_preset_name", None)
        if origin_name:
            preset_info = origin_name.replace("\n", " ")[:40]
            lines.append(preset_info)

        annot.set_text("\n".join(lines))

    def on_hover(event):
        """
        鼠标移动事件：用于悬停显示气泡。
        """
        nonlocal scatter, annot

        # 不在当前坐标轴范围内 → 隐藏 annotation
        if event.inaxes is not ax:
            if annot is not None and annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        if scatter is None or annot is None:
            return

        contains, info = scatter.contains(event)
        if not contains:
            # 鼠标不在点附近 → 隐藏 annotation
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        ind = info.get("ind")
        if ind is None or len(ind) == 0:
            return

        idx = int(ind[0])  # 命中多个点时，取第一个
        update_annot(idx)
        annot.set_visible(True)
        fig.canvas.draw_idle()

    # ========= 点击事件 =========

    def on_pick(event):
        """
        鼠标点击事件：打印被点击方案的详细信息和配装树。
        """
        ind = getattr(event, "ind", None)
        if ind is None or len(ind) == 0:
            return
        idx = int(ind[0])
        if idx < 0 or idx >= len(plans):
            return

        node, sh = plans[idx]

        final_ergo = base_ergo + sh.total_ergo
        final_recoil_ver = base_recoil_ver - sh.total_recoil_benefit * base_recoil_ver
        final_recoil_hor = base_recoil_hor - sh.total_recoil_benefit * base_recoil_hor

        print(f"\n[方案 #{idx}]")
        print(f"初始预设id={sh.origin_preset_id}, 初始预设名称={sh.origin_preset_name}")
        print(
            f"成本={sh.total_cost:.0f}, "
            f"人机={final_ergo:.1f} (变化 {sh.total_ergo:+.2f}), "
            f"垂直后座={final_recoil_ver:.1f} (变化 {-sh.total_recoil_benefit:+.2f}), "
            f"水平后座={final_recoil_hor:.1f}, "
            f"配件数量={len(sh.items)}"
        )
        print_scheme_tree(node)

    # ========= 键盘事件 =========

    def on_key(event):
        """
        键盘事件：
          - r: 切换 Y 轴为最终垂直后座
          - e: 切换 Y 轴为最终人机
        """
        nonlocal mode
        if event.key == "r":
            mode = "recoil"
            print("\n切换到：Y 轴 = 最终垂直后座")
            redraw()
        elif event.key == "e":
            mode = "ergo"
            print("\n切换到：Y 轴 = 最终人机")
            redraw()

    # ========= 绑定事件 & 初次绘制 =========

    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    fig.canvas.mpl_connect("pick_event", on_pick)
    fig.canvas.mpl_connect("key_press_event", on_key)

    redraw()  # 初次绘制

    # 弹出窗口（非阻塞），方便一边看图一边在终端交互
    plt.show(block=False)

    print("\n已打开方案散点图：")
    print("  - 鼠标移动到点上：显示 cost / 垂直后座 / 水平后座 / 人机；")
    print("  - 鼠标点击点：在终端打印该方案的详细配装树；")
    print("  - 图窗口按键：r = Y 轴显示最终垂直后座，e = Y 轴显示最终人机；")
    print("  - 终端也可以直接输入方案编号查看（q 退出）。")

    # ========= 终端交互：多次输入编号查看方案 =========

    while True:
        s = input("\n输入方案编号查看详细方案（q 退出）：").strip().lower()
        if s in ("q", "quit", "exit"):
            break
        if not s:
            continue
        if not s.isdigit():
            print("请输入数字编号，或 q 退出。")
            continue
        idx = int(s)
        if idx < 0 or idx >= len(plans):
            print(f"编号超出范围，有效范围：0 ~ {len(plans)-1}")
            continue

        node, sh = plans[idx]
        final_ergo = base_ergo + sh.total_ergo
        final_recoil_ver = base_recoil_ver -  sh.total_recoil_benefit*base_recoil_ver
        final_recoil_hor = base_recoil_hor - sh.total_recoil_benefit*base_recoil_hor

        print(f"\n[方案 #{idx}]")
        print(f"初始预设id={sh.origin_preset_id}, 初始预设名称={sh.origin_preset_name}")
        print(
            f"成本={sh.total_cost:.0f}, "
            f"人机={final_ergo:.1f} (变化 {sh.total_ergo:+.2f}), "
            f"垂直后座={final_recoil_ver:.1f} (变化 {-sh.total_recoil_benefit:+.2f}), "
            f"水平后座={final_recoil_hor:.1f}, "
            f"配件数量={len(sh.items)}"
        )
        print_scheme_tree(node)
