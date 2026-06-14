#!/usr/bin/env python3
"""Rank relics by multi-dimension scoring using LLM (v2)."""
import os
import sys
import json
import time
import re
import random
import argparse
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RELIC_SOURCE = os.path.join(BASE_DIR, 'relics_special.py')
RELIC_SOURCE_195 = os.path.join(BASE_DIR, 'relics_data.py')
OUTPUT_DIR = os.path.join(BASE_DIR, 'rank_output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
CACHE_FILE = os.path.join(OUTPUT_DIR, 'scores_special.json')
RESULT_FILE = os.path.join(OUTPUT_DIR, 'avg_special.json')




WEIGHTS = {"历史": 0.45, "稀缺": 0.23, "艺术": 0.22, "符号": 0.1}
DIMS = ["历史", "稀缺", "艺术", "符号"]

NUM_ROUNDS = 3  # default, overridden by --rounds
GROUP_SIZE = 20
MAX_RETRIES = 3

SYSTEM_PROMPT = (
    "你是中国文物专家。对以下每件文物在四个维度上分别评分（一位小数），各维度严格遵守以下具体解释方法，不得自作理解或望文生义："
    "【历史价值】少了它历史缺了什么？文献类看信息量和不可替代性，艺术品看审美/技法/生活的时代记录，器物看制度/科技/文化意义。摹本/复制品低于真迹创作品，除非原作失传且该摹本就是该历史信息的主要载体。年代差异不自动决定分数高低，看的是这件文物在所属时代中的历史信息独特性。最高99.9分。"
    "【稀缺性】同类完整品存世稀缺程度。同时考虑品类代表性：代表完整品类核心成就的文物，稀缺分应高于同样存世量但在同品类中边缘的文物。同品类中非核心的文物（如孤品书画作品，但作者本身非品类核心人物）即使存世极少，稀缺分也应以核心成就文物优先。最高99.9分。"
    "【艺术/工艺水准】在同品类中排位。书画类侧重表现力/创新/影响力，器物侧重工艺难度/技术含量。不以艺术见长的品类(如简牍、文书)看其记载的清晰完整程度，在品类内评分不跨品类比较。作品的体量和叙事独特性也应纳入考量。最低70分，最高99.9分。"
    "【文明符号力】跨圈知名度和符号意义。最高99.9分。"
    "回复严格JSON格式数组，不要其他内容："
    '[{"no":1,"历史":80.0,"稀缺":70.5,"艺术":90.8,"符号":80.2}]'
)


def load_relics(path, var_name='relics_special'):
    namespace = {}
    with open(path, 'r', encoding='utf-8') as f:
        exec(f.read(), namespace)
    return namespace[var_name]


def make_description(item):
    name = item['name']
    era = item['era'].split('（')[0]
    museum = item['museum']
    source = item.get('source', '').replace('\n', ' ').strip()
    desc = item.get('desc', '').replace('\n', ' ').strip()
    return f"{name} | {era} | {museum}\n  来源: {source}\n  描述: {desc}"


def extract_json(text):
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        return match.group()
    return text


def llm_score_group(group_indices, descriptions, llm_config):
    lines = []
    for j, desc in enumerate(descriptions, 1):
        lines.append(f"{j}. {desc}")
    user_prompt = "\n".join(lines)

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                f"{llm_config['base_url'].rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {llm_config['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": llm_config['model'],
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0,
                },
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            content = result['choices'][0]['message']['content'].strip()
            content = extract_json(content)
            scores = json.loads(content)
            score_dict = {}
            for entry in scores:
                pos = entry['no'] - 1
                idx = group_indices[pos]
                score_dict[idx] = {dim: int(entry[dim]) for dim in DIMS}
            return score_dict
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)

    print("\n  API failed. Please enter scores manually.")
    score_dict = {}
    for j, (idx, desc) in enumerate(zip(group_indices, descriptions), 1):
        print(f"  [{j}] {desc}")
        while True:
            try:
                inp = input("  历史 稀缺 艺术 符号 (空格分隔 1-100): ").strip()
            except (EOFError, KeyboardInterrupt):
                inp = "5 5 5 5"
            parts = inp.split()
            if len(parts) == 4:
                try:
                    vals = {dim: max(1, min(100, int(v))) for dim, v in zip(DIMS, parts)}
                    score_dict[idx] = vals
                    break
                except ValueError:
                    pass
            print("  格式错误, 输入4个1-100数字空格分隔")
    return score_dict


def load_cache():
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except Exception as e:
            print(f"Cache load failed: {e}")
    return cache


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def migrate_cache(cache):
    """Migrate old format (round_X keys at top) to new format (run_0 -> round_X)."""
    if any(k.startswith('round_') for k in cache):
        print("Migrating cache from old format to new run-based format...")
        new_cache = {'run_0': {}}
        round_keys = sorted(
            [k for k in cache if k.startswith('round_')],
            key=lambda x: int(x.split('_')[1])
        )
        for rk in round_keys:
            new_cache['run_0'][rk] = cache[rk]
        save_cache(new_cache)
        print(f"Migrated {len(round_keys)} rounds under run_0")
        return new_cache
    return cache


def compute_run_scores(run_data, n):
    """Per-item average of dimension scores across all rounds in one run."""
    avg_scores = {}
    for idx in range(n):
        dim_sums = {dim: 0.0 for dim in DIMS}
        count = 0
        for round_data in run_data.values():
            if str(idx) in round_data:
                count += 1
                for dim in DIMS:
                    dim_sums[dim] += round_data[str(idx)][dim]
        if count > 0:
            avg_scores[idx] = {dim: dim_sums[dim] / count for dim in DIMS}
        else:
            avg_scores[idx] = {dim: 5.0 for dim in DIMS}
    return avg_scores


def fmt(val):
    s = f"{val:.2f}"
    return s.rstrip('0').rstrip('.')


def print_ranking(avg_scores, relics, total_api_calls, total_tokens):
    n = len(relics)
    ranked_list = []
    for idx, scores in avg_scores.items():
        weighted = sum(scores[dim] * WEIGHTS[dim] for dim in DIMS)
        ranked_list.append((weighted, idx, scores))
    ranked_list.sort(key=lambda x: -x[0])

    print(f"\n{'─' * 108}")
    header = (
        f"{'排名':<6}{'文物名称':<28}{'博物馆':<28}"
        f"{'历史分':<8}{'稀缺分':<8}{'艺术分':<8}{'符号分':<8}{'加权总分':<8}"
    )
    print(header)
    print(f"{'─' * 108}")

    result = []
    for rank, (total, idx, scores) in enumerate(ranked_list, 1):
        item = relics[idx]
        entry = {
            'rank': rank,
            'no': item.get('no'),
            'name': item['name'],
            'era': item['era'],
            'museum': item['museum'],
            '历史': round(scores['历史'], 2),
            '稀缺': round(scores['稀缺'], 2),
            '艺术': round(scores['艺术'], 2),
            '符号': round(scores['符号'], 2),
            '加权总分': round(total, 2),
        }
        result.append(entry)
        print(
            f"{rank:<6}{item['name']:<28}{item['museum']:<28}"
            f"{scores['历史']:<8.2f}{scores['稀缺']:<8.2f}"
            f"{scores['艺术']:<8.2f}{scores['符号']:<8.2f}{total:<8.2f}"
        )

    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'─' * 108}")
    print(f"总计 API 调用次数: {total_api_calls} (每次批处理 {GROUP_SIZE} 件文物)")
    print(f"总轮次: {NUM_ROUNDS}")
    print(f"估算输入 tokens: ~{total_tokens}")
    print(f"每件文物被评分 {NUM_ROUNDS} 次取平均")
    print(f"结果已保存: {RESULT_FILE}")
    print(f"缓存文件: {CACHE_FILE}")


def do_run(run_num, force, resume, cache, relics, descriptions, llm_config):
    n = len(relics)
    run_key = f"run_{run_num}"

    if run_key in cache and not force:
        run_data = cache[run_key]
        all_complete = all(
            f"round_{r}" in run_data and len(run_data[f"round_{r}"]) >= n
            for r in range(NUM_ROUNDS)
        )
        if all_complete:
            print(f"Run {run_num} already cached and complete")
            avg_scores = compute_run_scores(run_data, n)
            print_ranking(avg_scores, relics, 0, 0)
            return
        else:
            print(f"Run {run_num} partially cached, resuming...")

    if not llm_config['api_key']:
        print("Error: LLM_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    total_api_calls = 0
    total_tokens = 0

    run_data = cache.get(run_key, {})
    if force:
        run_data = {}

    for round_num in range(NUM_ROUNDS):
        round_key = f"round_{round_num}"
        seed = run_num * NUM_ROUNDS + round_num

        if round_key in run_data and not force:
            cached = run_data[round_key]
            if len(cached) >= n:
                print(
                    f"Run {run_num} Round {round_num}: "
                    f"using cache ({len(cached)} items)"
                )
                continue

        rng = random.Random(seed)
        indices = list(range(n))
        rng.shuffle(indices)
        groups = [indices[i:i + GROUP_SIZE] for i in range(0, n, GROUP_SIZE)]
        if len(groups) > 1 and len(groups[-1]) <= 10:
            groups[-2] += groups[-1]  # merge last small group
            groups.pop()

        round_data = run_data.get(round_key, {})
        if not resume or force:
            round_data = {}

        groups_to_score = [
            g for g in groups
            if any(str(idx) not in round_data for idx in g)
        ]

        if not groups_to_score:
            print(
                f"Run {run_num} Round {round_num}: "
                f"all groups cached, skipping"
            )
            run_data[round_key] = round_data
            continue

        print(
            f"Run {run_num} Round {round_num} (seed={seed}): "
            f"{len(groups_to_score)}/{len(groups)} groups to score"
        )

        prompt_tokens_this_round = 0
        for g_idx, group in enumerate(groups_to_score):
            group_descs = [descriptions[i] for i in group]
            scores = llm_score_group(group, group_descs, llm_config)
            for idx, s in scores.items():
                round_data[str(idx)] = s
            total_api_calls += 1
            prompt_tokens_this_round += (
                sum(len(descriptions[i]) for i in group) // 2
                + len(SYSTEM_PROMPT) // 2
            )
            # Save immediately after each group
            run_data[round_key] = round_data
            cache[run_key] = run_data
            save_cache(cache)

        total_tokens += prompt_tokens_this_round
        print(f"  Run {run_num} Round {round_num} done, cache saved")

    cache[run_key] = run_data
    save_cache(cache)

    avg_scores = compute_run_scores(run_data, n)
    print_ranking(avg_scores, relics, total_api_calls, total_tokens)


def do_aggregate(cache, relics):
    n = len(relics)
    run_keys = sorted(
        [k for k in cache if k.startswith('run_')],
        key=lambda x: int(x.split('_')[1])
    )

    if not run_keys:
        print("No runs found in cache, nothing to aggregate.")
        sys.exit(1)

    print(
        f"Aggregating {len(run_keys)} runs: "
        f"{', '.join(run_keys)}\n"
    )

    run_avg_scores = {}
    for rk in run_keys:
        run_avg_scores[rk] = compute_run_scores(cache[rk], n)

    ranked_list = []
    for idx in range(n):
        dim_sums = {dim: 0.0 for dim in DIMS}
        count = 0
        for rk in run_keys:
            if idx in run_avg_scores[rk]:
                count += 1
                for dim in DIMS:
                    dim_sums[dim] += run_avg_scores[rk][idx][dim]

        if count > 0:
            avg_scores = {dim: dim_sums[dim] / count for dim in DIMS}
        else:
            avg_scores = {dim: 5.0 for dim in DIMS}

        weighted = sum(avg_scores[dim] * WEIGHTS[dim] for dim in DIMS)
        ranked_list.append((weighted, idx, avg_scores))

    ranked_list.sort(key=lambda x: -x[0])

    for rank, (total, idx, avg_scores) in enumerate(ranked_list, 1):
        name = relics[idx]['name']

        run_parts = []
        for rk in run_keys:
            scores = run_avg_scores[rk][idx]
            parts = ''.join(
                f"{d[:1]}{fmt(scores[d])}" for d in DIMS
            )
            w = sum(scores[d] * WEIGHTS[d] for d in DIMS)
            run_parts.append(f"{rk}:{parts}={fmt(w)}")

        run_line = ' | '.join(run_parts)

        avg_parts = ''.join(
            f"{d[:1]}{fmt(avg_scores[d])}" for d in DIMS
        )
        avg_total = fmt(total)

        print(f"{name}:")
        print(f"  {run_line}")
        print(f"  avg:{avg_parts}={avg_total}")

    result = []
    for rank, (total, idx, avg_scores) in enumerate(ranked_list, 1):
        item = relics[idx]
        entry = {
            'rank': rank,
            'no': item.get('no'),
            'name': item['name'],
            'era': item['era'],
            'museum': item['museum'],
            '历史': round(avg_scores['历史'], 2),
            '稀缺': round(avg_scores['稀缺'], 2),
            '艺术': round(avg_scores['艺术'], 2),
            '符号': round(avg_scores['符号'], 2),
            '加权总分': round(total, 2),
        }
        result.append(entry)

    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nAggregated result saved to {RESULT_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description='Rank relics by LLM multi-dimension scoring'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Ignore cache, re-score everything'
    )
    parser.add_argument(
        '--resume', action='store_true',
        help='Resume incomplete rounds from cache'
    )
    parser.add_argument(
        '--run', type=int, default=0,
        help='Run number (default 0)'
    )
    parser.add_argument(
        '--aggregate', action='store_true',
        help='Aggregate all runs from cache'
    )
    parser.add_argument(
        '--source', choices=['special', '195'], default='special',
        help='Data source: special (特辑) or 195 (官方名单)'
    )
    parser.add_argument(
        '--rounds', type=int, default=30,
        help='Number of scoring rounds (default 30)'
    )
    args = parser.parse_args()

    if args.source == '195':
        global CACHE_FILE, RESULT_FILE
        CACHE_FILE = os.path.join(OUTPUT_DIR, 'scores_195.json')
        RESULT_FILE = os.path.join(OUTPUT_DIR, 'avg_195.json')
        relics = load_relics(RELIC_SOURCE_195, 'relics')
    else:
        relics = load_relics(RELIC_SOURCE, 'relics_special')
    n = len(relics)
    print(f"Loaded {n} relics")

    descriptions = [make_description(item) for item in relics]

    cache = load_cache()
    cache = migrate_cache(cache)

    if cache:
        total_cached = sum(
            sum(len(v) for v in run_data.values())
            for run_data in cache.values()
        )
        print(
            f"Loaded cache: {total_cached} entries "
            f"across {len(cache)} runs"
        )

    if args.aggregate:
        do_aggregate(cache, relics)
        return

    llm_config = {
        'base_url': os.environ.get(
            'LLM_BASE_URL', 'https://api.deepseek.com'
        ),
        'api_key': os.environ.get('LLM_API_KEY', ''),
        'model': os.environ.get('LLM_MODEL', 'deepseek-chat'),
    }

    global NUM_ROUNDS
    NUM_ROUNDS = args.rounds

    do_run(
        args.run, args.force, args.resume,
        cache, relics, descriptions, llm_config
    )


if __name__ == '__main__':
    main()
