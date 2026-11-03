# 特別活動の「いま（平成29年告示）」をコード表から、「前回（平成20年告示）」を data/tokkatsu_h20.json から読み、
# くらべ・歩み・次の改訂・用語（data/tokkatsu_extra.json）と合わせて data/tokkatsu.json にし、見本の HTML を書き出す。
# 本文はどちらも原文のまま（ふりがな《》だけ外す）。
# 使い方: python3 tools/build_tokkatsu.py
import csv, json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

def clean(t): return re.sub(r'《[^》]*》', '', t).replace('\r', '').strip()
HEAD = re.compile(r'^(第[１２３]|[１２３](?=[\s　])|\([0-9]\)|[アイウエオカキ](?=[\s　])|〔第[^〕]*〕)[\s　]*(.*)$')
Z2H = str.maketrans('１２３４５６', '123456')

def row(rid, text, lv0=0):
    """1行を {id, n(番号), h(見出し), t(本文), lv} にする"""
    text = clean(text)
    if re.fullmatch(r'〔[^〕]*〕', text): return {'id': rid, 'n': text.strip('〔〕'), 'h': '', 't': '', 'lv': 0}
    first, _, rest = text.partition('\n')
    m = HEAD.match(first)
    if not m: return {'id': rid, 'n': '', 'h': '', 't': text, 'lv': 1}
    n, h = m.group(1), m.group(2).strip()
    lv = 1 if n.startswith('(') else 2 if (n[0] in 'アイウエオカキ' or n.startswith('〔')) else 0
    if n.startswith('〔'): n = n.strip('〔〕').replace('第', '').replace('学年及び', '・').replace('学年', '年').translate(Z2H)
    h = h.replace('　', '').replace(' ', '') if len(h) <= 8 else h
    if n.startswith('第') or (lv == 0 and len(h) <= 8 and h): n, h = h if h else n, ''  # 「目標」「内容」はそれ自体を番号の所へ
    if not rest and h.endswith('。'): h, rest = '', h  # 1行の本文
    return {'id': rid, 'n': n, 'h': h, 't': rest.strip(), 'lv': lv}

SECS = [('goal', '目標'), ('gakkyu', '学級活動'), ('jidokai', '児童会活動'), ('club', 'クラブ活動'), ('gyoji', '学校行事'), ('keikaku', '指導計画の作成と内容の取扱い')]
def secOfCode(c):
    if c[3] == '0': return 'goal' if c[4] == '1' else None
    return {'1': 'gakkyu', '2': 'jidokai', '3': 'club'}.get(c[3]) or ('gyoji' if c[4] == '2' else 'keikaku')

def build_now():
    rows = [x for x in csv.reader(open(P('data', '国のコード表_小学校_82V12.csv'), encoding='utf-8-sig')) if x and x[0] == '特別活動']
    out = {k: [] for k, _ in SECS}
    for _, _, t, c in rows:
        s = secOfCode(c)
        if not s or t.strip().startswith('〔') and t.strip().endswith('〕'): continue
        if t.startswith('第３') or t.startswith('第２'): continue  # 大見出しは左の一覧が受け持つ
        out[s].append(row(c, t))
    return out

def build_old():
    src = json.load(open(P('data', 'tokkatsu_h20.json'), encoding='utf-8'))
    out = {k: [] for k, _ in SECS}
    for r in src['rows']:
        out[r['sec']].append(row(r['id'], r['t']))
    return out, src['src']

now = build_now()
old, oldsrc = build_old()
ex = json.load(open(P('data', 'tokkatsu_extra.json'), encoding='utf-8'))
ids = {r['id'] for v in now.values() for r in v} | {r['id'] for v in old.values() for r in v}
for p in ex['pairs']:  # くらべの対応が本文にあるか
    for i in p.get('now', []) + p.get('old', []): assert i in ids, ('くらべの id が本文にない', i)
D = {'src': {'now': '小学校学習指導要領（平成29年告示）第６章 特別活動　学習指導要領コード【82V12】Ver1.2（文部科学省）', 'old': oldsrc},
     'secs': [{'id': k, 'n': n} for k, n in SECS], 'now': now, 'old': old, **ex}
json.dump(D, open(P('data', 'tokkatsu.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

t = open(P('mock', 'template_tokkatsu.html'), encoding='utf-8').read()
assert t.count('__DATA__') == 1
out = P('mock', '見本_学習指導要領_特活_v1.html')
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, ensure_ascii=False).replace('</', '<\\/')))
print('書き出し', out, os.path.getsize(out), 'バイト')
# 公開する所（GitHub Pages の docs/）にも同じものを置く。入口は docs/index.html（教科のリンク集）
os.makedirs(P('docs', 'tokkatsu'), exist_ok=True)
open(P('docs', 'tokkatsu', 'index.html'), 'w', encoding='utf-8').write(open(out, encoding='utf-8').read())
print('公開用', P('docs', 'tokkatsu', 'index.html'))
