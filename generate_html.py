# -*- coding: utf-8 -*-
"""
生成中国禁止出国（境）展览文物HTML页面（修正版）
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from relics_data import relics
from relics_special import relics_special

# 中国传统色系背景（用于占位图）
traditional_colors = [
    "#C45C48", "#8B4513", "#D4A574", "#2F4F4F", "#8B0000",
    "#556B2F", "#483D8B", "#800080", "#A0522D", "#6B8E23",
    "#B22222", "#4682B4", "#D2691E", "#CD853F", "#708090",
    "#8B7355", "#9ACD32", "#5F9EA0", "#BC8F8F",     "#A9A9A9",
]

# 百度百科页面名称覆盖（当文物名称与百度百科词条名称不一致时）
ROTATED_IMAGES = {
    "米芾《苕溪诗》卷": "90deg",
    "文彦博《三帖卷》": "-90deg",
}

def get_image_html(relic, index):
    """生成图片HTML，从文物数据的 image_url 字段读取"""
    url = relic.get('image_url', '')
    name = relic['name']
    era = relic['era']
    if url:
        rot = ROTATED_IMAGES.get(name)
        extra = f' style="transform: rotate({rot});"' if rot else ''
        img = f'<img src="{url}" alt="{name}" loading="lazy"{extra} onerror="this.style.display=\'none\';this.parentElement.nextElementSibling.style.display=\'flex\';">'
        return f'<a href="{url}" target="_blank" rel="noopener">{img}</a>'
    return ""

def get_placeholder_html(name, era, index):
    """生成占位图HTML"""
    color = traditional_colors[index % len(traditional_colors)]
    first_char = name[0] if name else "文"
    return f'''<div class="placeholder" style="background: linear-gradient(135deg, {color}22, {color}44); border-color: {color}66;">
        <div class="placeholder-icon" style="color: {color};">{first_char}</div>
        <div class="placeholder-text" style="color: {color}cc;">{era}</div>
    </div>'''

# 中国城市/博物馆坐标映射
LOCATION_COORDS = {
    "北京": [116.4, 39.9], "上海": [121.5, 31.2], "天津": [117.2, 39.1], "重庆": [106.5, 29.6],
    "广州": [113.3, 23.1], "深圳": [114.1, 22.5], "南京": [118.8, 32.1], "杭州": [120.2, 30.3],
    "成都": [104.1, 30.6], "武汉": [114.3, 30.6], "西安": [108.9, 34.3], "郑州": [113.7, 34.8],
    "长沙": [113.0, 28.2], "沈阳": [123.4, 41.8], "济南": [117.0, 36.7], "石家庄": [114.5, 38.0],
    "太原": [112.5, 37.9], "合肥": [117.3, 31.8], "南昌": [115.9, 28.7], "兰州": [103.8, 36.0],
    "西宁": [101.8, 36.6], "贵阳": [106.6, 26.6], "昆明": [102.7, 25.0], "哈尔滨": [126.6, 45.8],
    "长春": [125.3, 43.9], "呼和浩特": [111.8, 40.8], "乌鲁木齐": [87.6, 43.8], "拉萨": [91.1, 29.7],
    "南宁": [108.4, 22.8], "海口": [110.4, 20.0], "福州": [119.3, 26.1], "台北": [121.5, 25.0],
    "香港": [114.2, 22.3], "澳门": [113.5, 22.2],
    # 博物馆
    "中国国家博物馆": [116.395, 39.9036], "故宫博物院": [116.3908, 39.9156], "首都博物馆": [116.3359, 39.9051],
    "中国国家图书馆": [116.32236, 39.94587], "中国社会科学院考古研究所": [116.3905, 39.9915],
    "上海博物馆": [121.470556, 31.230278], "天津博物馆": [117.20153, 39.08606],
    "南京博物院": [118.8201722, 32.0426444],     "南京市博物馆": [118.775, 32.035],
    "苏州博物馆": [120.62056, 31.32472], "扬州博物馆": [119.36639, 32.39278],
    "镇江博物馆": [119.4519, 32.2110], "杭州博物馆": [120.1661, 30.2389],
    "浙江省博物馆": [120.13861, 30.25347], "临安博物馆": [119.7254000, 30.2272694],
    "宁波博物馆": [121.5, 29.9], "山东博物馆": [117.0961333, 36.6588500],
    "山东省博物馆": [117.0, 36.7],     "泰安市博物馆": [117.0876, 36.2001],
    "山东省文物考古研究所": [117.0, 36.7], "山东省文物考古研究院": [117.0, 36.7],
    "济南市博物馆": [117.0, 36.7], "淄博市博物馆": [118.0593, 36.8071],
    "定州市博物馆": [114.9943, 38.5159], "河北博物院": [114.523183, 38.040949],
    "河北省文物研究所": [114.5, 38.0],     "河南省文物考古研究院": [113.6661, 34.7895],
    "河南博物院": [113.6661, 34.7895], "洛阳博物馆": [112.4601, 34.6635],
    "山西省艺术博物馆": [112.55, 37.87], "山西博物院": [112.5264, 37.8650],
    "陕西省考古研究院": [108.9, 34.3], "陕西历史博物馆": [108.95139, 34.22528],
    "西安博物院": [108.936, 34.239],     "西安碑林博物馆": [108.94820, 34.25509],
    "宝鸡青铜器博物院": [107.19388, 34.34758], "宝鸡市文物局": [107.2, 34.4],
    "秦始皇帝陵博物院": [109.25389, 34.38167], "茂陵博物馆": [108.5864, 34.3385],
    "法门寺博物馆": [107.90389, 34.44167], "淳化县博物馆": [108.6, 34.8],
    "甘肃省博物馆": [103.83430, 36.06109], "甘肃省文物考古研究所": [103.83430, 36.06109],
    "敦煌研究院": [94.80139, 40.03639], "青海省博物馆": [101.75417, 36.63029],
    "新疆维吾尔自治区博物馆": [87.58111, 43.81833], "新疆维吾尔自治区文物考古研究所": [87.6, 43.8],
    "四川博物院": [104.02913, 30.66304], "三星堆博物馆": [104.21814, 31.00308],
    "成都金沙遗址博物馆": [104.012602, 30.681183], "绵阳市博物馆": [104.8, 31.5],
    "湖北省博物馆": [114.35889, 30.56389], "湖南博物院": [112.98784, 28.21526],
    "湖南省博物馆": [112.98784, 28.21526], "湖南大学": [113.0, 28.2],
    "江西省博物馆": [115.87698, 28.70926], "江西省文物考古研究院": [115.87698, 28.70926],
    "安徽省文物考古研究所": [117.2149, 31.8040], "安徽博物院": [117.2149, 31.8040],
    "马鞍山市三国朱然家族墓地博物馆": [118.5, 31.7],
    "广东省博物馆": [113.326336, 23.11475], "南越王博物院": [113.25615, 23.14038],
    "福建省博物院": [119.3, 26.1],     "云南省博物馆": [102.75278, 24.95139],
    "贵州省博物馆": [106.63917, 26.65069],     "西藏博物馆": [91.09728, 29.65115],
    "吉林省博物院": [125.433237, 43.768461], "辽宁省博物馆": [123.43028, 41.80083],
    "辽宁省文物考古研究院": [123.4, 41.8],
    "宁夏回族自治区博物馆": [106.3, 38.5],
    "内蒙古博物院": [111.73111, 40.83830],     "广西壮族自治区博物馆": [108.33106, 22.81508],
    "海南省博物馆": [110.37459, 20.01751],
    "荆门市博物馆": [112.2, 31.0], "淄博市博物馆": [118.0593, 36.8071],
    "清华大学": [116.3, 40.0], "明十三陵博物馆": [116.21583, 40.295],
    # 地级市/县
    "安阳市": [114.4, 36.1], "安阳": [114.4, 36.1],
    "洛阳市": [112.5, 34.6], "洛阳": [112.5, 34.6],
    "开封市": [114.3, 34.8], "许昌市": [113.9, 34.0],
    "淅川县": [111.5, 33.2], "新郑市": [113.7, 34.4], "新郑": [113.7, 34.4],
    "辉县": [113.8, 35.5], "辉县市": [113.8, 35.5],
    "临汝县": [112.8, 34.2], "汝州市": [112.8, 34.2],
    "登封市": [113.0, 34.5], "登封": [113.0, 34.5],
    "三门峡市": [111.2, 34.8],
    "宝鸡市": [107.2, 34.4], "宝鸡": [107.2, 34.4],
    "岐山县": [107.6, 34.4], "扶风县": [107.9, 34.4],
    "眉县": [107.8, 34.3],
    "西安市": [108.9, 34.3], "华县": [109.8, 34.5],
    "咸阳市": [108.7, 34.3], "咸阳": [108.7, 34.3],
    "淳化县": [108.6, 34.8],
    "彬县": [108.1, 35.0], "彬州市": [108.1, 35.0],
    "渭南市": [109.5, 34.5],
    "汉中市": [107.0, 33.1],
    "泰安": [117.1, 36.2],
    "寿张县": [115.9, 36.0], "定县": [115.0, 38.5], "定州市": [115.0, 38.5],
    "满城县": [115.3, 38.9], "平山县": [114.2, 38.3],
    "景县": [116.3, 37.7],
    "石楼县": [110.8, 37.0],
    "大同市": [113.3, 40.1],
    "运城": [111.00214, 35.02764],
    "运城市": [111.00214, 35.02764],
    "内蒙古": [111.8, 40.8], "鄂尔多斯": [110.0, 39.6],
    "朝阳": [120.5, 41.6],
    "北票市": [120.8, 41.8],
    "南京市": [118.8, 32.1],
    "苏州市": [120.6, 31.3], "扬州市": [119.4, 32.4],
    "镇江市": [119.4, 32.2], "马鞍山市": [118.5, 31.7],
    "盱眙县": [118.5, 33.0],
    "余杭县": [120.3, 30.4],
    "余姚市": [121.2, 30.1],
    "随县": [113.4, 31.7],
    "随州市": [113.4, 31.7], "江陵": [112.2, 30.0],
    "黄陂县": [114.4, 30.9], "云梦县": [113.7, 31.0],
    "荆门市": [112.2, 31.0],
    "长沙市": [113.0, 28.2],
    "宁乡县": [112.6, 28.3], "衡阳市": [112.6, 26.9],
    "景德镇市": [117.2, 29.3],
    "广州市": [113.3, 23.1],
    "广汉市": [104.3, 31.0],
    "绵阳市": [104.8, 31.5],
    "晋宁区": [102.6, 24.7],
    "武威市": [102.6, 37.9],
    "敦煌市": [94.8, 40.1],
    "乐都县": [102.4, 36.5],
    "大通县": [101.7, 36.9], "都兰县": [98.1, 36.3],
    "宁夏": [106.3, 38.5], "贺兰县": [106.4, 38.6],
    "新疆": [87.6, 43.8], "吐鲁番": [89.2, 42.9],
    "民丰县": [82.7, 37.1], "阿拉尔": [81.3, 40.5],
    "西藏": [91.1, 29.7],
    "翁牛特旗": [119.0, 42.9], "侯马": [111.3, 35.6], "曲沃": [111.5, 35.6],
    "昌平": [116.2, 40.2],
    # 县级→所属地级市坐标（精确到地级市）
    "临汝县": [112.83903, 34.17362], "汝州市": [112.83903, 34.17362],
    "淅川县": [111.49095, 33.13649], "辉县": [113.80276, 35.46378],
    "岐山县": [107.61776, 34.44653], "岐山": [107.61776, 34.44653],
    "扶风县": [107.89219, 34.37844],
    "眉县": [107.76508, 34.27795],
    "临潼": [109.21428, 34.37232],
    "华县": [109.76845, 34.55588],
    "彬县": [108.08226, 35.03629], "彬州市": [108.08226, 35.03629],
    "淳化县": [108.58051, 34.79954],
    "满城": [115.32317, 38.95137],
    "满城县": [115.32317, 38.95137],
    "平山县": [114.19064, 38.26127],
    "景县": [116.27224, 37.69617],
    "寿张县": [115.90348, 36.00351],
    "寿县": [116.7929, 32.54751],
    "淄博": [118.05493, 36.81349],
    "凌源": [119.401, 41.243],
    "猗氏县": [110.5, 35.1],
    "襄汾县": [111.42176, 35.88187],
    "秦安县": [105.66575, 34.85999],
    "偃师县": [112.76772, 34.73331],
    "晋宁县": [102.59411, 24.67247],
    "北票": [120.8, 41.8],
    "江宁区": [118.85, 31.95],
    "雨花区": [118.73, 31.99],
    "临安市": [119.71, 30.23],
    "绍兴市": [120.5786, 30.0024],
    "兴平市": [108.48158, 34.29987],
    "乾县": [108.24091, 34.53045],
    "礼泉县": [108.42722, 34.48372],
    "石楼县": [110.83781, 36.99913],
    "安乡县": [112.16527, 29.41356],
    "宁乡县": [112.55697, 28.28726],
    "云梦县": [113.75755, 31.01864],
    "随县": [113.30728, 31.85705],
    "黄陂县": [114.37543, 30.87679],
    "宜兴市": [119.8202, 31.3606],
    "丹徒县": [119.42852, 32.13374],
    "盱眙县": [118.54897, 32.98922],
    "余杭县": [120.30516, 30.42193],
    "乐都县": [102.40973, 36.47756],
    "都兰县": [98.09389, 36.30545],
    "大通县": [101.68936, 36.93518],
    "民丰县": [82.69983, 37.07124],
    "贺兰县": [106.35288, 38.56178],
    "晋宁区": [102.60029, 24.67951],
    "黑龙江": [126.6, 45.8], "吉林": [125.3, 43.9], "辽宁": [123.4, 41.8],
    "河北": [114.5, 38.0], "河南": [113.7, 34.8], "山东": [117.0, 36.7],
    "山西": [112.5, 37.9], "陕西": [108.9, 34.3], "甘肃": [103.8, 36.0],
    "青海": [101.8, 36.6], "四川": [104.1, 30.6], "云南": [102.7, 25.0],
    "贵州": [106.6, 26.6],     "湖南": [113.0, 28.2], "湖北": [114.3, 30.6],
    "安徽": [117.3, 31.8], "江西": [115.9, 28.7], "江苏": [118.8, 32.1],
    "浙江": [120.2, 30.3], "福建": [119.3, 26.1], "广东": [113.3, 23.1],
    "海南": [110.4, 20.0],
}

def extract_origin(relic):
    """从 source 字段提取出土地点坐标，仅在首句中查找"""
    s = relic['source']
    # 首句搜索（出土地通常在首句）
    parts = s.split('。', 1)
    first_sentence = parts[0]
    candidates = []
    for name, coord in LOCATION_COORDS.items():
        if len(name) > 1 and name in first_sentence:
            pos = first_sentence.index(name)
            candidates.append((pos, len(name), name, coord))
    if candidates:
        candidates.sort(key=lambda x: (-x[1], -x[0]))
        return candidates[0][3]
    # 首句无结果：搜索后续句子
    if len(parts) > 1:
        rest = parts[1]
        # 特定文物来源坐标覆盖（数据中地点描述过于笼统时）
        ORIGIN_OVERRIDE = {
            "商鞅方升": [109.58626, 34.95576],  # 铭文"重泉"=今蒲城县, 非西安
            "'统领释教大元国师之印'龙钮玉印": [88.01965, 28.90381],  # 原属萨迦寺, 非拉萨
        }
        name = relic['name']
        if name in ORIGIN_OVERRIDE:
            return ORIGIN_OVERRIDE[name]
        # 如果提到"出土"，只搜索"出土"附近（出土前到第一个收藏动词前）
        search_text = rest
        if '出土' in rest:
            end_keywords = ['由', '捐赠', '藏于', '收藏', '入藏', '移交', '后归', '后由']
            end_pos = len(rest)
            for kw in end_keywords:
                p = rest.find(kw)
                if p > 0 and p < end_pos:
                    end_pos = p
            # 从"出土"往前找到句子开头，截取出土相关部分
            dig_pos = rest.index('出土')
            search_text = rest[max(0, dig_pos-40):end_pos]
        for name, coord in LOCATION_COORDS.items():
            if len(name) > 1 and name in search_text:
                pos = search_text.index(name)
                candidates.append((pos, len(name), name, coord))
        if candidates:
            candidates.sort(key=lambda x: (-x[1], -x[0]))
            return candidates[0][3]
    return None

def extract_museum_coords(museum_str):
    """从 museum 字段提取坐标"""
    for name in museum_str.split('/'):
        name = name.strip()
        if name in LOCATION_COORDS:
            return LOCATION_COORDS[name]
    return None

def generate_html():
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">
    <title>中国禁止出国（境）展览文物 | 195件（组）国宝档案</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"></script>
    <style>
        :root {
            --primary: #8B4513;
            --primary-light: #A0522D;
            --bg-warm: #FDF6E3;
            --bg-cream: #FFF8DC;
            --text-dark: #2C1810;
            --text-medium: #5D4037;
            --text-light: #8D6E63;
            --border: #D7CCC8;
            --accent-gold: #D4A574;
            --accent-red: #C45C48;
            --card-bg: #FFFBF0;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-warm);
            color: var(--text-dark);
            line-height: 1.7;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(180deg, #2C1810 0%, #4A3728 100%);
            color: #FDF6E3;
            padding: 80px 20px 60px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23D4A574' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.3;
        }
        
        .header-content {
            position: relative;
            z-index: 1;
            max-width: 900px;
            margin: 0 auto;
        }
        
        .header h1 {
            font-family: 'Noto Serif SC', serif;
            font-size: clamp(2rem, 5vw, 3.2rem);
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: 0.1em;
            text-shadow: 0 2px 20px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.15rem;
            color: var(--accent-gold);
            margin-bottom: 24px;
            font-weight: 300;
            letter-spacing: 0.15em;
        }
        
        .header .desc {
            font-size: 0.95rem;
            color: rgba(253,246,227,0.7);
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.8;
        }
        
        .header-stats {
            display: flex;
            justify-content: center;
            gap: 48px;
            margin-top: 40px;
            flex-wrap: wrap;
        }
        
        .stat-item { text-align: center; }
        .stat-number {
            font-family: 'Noto Serif SC', serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-gold);
            line-height: 1;
        }
        .stat-label {
            font-size: 0.85rem;
            color: rgba(253,246,227,0.6);
            margin-top: 8px;
            letter-spacing: 0.1em;
        }
        
        .controls {
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            padding: 24px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 20px rgba(0,0,0,0.05);
        }
        
        .controls-inner {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
        }
        
        .search-box {
            flex: 1;
            min-width: 280px;
            max-width: 500px;
            position: relative;
        }
        
        .search-clear {
            display: none;
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            color: #bbb;
            font-size: 1rem;
            padding: 4px 6px;
            z-index: 2;
            line-height: 1;
            border-radius: 50%;
            transition: all 0.2s;
            user-select: none;
        }
        .search-clear:hover { color: var(--text-medium); background: #f0e8d8; }
        .search-clear.visible { display: block; }
        .search-box input {
            width: 100%;
            padding: 12px 40px 12px 48px;
            border: 2px solid var(--border);
            border-radius: 12px;
            background: #fff;
            font-size: 0.95rem;
            color: var(--text-dark);
            transition: all 0.3s;
            font-family: inherit;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: var(--accent-gold);
            box-shadow: 0 0 0 4px rgba(212,165,116,0.15);
        }
        
        .search-box::before {
            content: "🔍";
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.1rem;
            opacity: 0.5;
        }
        
        .filter-group {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 10px 20px;
            border: 2px solid var(--border);
            border-radius: 10px;
            background: #fff;
            color: var(--text-medium);
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s;
            font-family: inherit;
            font-weight: 500;
        }
        
        .filter-btn:hover, .filter-btn.active {
            border-color: var(--accent-gold);
            background: linear-gradient(135deg, #FFF8DC, #FDF6E3);
            color: var(--primary);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        .relics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 24px;
        }
        
        .relic-card {
            background: var(--card-bg);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }
        
        .relic-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }
        
        .card-image {
            width: 100%;
            height: 220px;
            background: linear-gradient(135deg, #f5f0e8, #ebe4d6);
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .card-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        
        .placeholder {
            width: 100%;
            height: 100%;
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }
        
        .placeholder-icon {
            font-family: 'Noto Serif SC', serif;
            font-size: 4rem;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 8px;
            opacity: 0.6;
        }
        
        .placeholder-text {
            font-size: 0.85rem;
            letter-spacing: 0.1em;
        }
        
        .batch-badge {
            position: absolute;
            top: 12px;
            right: 12px;
            padding: 6px 14px;
            background: rgba(44,24,16,0.85);
            color: var(--accent-gold);
            font-size: 0.75rem;
            border-radius: 20px;
            font-weight: 500;
            letter-spacing: 0.05em;
            backdrop-filter: blur(10px);
        }
        
        .card-body {
            padding: 24px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .card-header { margin-bottom: 16px; }
        
        .card-name {
            font-family: 'Noto Serif SC', serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-dark);
            margin-bottom: 6px;
            line-height: 1.4;
        }
        
        .card-name a {
            color: inherit;
            text-decoration: none;
        }
        
        .card-name a:hover {
            color: var(--primary-light);
            text-decoration: underline;
        }
        
        .card-era {
            display: inline-block;
            padding: 4px 12px;
            background: linear-gradient(135deg, #FFF8DC, #FDF6E3);
            color: var(--primary-light);
            font-size: 0.8rem;
            border-radius: 6px;
            font-weight: 500;
            border: 1px solid var(--accent-gold);
        }
        
        .card-info { margin-top: auto; }
        
        .info-row {
            display: flex;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }
        
        .info-label {
            color: var(--text-light);
            min-width: 48px;
            font-weight: 500;
            flex-shrink: 0;
        }
        
        .info-value {
            color: var(--text-medium);
            flex: 1;
        }
        
        .card-desc {
            margin-top: 14px;
            padding-top: 14px;
            border-top: 1px dashed var(--border);
            font-size: 0.88rem;
            color: var(--text-light);
            line-height: 1.7;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .card-footer {
            margin-top: 16px;
            padding-top: 14px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .card-owner {
            font-size: 0.85rem;
            color: var(--text-light);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .card-owner::before { content: "🏛"; }
        
        .card-no {
            font-family: 'Noto Serif SC', serif;
            font-size: 0.8rem;
            color: var(--accent-gold);
            font-weight: 600;
        }
        
        .footer {
            background: #2C1810;
            color: rgba(253,246,227,0.6);
            text-align: center;
            padding: 40px 20px;
            font-size: 0.9rem;
        }
        
        .footer a {
            color: var(--accent-gold);
            text-decoration: none;
        }
        
        .map-section {
            overflow: hidden;
            transition: all 0.5s ease;
            max-height: 800px;
            opacity: 1;
        }
        .map-section.collapsed {
            max-height: 0;
            padding: 0 20px;
            opacity: 0;
            border-top: none;
        }
        .special-tab-btn {
            padding: 6px 16px;
            border: 1px solid #b8860b;
            background: transparent;
            border-radius: 16px;
            cursor: pointer;
            font-size: 0.85rem;
            color: #b8860b;
            transition: all 0.3s;
            white-space: nowrap;
        }
        .special-tab-btn:hover {
            background: #b8860b;
            color: #fff;
        }
        .special-tab-btn.active {
            background: #b8860b;
            color: #fff;
        }
        .special-section { display: none; }
        .special-section.visible { display: block; }
        .relics-grid.special-hidden { display: none; }
        .special-header {
            text-align: center;
            padding: 40px 20px 30px;
            background: linear-gradient(180deg, rgba(184,134,11,0.08), transparent);
            border-bottom: 1px solid rgba(184,134,11,0.2);
            margin-bottom: 32px;
        }
        .special-header h2 {
            font-family: 'Noto Serif SC', serif;
            font-size: 1.8rem;
            color: #8B6914;
            margin-bottom: 12px;
        }
        .special-header p {
            font-size: 0.95rem;
            color: #8D6E63;
            max-width: 640px;
            margin: 0 auto;
            line-height: 1.8;
        }
        .map-toggle-btn {
            padding: 6px 16px;
            border: 1px solid var(--accent-gold);
            background: transparent;
            border-radius: 16px;
            cursor: pointer;
            font-size: 0.85rem;
            color: var(--primary-light);
            transition: all 0.3s;
            white-space: nowrap;
        }
        .map-toggle-btn:hover {
            background: var(--accent-gold);
            color: #fff;
        }
        .map-title {
            font-family: 'Noto Serif SC', serif;
            font-size: 1.6rem;
            text-align: center;
            margin-bottom: 24px;
            color: var(--text-dark);
        }
        .map-tabs {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 24px;
        }
        .map-btn {
            padding: 8px 24px;
            border: 1px solid var(--border);
            background: var(--card-bg);
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            color: var(--text-medium);
            transition: all 0.3s;
        }
        .map-btn:hover { border-color: var(--accent-gold); }
        .map-btn.active {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }
        #chinaMap { border-radius: 12px; background: #faf3ea; }
        
        @media (max-width: 768px) {
            .header { padding: 60px 20px 40px; }
            .header-stats { gap: 24px; }
            .stat-number { font-size: 2rem; }
            .relics-grid { grid-template-columns: 1fr; }
            .controls-inner { flex-direction: column; align-items: stretch; }
            .search-box { max-width: 100%; }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .relic-card { animation: fadeIn 0.6s ease-out both; }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <h1>禁止出国（境）展览文物</h1>
            <p class="subtitle">195件（组）中华国宝档案</p>
            <p class="desc">
                国家文物局先后于2002年、2012年、2013年公布三批禁止出境展览的一级文物名单，
                旨在保护国家一级文物中的孤品和易损品，确保珍贵文物的绝对安全。
            </p>
            <div class="header-stats">
                <div class="stat-item">
                    <div class="stat-number">64</div>
                    <div class="stat-label">第一批（2002年）</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">37</div>
                    <div class="stat-label">第二批（2012年）</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">94</div>
                    <div class="stat-label">第三批（2013年）</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">195</div>
                    <div class="stat-label">总计（件/组）</div>
                </div>
            </div>
        </div>
    </header>
    
    <div class="controls">
        <div class="controls-inner">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="搜索文物名称、时代、物主...">
                <span class="search-clear" id="searchClear" onclick="clearSearch()">✕</span>
            </div>
            <div class="filter-group">
                <button class="filter-btn active" data-filter="all">全部</button>
                <button class="filter-btn" data-filter="第一批">第一批</button>
                <button class="filter-btn" data-filter="第二批">第二批</button>
                <button class="filter-btn" data-filter="第三批">第三批</button>
                <button class="map-toggle-btn" onclick="toggleMapSection()">🗺 地理分布</button>
                ''' + ('<button class="special-tab-btn" onclick="showSpecial()">✦ 未收录特辑</button>' if relics_special else '') + '''
            </div>
        </div>
    </div>
    
    <section class="map-section collapsed" id="mapSection">
        <div class="container">
            <h2 class="map-title">文物地理分布</h2>
            <div class="map-tabs">
                <button class="map-btn active" onclick="switchMap(0)">来源地分布</button>
                <button class="map-btn" onclick="switchMap(1)">馆藏地分布</button>
            </div>
            <div id="chinaMap" style="width:100%;height:600px;"></div>
        </div>
    </section>
    
    <main class="container">
        <div class="relics-grid" id="relicsGrid">
'''
    
    for idx, relic in enumerate(relics):
        batch = relic.get("batch", "")
        no = relic.get("no", idx+1)
        name = relic["name"]
        era = relic["era"]
        source = relic["source"]
        owner = relic["owner"]
        museum = relic.get("museum", "")
        desc = relic["desc"]
        
        img_html = get_image_html(relic, idx)
        placeholder_html = get_placeholder_html(name, era, idx)
        
        if img_html:
            image_section = img_html + placeholder_html.replace('<div class="placeholder"', '<div class="placeholder" style="display:none;"')
        else:
            image_section = placeholder_html.replace('<div class="placeholder"', '<div class="placeholder" style="display:flex;"')
        
        card_html = f'''
            <article class="relic-card" data-batch="{batch[:3]}" data-name="{name}" data-era="{era}" data-owner="{owner}" data-museum="{museum}">
                <div class="card-image">
                    {image_section}
                    <span class="batch-badge">{batch}</span>
                </div>
                <div class="card-body">
                    <div class="card-header">
                        <h2 class="card-name">{'<a href="' + relic['baike_url'] + '" target="_blank" rel="noopener">' + name + '</a>' if relic.get('baike_url') else name}</h2>
                        <span class="card-era">{era}</span>
                    </div>
                    <div class="card-info">
                        <div class="info-row">
                            <span class="info-label">来源</span>
                            <span class="info-value">{source}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">物主</span>
                            <span class="info-value">{owner}</span>
                        </div>
                    </div>
                    <p class="card-desc">{desc}</p>
                    <div class="card-footer">
                        <span class="card-owner">{museum}</span>
                        <span class="card-no">No. {no}</span>
                    </div>
                </div>
            </article>
'''
        html += card_html
    
    # 生成地图数据（按坐标聚合，同地点多条记录合并）
    def aggregate(data_list):
        groups = {}
        for item in data_list:
            key = (item["x"], item["y"])
            if key not in groups:
                groups[key] = {"names": [], "srcs": [], "muses": [], "x": item["x"], "y": item["y"]}
            groups[key]["names"].append(item["name"])
            groups[key]["srcs"].append(item.get("src", ""))
            groups[key]["muses"].append(item.get("mus", ""))
        result = []
        for k, g in groups.items():
            result.append({
                "names": g["names"],
                "count": len(g["names"]),
                "srcs": g["srcs"],
                "muses": g["muses"],
                "value": [round(g["x"], 4), round(g["y"], 4), len(g["names"])]
            })
        return result
    
    origin_items = []
    museum_items = []
    for r in relics:
        ox, oy = extract_origin(r) or (None, None)
        mx, my = extract_museum_coords(r.get('museum', '')) or (None, None)
        name = r['name']
        src = r.get('source', '').strip()
        mus = r.get('museum', '').strip()
        if not ox and ('故宫' in mus or '首都' in mus):
            ox, oy = LOCATION_COORDS.get('北京', (None, None))
        if ox: origin_items.append({"name": name, "src": src, "x": ox, "y": oy})
        if mx: museum_items.append({"name": name, "mus": mus, "x": mx, "y": my})
    
    origin_data = aggregate(origin_items)
    museum_data = aggregate(museum_items)
    
    map_json_origin = json.dumps(origin_data, ensure_ascii=False)
    map_json_museum = json.dumps(museum_data, ensure_ascii=False)
    
    # 特辑
    if relics_special:
        special_cards = ''
        for idx, r in enumerate(relics_special):
            s_name = r['name']
            s_era = r.get('era', '')
            s_img_html = get_image_html(r, idx)
            s_placeholder_html = get_placeholder_html(s_name, s_era, idx)
            if s_img_html:
                s_image_section = s_img_html + s_placeholder_html.replace('<div class="placeholder"', '<div class="placeholder" style="display:none;"')
            else:
                s_image_section = s_placeholder_html.replace('<div class="placeholder"', '<div class="placeholder" style="display:flex;"')
            special_cards += f'''
            <article class="relic-card special-card">
                <div class="card-image">
                    {s_image_section}
                </div>
                <div class="card-body">
                    <div class="card-header">
                        <h2 class="card-name" style="color:#8B6914;">{'<a href="' + r['baike_url'] + '" target="_blank" rel="noopener" style="color:#8B6914;">' + s_name + '</a>' if r.get('baike_url') else s_name}</h2>
                        <span class="card-era">{s_era}</span>
                    </div>
                    <div class="card-info">
                        <div class="info-row">
                            <span class="info-label">来源</span>
                            <span class="info-value">{r.get('source','')}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">物主</span>
                            <span class="info-value">{r.get('owner','')}</span>
                        </div>
                    </div>
                    <p class="card-desc">{r.get('desc','')}</p>
                    <div class="card-footer">
                        <span class="card-owner">{r.get('museum','')}</span>
                        <span class="card-no">No. {r['no']}</span>
                    </div>
                </div>
            </article>'''
        html += '''
        </div>
    </main>
    
    <section class="special-section" id="specialSection">
        <div class="special-header">
            <h2>✦ 未收录特辑</h2>
            <p>此特辑收录未列入禁止出境展览文物名录（或流失、流转至境外）的重磅文物，这些文物的历史价值与艺术成就丝毫不逊。特辑持续更新中。</p>
        </div>
        <div class="container">
            <div class="relics-grid">''' + special_cards + '''
        </div></div>
    </section>'''
    
    html += '''
    <script>
    const originData = ''' + map_json_origin + ''';
    const museumData = ''' + map_json_museum + ''';
    var currentMode = 0;

    fetch('china.json')
        .then(r => r.json())
        .then(china => {
            echarts.registerMap('china', china);
            const chart = echarts.init(document.getElementById('chinaMap'));
            window.mapChart = chart;
            renderMap(originData);
            window.addEventListener('resize', () => chart.resize());
        });
    
    function renderMap(data) {
        var opt = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'item',
                position: 'left',
                formatter: function(p) {
                    if (!p.data) return '';
                    var names = p.data.names, srcs = p.data.srcs, muses = p.data.muses;
                    var count = p.data.count;
                    var truncate = function(s, n) {
                        return s.length > n ? s.substring(0, n) + '...' : s;
                    };
                    var items = [];
                    for (var i = 0; i < Math.min(count, 15); i++) {
                        var extra = currentMode === 0 ? (srcs[i] || '') : (muses[i] || '');
                        var line = '<b>' + names[i] + '</b>';
                        if (extra) line += '<br/><span style=\"font-size:0.8rem;color:#888;\">' + truncate(extra, 80) + '</span>';
                        items.push(line);
                    }
                    var html = items.join('<hr style=\"margin:4px 0;border:none;border-top:1px solid #eee;\"/>');
                    if (count > 15) html += '<hr style=\"margin:4px 0;border:none;border-top:1px solid #eee;\"/><span style=\"font-size:0.8rem;color:#999;\">...等共' + count + '件</span>';
                    return html;
                }
            },
            geo: {
                map: 'china',
                roam: true,
                zoom: 1.6,
                center: [104, 36],
                itemStyle: {
                    areaColor: '#f5e6d3',
                    borderColor: '#c4a882',
                    borderWidth: 1,
                },
                emphasis: {
                    itemStyle: { areaColor: '#e8d5b8' },
                    label: { show: false }
                }
            }
        };
        opt.series = [{
            type: 'scatter',
            coordinateSystem: 'geo',
            data: data,
            symbol: 'circle',
            symbolSize: function(d) {
                return Math.min(6 + (d.count || 1) * 2, 20);
            },
            itemStyle: {
                color: '#c45c48',
                shadowBlur: 4,
                shadowColor: 'rgba(196,92,72,0.4)'
            },
            emphasis: {
                itemStyle: { color: '#8b3a2a', shadowBlur: 8 }
            }
        }];
        window.mapChart.setOption(opt, true);
    }
    
    function switchMap(idx) {
        currentMode = idx;
        document.querySelectorAll('.map-btn').forEach((b,i) => b.classList.toggle('active', i===idx));
        renderMap(idx === 0 ? originData : museumData);
    }
    
    function showSpecial() {
        location.hash = 'special';
        var sec = document.getElementById('specialSection');
        if (!sec) return;
        document.querySelectorAll('.filter-btn, .special-tab-btn').forEach(function(b) { b.classList.remove('active'); });
        var sbtn = document.querySelector('.special-tab-btn');
        if (sbtn) sbtn.classList.add('active');
        document.getElementById('relicsGrid').style.display = 'none';
        sec.style.display = 'block';
        sec.querySelectorAll('.special-card').forEach(function(c) { c.classList.remove('hidden'); c.style.animationDelay = '0s'; });
        var mc = document.querySelector('main.container');
        if (mc) mc.style.padding = '0';
        // 隐藏地理分布按钮
        var mtb = document.querySelector('.map-toggle-btn');
        if (mtb) mtb.style.display = 'none';
        var ms = document.getElementById('mapSection');
        if (ms && !ms.classList.contains('collapsed')) toggleMapSection();
        // 应用当前搜索词
        var sq = document.getElementById('searchInput');
        if (sq && sq.value) {
            var q = sq.value.toLowerCase().trim();
            sec.querySelectorAll('.special-card').forEach(function(c) {
                c.classList.toggle('hidden', !(c.textContent || '').toLowerCase().includes(q));
            });
        }
    }
    function showMain() {
        var sec = document.getElementById('specialSection');
        if (!sec) return;
        sec.style.display = 'none';
        var sbtn = document.querySelector('.special-tab-btn');
        if (sbtn) sbtn.classList.remove('active');
        var grid = document.getElementById('relicsGrid');
        grid.style.display = '';
        var mainContainer = document.querySelector('main.container');
        if (mainContainer) mainContainer.style.padding = '';
        // 显示地理分布按钮
        var mtb = document.querySelector('.map-toggle-btn');
        if (mtb) mtb.style.display = '';
    }
    function toggleMapSection() {
        var section = document.getElementById('mapSection');
        var btn = document.querySelector('.map-toggle-btn');
        var isCollapsed = section.classList.contains('collapsed');
        section.classList.toggle('collapsed');
        btn.textContent = isCollapsed ? '🗺 收起地图' : '🗺 地理分布';
        if (isCollapsed) {
            setTimeout(function() {
                window.mapChart && window.mapChart.resize();
            }, 500);
        }
    }
    </script>
    
    <footer class="footer">
        <p>数据来源：国家文物局《禁止出境展览文物目录》（2002年、2012年、2013年）</p>
        <p style="margin-top:8px; font-size:0.85rem; opacity:0.7;">图片来源于各博物馆公开资料及网络搜集 · 仅供学习研究使用</p>
        <p style="margin-top:12px; font-size:0.8rem; opacity:0.5;">
            参考：<a href="https://baike.baidu.com/item/%E7%A6%81%E6%AD%A2%E5%87%BA%E5%9B%BD%EF%BC%88%E5%A2%83%EF%BC%89%E5%B1%95%E8%A7%88%E6%96%87%E7%89%A9/8213166" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline;text-underline-offset:2px;">百度百科·禁止出境展览文物</a> · <a href="https://www.eeo.com.cn/2023/0818/601837.shtml" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline;text-underline-offset:2px;">经济观察网·195件禁出境文物全名单</a>
        </p>
    </footer>
    
    <script>
        const searchInput = document.getElementById('searchInput');
        const cards = document.querySelectorAll('.relic-card');
        
        function applySearch() {
            var evt = new Event('input');
            searchInput.dispatchEvent(evt);
        }
        function clearSearch() {
            searchInput.value = '';
            document.getElementById('searchClear').classList.remove('visible');
            applySearch();
            searchInput.focus();
        }
        searchInput.addEventListener('input', function() {
            var clr = document.getElementById('searchClear');
            if (clr) clr.classList.toggle('visible', this.value.length > 0);
        });
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            // 搜索195名单
            var activeFilter = document.querySelector('.filter-btn.active');
            var filter = activeFilter ? activeFilter.dataset.filter : 'all';
            cards.forEach(card => {
                if (!card.dataset.name) return;
                var name = card.dataset.name.toLowerCase();
                var era = card.dataset.era.toLowerCase();
                var owner = card.dataset.owner.toLowerCase();
                var museum = (card.dataset.museum || '').toLowerCase();
                var match = name.includes(query) || era.includes(query) || owner.includes(query) || museum.includes(query);
                if (filter !== 'all') match = match && (card.dataset.batch === filter);
                card.classList.toggle('hidden', !match);
                });
            // 搜索特辑卡片
            document.querySelectorAll('.special-card').forEach(function(card) {
                var txt = (card.textContent || '').toLowerCase();
                card.classList.toggle('hidden', !txt.includes(query));
            });
        });
        
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                showMain();
                location.hash = btn.dataset.filter;
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filter = btn.dataset.filter;
                var query = searchInput ? searchInput.value.toLowerCase().trim() : '';
                cards.forEach(card => {
                    if (!card.dataset.batch) return;
                    var match = filter === 'all' || card.dataset.batch === filter;
                    if (query) {
                        var txt = ((card.dataset.name || '') + (card.dataset.era || '') + (card.dataset.owner || '') + (card.dataset.museum || '')).toLowerCase();
                        match = match && txt.includes(query);
                    }
                    card.classList.toggle('hidden', !match);
                });
            });
        });
        
        cards.forEach((card, i) => {
            card.style.animationDelay = `${(i % 20) * 0.05}s`;
        });

        // 恢复刷新前的标签状态
        if (location.hash === '#special') {
            showSpecial();
        } else if (location.hash) {
            var target = document.querySelector('.filter-btn[data-filter="' + location.hash.slice(1) + '"]');
            if (target) target.click();
        }
    </script>
</body>
</html>
'''
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("HTML页面已生成：relics-195/index.html")
    print(f"总计 {len(relics)} 件文物")
    print(f"配有图片 {sum(1 for r in relics if r.get('image_url'))} 件")

if __name__ == "__main__":
    generate_html()
