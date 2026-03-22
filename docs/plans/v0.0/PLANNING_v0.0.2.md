# PLANNING_v0.0.2

> 版本计划：组件通信解耦重构 + 集成专项

---

## 1. Context（背景）

**所属里程碑**：v0.0

**版本目标**：消除 MainWindow 与子组件之间的高耦合，统一使用 EventBus 通信；完成 `image_crop/` 原型能力并入 `agp/core`

**关联需求**：
- 需求来源：PLANNING_V2 集成专项（P0/P1）+ 模块7 组件通信解耦

---

## 2. Goals（目标）

### 核心目标
1. 引入 EventBus 事件总线，实现组件间解耦通信
2. 移除 Widget 中的冗余 `main_window` 引用
3. 使用字典映射替代 if-elif 功能分发
4. 缩略图系统拆分为独立模块
5. 统一包导入路径，确保 `python -m agp.main` 可稳定启动
6. 将 `image_crop/` 可复用能力收敛到 `agp/core`

### 验收标准
- [x] `python -c "import agp.main"` 成功
- [x] `python -m agp.main` 可启动主界面且不报导入异常
- [x] 四功能按钮可完成一次最小闭环执行
- [x] `python -m pytest -q` 可完成收集并通过主项目基线
- [x] Widget 构造函数无 `main_window` 参数

---

## 3. Tasks（任务列表）

### 模块A：集成专项 P0（阻断修复）

| 任务ID | 任务名称 | 任务描述 | 优先级 | 依赖 | 状态 |
|--------|----------|----------|--------|------|------|
| T001 | 统一包导入路径 | 统一为 `agp.*`，禁止 `from utils...`、`from core...` 混用 | P0 | 无 | ✅ |
| T002 | 移除 sys.path.insert | 移除业务代码中的 `sys.path.insert` 依赖 | P0 | T001 | ✅ |
| T003 | 统一 UI 与 core 调用契约 | 入参类型、方法名、返回结构一致 | P0 | T001 | ✅ |
| T004 | 修复四功能主链路 | 角度检测/校正、图片切分/压缩可执行 | P0 | T002, T003 | ✅ |
| T005 | 修复图片切分调用断裂 | `crop`/`split_by_count` 签名一致 | P0 | T003 | ✅ |

### 模块B：集成专项 P1（并入与稳定性）

| 任务ID | 任务名称 | 任务描述 | 优先级 | 依赖 | 状态 |
|--------|----------|----------|--------|------|------|
| T006 | image_crop 能力收敛 | 将 `image_crop/` 可复用能力收敛到 `agp/core` | P1 | T004 | ✅ |
| T007 | 建立最小测试门禁 | 导入启动测试 + 四功能 smoke test | P1 | T004 | ✅ |
| T008 | 清理实验脚本 | 隔离实验脚本，避免影响主项目 `pytest` 基线 | P1 | T007 | ✅ |
| T009 | 文档口径对齐 | README 与 plan/ 口径一致 | P2 | T004 | ✅ |

### 模块C：EventBus 事件总线

| 任务ID | 任务名称 | 任务描述 | 优先级 | 依赖 | 状态 |
|--------|----------|----------|--------|------|------|
| T010 | 创建 EventBus | `ui/event_bus.py`，全局 QObject + Signal 单例 | P0 | 无 | ✅ |
| T011 | 定义标准信号 | image_selected/loaded/changed、pil_image_changed、function_triggered、result_ready、status_updated、directory_loaded、image_info_requested | P0 | T010 | ✅ |
| T012 | MainWindow 接入 EventBus | connect_events() 替代直接信号连接 | P0 | T010 | ✅ |

### 模块D：Widget 解耦

| 任务ID | 任务名称 | 任务描述 | 优先级 | 依赖 | 状态 |
|--------|----------|----------|--------|------|------|
| T013 | 移除冗余 main_window 引用 | DirectoryPreviewWidget/FunctionPanelWidget/ImagePreviewWidget/ResultDisplayWidget 构造函数移除 `main_window` 参数 | P0 | T012 | ✅ |
| T014 | ImagePreview 解耦 | `log_image_info` 改为发出 `image_info_requested` 信号 | P1 | T013 | ✅ |

### 模块E：功能分发重构

| 任务ID | 任务名称 | 任务描述 | 优先级 | 依赖 | 状态 |
|--------|----------|----------|--------|------|------|
| T015 | FUNCTION_MAP 字典映射 | 替代 `on_function_triggered` 中的 if-elif 分发 | P1 | T012 | ✅ |
| T016 | 统一结果处理 | `_handle_function_result` 通过 EventBus 广播 `result_ready` | P1 | T015 | ✅ |

### 模块F：缩略图系统拆分

| 任务ID | 任务名称 | 任务描述 | 优先级 | 依赖 | 状态 |
|--------|----------|----------|--------|------|------|
| T017 | 提取 ThumbnailItem | 独立缩略图项组件，支持延迟加载 | P2 | T013 | ✅ |
| T018 | 提取 ThumbnailLoader | 独立目录扫描 + 懒加载调度逻辑 | P2 | T017 | ✅ |

---

## 4. Progress（进度）

**完成情况**：
- 总任务数：18
- 已完成：18
- 进行中：0
- 待开始：0

**时间线**：
- 开始日期：2026-03-13
- 预计完成：2026-03-15
- 实际完成：2026-03-15

---

## 5. Notes（备注）

### 技术决策
- EventBus 基于 QObject + Signal 实现，全局单例模式
- 功能分发使用 `FUNCTION_MAP` 字典映射，新增功能只需添加一行
- 缩略图系统从 `directory_preview.py` 拆分为 `thumbnail_item.py` + `thumbnail_loader.py`

### 风险提示
- 旧面板文件（angle_detect.py、angle_correct.py、image_crop.py、image_compress.py）仍保留在 `ui/` 目录，代码已写好但未接入主窗口，需在后续版本决定去留

### 变更记录
- 2026-03-15：v0.0.2 完成，所有 18 项任务已完成
