# 中国禁止出国（境）展览文物项目 · Code Wiki

> 一个以 Python 为核心、HTML/CSS/JavaScript 为展示层的静态文物档案项目。包含 195 件官方禁出境文物（3 批）及 78 件"特辑"补充文物的完整结构化数据，并提供 LLM 多维评分与地理可视化展示。

---

## 1. 项目总览

| 维度 | 内容 |
|------|------|
| 项目目标 | 整理、展示中国禁止出国（境）展览文物的完整档案；使用 LLM 对文物进行多维价值评分并可视化展示 |
| 核心组成 | ① Python 数据模块 `relics_data.py` / `relics_special.py` <br> ② Python 静态页生成器 `generate_html.py` <br> ③ LLM 多维评分脚本 `rank_relics_v2.py` <br> ④ HTML/CSS/JS 展示页面 `index.html` <br> ⑤ 地理数据 `china.json` |
| 语言/框架 | Python 3.x（标准库 + `requests`），前端 HTML5 + CSS3 + 原生 JavaScript，ECharts 地图 |
| 依赖项 | `requests`（LLM 评分时使用）；`ECharts 5.5.0`（通过 CDN 加载，无需安装） |
| 代码规模 | 核心约 1400 行 Python + 约 1200 行 HTML/CSS/JS；文物数据通过字典/列表常量定义 |
| 数据规模 | 195 件禁出境文物（约 250 KB Python / JSON）+ 78 件特辑文物 |
| 典型运行流程 | 编辑 Python 数据文件 → 运行 `python3 generate_html.py` → 浏览器打开 `index.html` |

---

## 2. 目录结构与文件职责

```
/workspace
├── README.md                    # 项目使用说明（简短版）
├── relics_data.py              # 195 件禁出境文物数据（核心数据源 #1）
├── relics_special.py           # 78 件"未收录特辑"文物数据（核心数据源 #2）
├── generate_html.py            # HTML 页面生成脚本（核心构建脚本）
├── rank_relics_v2.py           # LLM 多维价值评分脚本（可选）
├── index.html                  # 生成的静态页面（主产物）
├── china.json                  # 中国地图 GeoJSON（ECharts 使用）
├── relics-195-data.json        # 195 件文物 JSON 导出（产物）
├── relics_special_export.json  # 特辑文物 JSON 导出（产物）
├── relics_rejected.json        # 被排除/未通过校验的文物记录（产物）
├── rank_output/                # LLM 评分结果输出目录
│   ├── scores_special.json     # 特辑文物评分缓存（多次评分的中间数据）
│   ├── avg_special.json        # 特辑文物平均加权总分（最终展示数据）
│   └── avg_195.json            # 195 件文物平均加权总分（最终展示数据）
├── .gitignore                  # 忽略临时/IDE 文件
├── add_museum.py               # 工具：批量新增博物馆字段
├── check_all_baidu.py          # 工具：检查百度百科链接有效性
├── fetch_images.py             # 工具：批量抓取文物图片
├── fetch_commons.py            # 工具：从 Wikimedia Commons 获取图片
├── fetch_last.py / fetch_remain.py / replace_kimi_images.py  # 图片补全/替换工具
└── baidu_batch_check.sh        # Shell 工具：批量校验百度百科链接
```

---

## 3. 模块设计与职责划分

### 3.1 数据层（Data Module）

| 文件 | 核心变量 | 数据结构 | 主要字段 |
|------|---------|---------|---------|
| `relics_data.py` | `relics` (list) | 列表，按"第一批 → 第二批 → 第三批"顺序拼接的字典元素 | `name`, `era`, `source`, `owner`, `desc`, `museum`, `image_url`, `baike_url`, `batch`（可选）, `no`（可选，1~195） |
| `relics_special.py` | `relics_special` (list) | 列表，按文物编号顺序的字典元素 | 与 `relics` 基本一致，但 `no` 为特辑独立编号（1~78） |

**单条文物记录示例**：
```python
{
    "name": "后母戊鼎",
    "era": "商后期·武丁至祖甲时期（约前13世纪-前12世纪）",
    "source": "1939 年河南省安阳市武官村出土。商王武丁之子祖庚或祖甲为祭祀母亲妇妌（庙号'戊'）而铸造……",
    "owner": "商王武丁之子祖庚或祖甲（为祭祀母亲妇妌铸造）",
    "desc": "旧称司母戊鼎，重达 832.84 千克，高 133 厘米，是迄今为止中国出土的最大、最重的青铜礼器……",
    "museum": "中国国家博物馆",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/HouMuWuDingFullView.jpg/960px-HouMuWuDingFullView.jpg",
    "baike_url": "https://baike.baidu.com/item/%E5%90%8E%E6%AF%8D%E6%88%8A%E9%BC%8E",
    "batch": "第一批（2002 年）",
    "no": 3
}
```

**数据规范**：
- `name`：唯一键（生成 HTML 时使用 data-name 匹配）；
- `era`：时代/年代，以"文化类型/王朝（约前年）"格式书写；
- `source`：出土信息 + 流传史（含保护、捐赠、流转海外等）；
- `owner`：文物的制造者/使用者/墓葬主人；
- `desc`：文物体量、材质、工艺、艺术/历史价值描述；
- `museum`：现藏单位（多馆用 "/" 分隔，如"上海博物馆/山西博物院"）；
- `image_url`：图片资源（优先维基共享资源 Wikimedia Commons）；
- `baike_url`：百度百科条目链接（汉字需 URL 编码）。

---

### 3.2 HTML 生成器（`generate_html.py`）

**文件路径**：[generate_html.py](file:///workspace/generate_html.py)

| 核心元素 | 类型 / 职责 |
|---------|------------|
| `traditional_colors` (list) | 20 种中国传统颜色（十六进制），用于图片加载失败时的占位卡片配色。循环使用，对每个文物按索引取模 |
| `ROTATED_IMAGES` (dict) | 关键字 → 旋转角度（`90deg` / `-90deg`），针对部分竖轴字画图片的横向旋转修复 |
| `LOCATION_COORDS` (dict) | 地理坐标映射表：键为"省名 / 市名 / 县名 / 博物馆名"，值为 `[lon, lat]` 二维数组。内含约 200 条映射（按考古遗址、馆藏机构、行政区划组织），用于地图可视化 |
| `get_image_html(relic, index)` | 函数。读取 `relic['image_url']`，生成 `<a><img></a>` 片段；`onerror` 失败时自动隐藏图片并显示占位卡片 |
| `get_placeholder_html(name, era, index)` | 函数。生成占位卡片，使用首汉字 + 时代信息作为视觉回退；背景与图标颜色来自 `traditional_colors[index % 20]` |
| `extract_origin(relic)` | 函数。从 `source` 文本中提取出土/来源地坐标。策略：先在首句匹配；若首句含"现藏/馆藏"等与出土地不符，则再搜索后续文本（并允许限定在"出土"词附近 40 字符）。使用 `LOCATION_COORDS` 中名称最长者优先匹配 |
| `extract_museum_coords(museum_str)` | 函数。从 museum 字段字符串中按 `/` 切分，取第一个可在 `LOCATION_COORDS` 中找到的实体坐标 |
| `aggregate(data_list)` | 函数。将 `[{name, src, x, y}, ...]` 按经纬度聚合（同坐标合并），输出为 ECharts 可消费格式：`{names, count, srcs, muses, value:[lon, lat, count]}` |
| `generate_html()` | 主函数。① 构造 HTML 骨架（CSS 样式、ECharts 脚本）；② 循环渲染 195 件文物卡片；③ 构造 origin/museum 两组地理数据并嵌入 JSON；④ 渲染特辑卡片；⑤ 写入 `index.html` 并打印统计 |

**页面组成结构（HTML）**：

```
+----------------------- <html lang="zh-CN"> ------------------------+
|  <head>  → meta / Google Fonts Noto Serif SC + Noto Sans SC / ECharts |
|         → 嵌入 CSS（约 520 行，含配色、卡片、地图、响应式）              |
+---------------------------------------------------------------------+
|  <body>                                                              |
|   ├── <header class="header"> 标题与统计（64 / 37 / 94 / 195）       |
|   ├── <div class="controls"> 搜索框 + 批次过滤按钮 + 地图按钮 + 特辑按钮 |
|   ├── <section id="mapSection" class="map-section collapsed"> 地图区 |
|   │    └── <div id="chinaMap"> 600px 高 ECharts 容器                  |
|   ├── <main class="container">                                        |
|   │    └── <div id="relicsGrid" class="relics-grid"> 195 张卡片网格   |
|   │          └── <article class="relic-card"> 逐件文物卡片             |
|   │                   ├── 图片区（image_url / placeholder 备选）       |
|   │                   ├── 标题（name + 百度百科链接）/ era 标签         |
|   │                   ├── source / owner 信息                          |
|   │                   ├── desc 描述（自动截断）                         |
|   │                   └── museum 现藏 + no 序号                         |
|   ├── <section id="specialSection" class="special-section"> 特辑区     |
|   │    └── 78 张特辑卡片（同上文，但采用暗金色调 / 独立序号系统）        |
|   ├── <script>                                                         |
|   │    ├── originData / museumData JSON 常量嵌入                         |
|   │    ├── fetch('china.json') + echarts.registerMap('china', ...)     |
|   │    ├── renderMap(data) → scatter + geo 配置                          |
|   │    ├── switchMap(idx) → 切换"来源地/馆藏地"视图                      |
|   │    ├── showSpecial() / showMain() / toggleMapSection()             |
|   │    └── 搜索 + 批次过滤交互（纯原生 JS，无框架）                       |
|   └── <footer> 数据来源声明与参考链接                                   |
+---------------------------------------------------------------------+
```

**样式系统（CSS）要点**：
- 采用 CSS 变量：`--primary:#8B4513`, `--accent-gold:#D4A574`, `--accent-red:#C45C48`；
- `.relics-grid` 使用 `auto-fill minmax(340px, 1fr)`，响应式；
- `.relic-card` 含 `fadeIn` 动画与 hover 上浮效果；
- `.map-section.collapsed` 通过 `max-height:0 + opacity:0` 平滑折叠；
- `.special-tab-btn` 使用暗金色 `#b8860b` 以与主列表视觉区分。

---

### 3.3 LLM 多维价值评分器（`rank_relics_v2.py`）

**文件路径**：[rank_relics_v2.py](file:///workspace/rank_relics_v2.py)

**设计目标**：使用大语言模型对每件文物在四个维度独立打分，然后按加权公式得出总分并排序。

**四个评分维度（及默认权重）**：

| 维度 | 权重 | 含义 |
|------|------|------|
| 历史价值 | 0.45 | 信息稀缺性、年代重要性、铭文及文献价值 |
| 稀缺性 | 0.23 | 同类文物存世量、品类代表性、孤本性质 |
| 艺术/工艺水准 | 0.22 | 同品类中排名、技法精湛程度、体量与叙事 |
| 文明符号力 | 0.10 | 跨圈知名度（国民度 / 国际认知） |

**核心函数清单**：

| 函数 | 签名与职责 |
|------|------------|
| `load_relics(path, var_name)` | `(str, str) → list[dict]`。通过 `exec()` 加载 Python 数据模块（可读取 `relics` 或 `relics_special` 变量）。允许在不解析数据结构的情况下复用同一加载器 |
| `make_description(item)` | `(dict) → str`。从一条文物数据生成发送给 LLM 的单行描述：`name \| era \| museum \n 来源: ... \n 描述: ...` |
| `extract_json(text)` | `(str) → str`。从 LLM 原始输出中正则匹配出第一个 `[...]` JSON 数组片段（因部分模型会混入说明文字） |
| `llm_score_group(group_indices, descriptions, llm_config)` | `(list[int], list[str], dict) → dict[int→dict]`。**核心函数**：将一组文物（默认 20 件）的描述一次性发给 LLM，并解析返回的 JSON 得到每件文物的四维分。失败时自动重试最多 3 次；仍失败则进入交互模式（stdin 手动输入）。**发送方式**：POST `{base_url}/chat/completions`，body 含 `model`、`messages`（system+user）、`temperature:0`、`max_tokens:2000` |
| `load_cache()` / `save_cache(cache)` | 读写 `rank_output/scores_*.json` 文件，实现增量评分。**缓存格式**：`{"run_0": {"round_0": {"idx": {"历史":xx, ...}}, ...}, "run_1": {...}}` |
| `migrate_cache(cache)` | 兼容旧版本：若缓存顶层为 `round_X` 键，则自动包裹为 `run_0 → round_X` 结构 |
| `compute_run_scores(run_data, n)` | `(dict, int) → dict`。计算单次 run 中每件文物的 round 维度平均分（缺省回退 5.0 分） |
| `fmt(val)` / `print_ranking(avg_scores, relics, ...)` | 格式化打印并写入 `avg_special.json` 或 `avg_195.json`（按数据源） |
| `do_run(run_num, force, resume, cache, relics, descriptions, llm_config)` | 一次完整评分流程：随机分组 → 组内 LLM 评分 → 保存缓存 → 计算并输出结果。支持 `--force`（忽略缓存重做）、`--resume`（仅对未完成组补齐） |
| `do_aggregate(cache, relics)` | 聚合模式：读取所有 `run_X` 的结果进行跨 run 汇总，适合多次 LLM 调用后求综合加权分 |
| `main()` | CLI 入口。参数：`--aggregate / --force / --resume / --run N / --source special|195 / --rounds N`。读取环境变量 `LLM_API_KEY`, `LLM_BASE_URL`（默认 `https://api.deepseek.com`）, `LLM_MODEL`（默认 `deepseek-chat`） |

**LLM System Prompt**：
```
你是中国文物专家。对以下每件文物在四个维度上分别评分（一位小数）……
【历史价值】……
【稀缺性】……
【艺术/工艺水准】……
【文明符号力】……
回复严格JSON格式数组：
[{"no":1,"历史":80.0,"稀缺":70.5,"艺术":90.8,"符号":80.2}]
```

**关键流程图示**：
```
      [ relics_data.py / relics_special.py ]
                   │
                   ▼ load_relics()
      [ List[Dict] 列表 · 描述规范化 make_description() ]
                   │
                   ▼ llm_score_group() 批次调用
      ┌──────────────────────────────────────────┐
      │  POST {base_url}/chat/completions        │
      │  body: system + user（20 件文物描述）    │
      │  temperature=0 · max_tokens=2000         │
      └───────────────┬──────────────────────────┘
                      │ JSON 数组响应
                      ▼ extract_json() + json.loads()
      [ scores_special.json (run_X → round_Y → idx → dims) ]
                   │
                   ▼ compute_run_scores() + print_ranking()
      [ avg_special.json / avg_195.json · 按加权总分排序 ]
```

**CLI 用法**：
```bash
# 1) 对特辑文物做一次 run，30 轮评分取平均（默认）
LLM_API_KEY=sk-xxx python3 rank_relics_v2.py --source special --rounds 30

# 2) 对 195 件官方文物做评分
LLM_API_KEY=sk-xxx python3 rank_relics_v2.py --source 195

# 3) 多次调用后聚合
python3 rank_relics_v2.py --source special --aggregate

# 4) 强制重新评分（不使用缓存）
python3 rank_relics_v2.py --source special --force
```

---

### 3.4 前端交互（`index.html`）

**文件路径**：[index.html](file:///workspace/index.html)

页面构建在**无框架**方案之上：

| 交互能力 | 实现方式 |
|---------|---------|
| 搜索 | `#searchInput` 监听 `input` 事件，按 `data-name / data-era / data-owner / data-museum` 属性做不区分大小写子串匹配；对特辑卡片按 `textContent` 匹配 |
| 批次过滤 | `data-batch="第一批"` 等属性选择器，切换 CSS `.hidden` 类 |
| 地理视图切换 | ECharts `scatter + geo` 双数据集（来源地/馆藏地），通过 `switchMap(idx)` 替换渲染 |
| 特辑视图切换 | `showSpecial()` 隐藏主列表、显示特辑列表并切换 `--special-tab-btn.active`；`location.hash = "special"` 支持刷新后恢复 |
| 地图折叠 | 点击"🗺 地理分布"按钮切换 `.collapsed` 类，并在展开后 setTimeout 触发 `chart.resize()` 防止尺寸初始化异常 |
| 图片容错 | 每个 `<img>` 挂载 `onerror="this.style.display='none'; this.parentElement.nextElementSibling.style.display='flex';"`，图片失效时展示占位卡 |
| 响应式 | `@media (max-width:768px)` 覆盖移动版样式 |

---

## 4. 运行方式与环境要求

### 4.1 运行环境

| 项目 | 版本要求 |
|------|---------|
| Python | 3.7+（使用 `json`、`requests`、`argparse`、`exec`、文件 I/O） |
| 浏览器 | 现代浏览器（支持 ES2015 + CSS Grid + Fetch API） |
| 操作系统 | Linux / macOS / Windows 均可 |

### 4.2 依赖安装

```bash
# 仅在需要 LLM 评分时需要 requests
pip install requests
```

前端依赖通过 CDN 加载，无需安装：
- `Noto Serif SC / Noto Sans SC`（Google Fonts）
- `ECharts 5.5.0`（BootCDN / cdnjs）

### 4.3 构建与查看主页面

```bash
cd /workspace
python3 generate_html.py
# 产出：index.html
# 直接用浏览器打开 index.html 即可浏览
```

> ⚠️ **注意**：`china.json` 与 `index.html` 需在同一目录（fetch 同源加载）。如果用 `file://` 协议打开地图加载失败，请使用本地静态服务器：
```bash
# 任选其一
python3 -m http.server 8000
# 然后访问 http://localhost:8000/
```

### 4.4 调用 LLM 评分（可选）

```bash
# 设置 API 环境变量
export LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxx
export LLM_BASE_URL=https://api.deepseek.com   # 或兼容 OpenAI 协议的其他端点
export LLM_MODEL=deepseek-chat

# 对特辑文物评分（默认 30 轮）
python3 rank_relics_v2.py --source special --rounds 30

# 对 195 件官方文物评分
python3 rank_relics_v2.py --source 195 --rounds 30

# 结果
#   rank_output/scores_*.json  —— 中间缓存（增量使用）
#   rank_output/avg_special.json / avg_195.json —— 最终排名数据
```

### 4.5 图片资源维护（可选辅助脚本）

```bash
# 校验百度百科链接
bash baidu_batch_check.sh
python3 check_all_baidu.py

# 抓取 Wikimedia Commons 图片
python3 fetch_commons.py

# 批量获取/补全图片
python3 fetch_images.py
python3 fetch_last.py
python3 fetch_remain.py
python3 replace_kimi_images.py

# 新增/修正博物馆字段
python3 add_museum.py
```

---

## 5. 依赖关系与数据流

### 5.1 模块依赖图

```
relics_data.py ─────┐
                    ├─► generate_html.py ──► index.html (静态站点)
relics_special.py ──┘              ▲
                                    │
china.json ─────────────────────────┘（前端 ECharts 运行时读取）

relics_data.py ─────┐
                    ├─► rank_relics_v2.py ──► rank_output/*.json
relics_special.py ──┘

# 工具脚本（可选）
check_all_baidu.py → 验证 baike_url 是否有效
fetch_commons.py / fetch_images.py / fetch_last.py / fetch_remain.py
    → 填充/修正 image_url 字段
add_museum.py → 修正 museum 字段
```

### 5.2 关键数据流说明

1. **数据写入路径**：人工编辑 `relics_data.py` / `relics_special.py` → Python 列表常量
2. **HTML 构建路径**：`generate_html.py` 通过 `from relics_data import relics` / `from relics_special import relics_special` 读取 → 生成 DOM 节点 + 嵌入 JSON 数据 → 写入 `index.html`
3. **地理数据路径**：`LOCATION_COORDS`（常量 dict）→ `extract_origin()` / `extract_museum_coords()` → `aggregate()` → `originData` / `museumData` 两个 JS 常量 → ECharts scatter
4. **LLM 评分路径**：`load_relics()` → `make_description()` → `llm_score_group()`（HTTP JSON）→ `save_cache()` → `compute_run_scores()` → `print_ranking()` → 写 `avg_special.json`

---

## 6. 常见问题与维护建议

- **新增一件文物**：在 `relics_data.py` 末尾添加 dict（保证字段完整，尤其 `image_url` 与 `baike_url`）；然后执行 `python3 generate_html.py` 重新生成页面。
- **图片加载失败**：检查 `image_url` 是否可直链访问（注意防盗链如百度图片可能返回 403）；优先使用维基共享资源（upload.wikimedia.org）。
- **地理坐标错误**：在 `generate_html.py` 的 `LOCATION_COORDS` 中查无此地名时，追加一条 `["地名": [lon, lat]]` 映射即可。
- **LLM 调用失败**：检查 `LLM_API_KEY` 是否有效，或脚本中 `MAX_RETRIES` / `timeout=30` 是否满足网络情况。API 协议需兼容 OpenAI `/chat/completions` 接口。
- **JSON 数据导出**：如需把 Python 源数据转成 JSON 给其他程序使用，可调用：
  ```python
  import json
  from relics_data import relics
  json.dump(relics, open('relics-195-data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
  ```

---

## 7. 文件索引

| 文件 | 路径 | 行数（约） | 类型 |
|------|------|-----------|------|
| 主 README | [README.md](file:///workspace/README.md) | 20 | Markdown |
| 195 件文物数据 | [relics_data.py](file:///workspace/relics_data.py) | 650+ | Python |
| 特辑文物数据 | [relics_special.py](file:///workspace/relics_special.py) | 650+ | Python |
| HTML 生成器 | [generate_html.py](file:///workspace/generate_html.py) | 300+ | Python |
| LLM 多维评分 | [rank_relics_v2.py](file:///workspace/rank_relics_v2.py) | 490 | Python |
| 生成页面 | [index.html](file:///workspace/index.html) | 1200+ | HTML |
| 中国地图 | [china.json](file:///workspace/china.json) | - | GeoJSON |
| 输出目录 | [rank_output](file:///workspace/rank_output) | - | 目录 |
| 忽略文件 | [.gitignore](file:///workspace/.gitignore) | 15 | Git Config |
