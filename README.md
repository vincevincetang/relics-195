# 物华天宝 · 何以中国

国家文物局禁止出境展览文物（195 件）+ 特辑重要文物（107 件）的静态展示页面。

## 数据

- **relics_data.py** — 195 件禁出文物（三批：2002/2012/2013）
- **relics_special.py** — 107 件特辑文物（台北故宫、海外藏珍、科技器物等）
- **relics-195.json / relics-195-data.json** — JSON 导出
- **relics_special_export.json** — 特辑 JSON 导出
- **relics_rejected.json** — 被排除的候选文物及理由

每件文物含：名称、年代、时期（period，用于排序）、来源、物主、描述、馆藏、图片链接、百科链接、分类标签。

## 生成

```bash
python3 generate_html.py
# → index.html
```

## 功能

- 195 名单 / 特辑名单 双 tab 切换
- 批次筛选下拉（仅 195 名单）
- 19 类分类筛选 + 清除按钮
- 多字段搜索（名称、年代、物主、说明等）
- 时代 / 默认排序 + 升降序切换
- ECharts 地理分布地图（来源地 / 馆藏地）
- Hash 路由状态保持
- 篆书标题字体
