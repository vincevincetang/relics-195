import re, copy

def classify(era):
    e = era.strip()
    if '仰韶' in e: return '仰韶文化'
    if '龙山' in e: return '龙山文化'
    if '良渚' in e: return '良渚文化'
    if '红山' in e: return '红山文化'
    if '大汶口' in e: return '大汶口文化'
    if '河姆渡' in e: return '河姆渡文化'
    if '马家窑' in e: return '马家窑文化'
    if '凌家滩' in e: return '凌家滩文化'
    if '贾湖' in e: return '贾湖文化'
    if '石峁' in e: return '石峁文化'
    if '北宋摹本' in e: return '北宋'
    if '唐摹本' in e: return '唐'
    if '晚唐' in e: return '唐'
    if '五代' in e: return '五代'
    if '西夏' in e: return '西夏'
    if '辽' in e: return '辽'
    if '北宋' in e: return '北宋'
    if '南宋' in e: return '南宋'
    if e.startswith('唐') or e.startswith('唐·'): return '唐'
    if e.startswith('隋'): return '隋'
    if '新莽' in e or e.startswith('新·') or e.startswith('新莽'): return '新'
    if '三国' in e: return '三国'
    if '西晋' in e: return '西晋'
    if '东晋' in e: return '东晋'
    if '北魏' in e or '北齐' in e or '北燕' in e or '南朝' in e or '北朝' in e: return '南北朝'
    if e.startswith('夏'): return '夏'
    if '商' in e: return '商'
    if '西周' in e: return '西周'
    if '春秋' in e: return '春秋'
    if '战国' in e: return '战国'
    if e.startswith('秦'): return '秦'
    if '西汉' in e: return '西汉'
    if '东汉' in e: return '东汉'
    if e.startswith('汉'): return '西汉'
    if e.startswith('元'): return '元'
    if e.startswith('明'): return '明'
    if e.startswith('清'): return '清'
    return f'UNKNOWN: {e}'

# Specific era updates keyed by name fragment
NAME_ERA_UPDATES = {
    '拓西岳华山庙碑册（华阴本）': '南宋·约13世纪（宋末）',
    '宋代玉云龙纹炉': '南宋·约12-13世纪',
    '宋人摹阎立本《步辇图》卷': '北宋·仁宗朝（约11世纪中期）',
    '宋定窑白釉孩儿枕': '北宋·约11-12世纪',
    '登封窑珍珠地划花虎豹纹瓶': '北宋·约11世纪',
    '曜变天目茶碗（稻叶天目）': '南宋·约12-13世纪',
    '红地对人兽树纹罽袍': '东汉·约1-2世纪（东汉中晚期）',
}

def process_file(filepath):
    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()
    
    out_lines = []
    i = 0
    changed_eras = 0
    added_periods = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this line starts an item block: `{` at line start (possibly with indent)
        if stripped == '{' or stripped == '{':
            # Read the whole item block
            block_lines = [line]
            brace_depth = stripped.count('{') - stripped.count('}')
            j = i + 1
            while j < len(lines) and brace_depth > 0:
                block_lines.append(lines[j])
                brace_depth += lines[j].count('{') - lines[j].count('}')
                j += 1
            if brace_depth == 0:
                # Process this item block
                processed, era_changed, period_added = process_block(block_lines)
                out_lines.extend(processed)
                changed_eras += era_changed
                added_periods += period_added
                i = j
                continue
        
        out_lines.append(line)
        i += 1
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)
    
    print(f'{filepath}: {changed_eras} eras changed, {added_periods} periods added')
    return changed_eras + added_periods

def process_block(block_lines):
    block_text = ''.join(block_lines)
    era_changed = 0
    period_added = 0
    
    # Extract name
    name_match = re.search(r'"name":\s*"([^"]*)"', block_text)
    if not name_match:
        return block_lines, 0, 0
    name = name_match.group(1)
    
    # Extract era value
    era_match = re.search(r'"era":\s*"([^"]*)"', block_text)
    if not era_match:
        return block_lines, 0, 0
    old_era = era_match.group(1)
    new_era = old_era
    
    # Apply name-specific era update
    if name in NAME_ERA_UPDATES:
        new_era = NAME_ERA_UPDATES[name]
    
    if new_era != old_era:
        era_changed = 1
    
    # Determine period from the (possibly updated) era
    period = classify(new_era)
    
    # Rebuild the block: add/update era line, add period after era
    out_lines = []
    era_seen = False
    for line in block_lines:
        stripped = line.strip()
        # Check for era line
        era_line_match = re.match(r'(\s*)"era":\s*"([^"]*)",?\s*', line)
        if era_line_match:
            era_seen = True
            indent = era_line_match.group(1)
            old_val = era_line_match.group(2)
            if old_val != new_era:
                # Replace era value
                line = line.replace(f'"{old_val}"', f'"{new_era}"', 1)
            out_lines.append(line)
            # Add period line after era
            out_lines.append(f'{indent}"period": "{period}",\n')
            period_added = 1
            continue
        
        out_lines.append(line)
    
    # Safety check
    if not era_seen:
        print(f'  WARNING: no era line found for {name}')
    
    return out_lines, era_changed, period_added

# Run
total = 0
total += process_file('relics_data.py')
total += process_file('relics_special.py')

# Check for any UNKNOWN
import importlib.util, sys
for mod_name, filepath in [('relics_data', 'relics_data.py'), ('relics_special', 'relics_special.py')]:
    spec = importlib.util.spec_from_file_location(mod_name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = getattr(mod, 'relics' if mod_name == 'relics_data' else 'relics_special')
    unknowns = [r for r in data if r.get('period', '').startswith('UNKNOWN')]
    if unknowns:
        for r in unknowns:
            print(f'  UNKNOWN: {r["name"]} era={r["era"]} period={r.get("period")}')
    else:
        print(f'{filepath}: all {len(data)} items OK')

print(f'\nTotal changes: {total}')
