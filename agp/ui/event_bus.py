"""
全局事件总线 - 基于 QObject + Signal 的组件间通信机制

所有跨组件通信通过 EventBus 进行，组件之间不直接引用。
使用方式：
    from agp.ui.event_bus import event_bus
    event_bus.image_selected.connect(handler)
    event_bus.image_selected.emit(file_path)
"""

from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """全局事件总线，承载所有跨组件通信的 Signal"""

    # ===== 图片相关 =====
    # 目录预览中图片被选中（file_path: str）
    image_selected = Signal(str)

    # 图片已加载到预览区（file_path: str）
    image_loaded = Signal(str)

    # 预览区图片发生变化（file_path: str，空字符串表示移除）
    image_changed = Signal(str)

    # PIL 图片对象变化（pil_image: object，None 表示移除）
    pil_image_changed = Signal(object)

    # 请求记录图片信息到控制台（file_path: str）
    image_info_requested = Signal(str)

    # ===== 目录相关 =====
    # 目录已加载（dir_path: str）
    directory_loaded = Signal(str)

    # ===== 功能执行相关 =====
    # 功能按钮被点击（func_id: str）
    function_triggered = Signal(str)

    # 功能执行结果就绪（pil_image: object）
    result_ready = Signal(object)

    # ===== 状态相关 =====
    # 状态栏消息更新（message: str）
    status_updated = Signal(str)


# 全局单例
event_bus = EventBus()

