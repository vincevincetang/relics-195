# 中国禁止出国（境）展览文物 · 国宝档案

195件（组）禁止出境展览文物 + 78件特辑文物 的静态展示页面。

## 内容结构

- **relics_data.py** — 195件/组禁出文物数据（含 image_url、baike_url）
- **relics_special.py** — 特辑文物数据（78件，含补遗、海外遗珍、科技器物等）
- **generate_html.py** — HTML 生成脚本
- **index.html** — 生成的静态页面（可直接浏览器打开）
- **relics-195-data.json** — 195件文物 JSON 导出
- **relics_special_export.json** — 特辑文物 JSON 导出

## 使用

```bash
python3 generate_html.py
```

直接打开 `index.html` 即可浏览。
