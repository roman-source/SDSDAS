from __future__ import annotations
import csv, json, re, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / 'social_farm_dashboard.html'
DATA_VK = BASE / 'data' / 'vk'
META = {
    'vk': {'label': 'ВКонтакте', 'color': '#0077FF', 'folder': 'data/vk', 'status': 'Активна'},
    'youtube': {'label': 'YouTube', 'color': '#FF3131', 'folder': 'data/youtube', 'status': 'Ждет CSV'},
    'instagram': {'label': 'Instagram', 'color': '#F97316', 'folder': 'data/instagram', 'status': 'Ждет CSV'},
    'tiktok': {'label': 'TikTok', 'color': '#14B8A6', 'folder': 'data/tiktok', 'status': 'Ждет CSV'},
}
ORDER = list(META)


def to_float(v):
    if v is None:
        return 0.0
    s = str(v).strip().replace('%', '').replace(',', '.').replace('\xa0', '')
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def to_int(v):
    return int(round(to_float(v)))


def strip_html(v):
    text = '' if v is None else str(v)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text)).strip()


def parse_dt(v):
    text = (v or '').replace(' MSK', '').strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None


def fmt_day(v):
    return 'Нет даты' if not v else v.strftime('%d.%m')


def fmt_dt(v):
    return 'Нет даты' if not v else v.strftime('%d.%m.%Y %H:%M')


def account_name(path: Path) -> str:
    stem = path.stem
    return stem.split(' - ', 1)[1].strip() if ' - ' in stem else stem


def load_vk_posts():
    rows = []
    for path in sorted(DATA_VK.glob('*.csv')):
        account = account_name(path)
        with path.open('r', encoding='utf-8-sig', newline='') as fh:
            for row in csv.DictReader(fh):
                ts = parse_dt(row.get('Date'))
                media_views = to_int(row.get('media_views'))
                media_likes = to_int(row.get('media_likes'))
                post_likes = to_int(row.get('post_likes'))
                reposts = to_int(row.get('reposts'))
                comments = to_int(row.get('Comments'))
                post_views = to_int(row.get('post_views'))
                media_eng = media_likes + reposts + comments
                post_eng = post_likes + reposts + comments
                text = strip_html(row.get('Text'))
                rows.append({
                    'platformKey': 'vk',
                    'platformLabel': META['vk']['label'],
                    'platformColor': META['vk']['color'],
                    'accountName': account,
                    'subscribers': to_int(row.get('Subscribers')),
                    'mediaKind': row.get('media_kind') or 'Без типа',
                    'publishedAt': ts.isoformat() if ts else None,
                    '_ts': ts,
                    'publishedAtLabel': fmt_dt(ts),
                    'publishedDay': ts.strftime('%Y-%m-%d') if ts else None,
                    'dayLabel': fmt_day(ts),
                    'mediaViews': media_views,
                    'postViews': post_views,
                    'mediaLikes': media_likes,
                    'postLikes': post_likes,
                    'reposts': reposts,
                    'comments': comments,
                    'mediaEngagements': media_eng,
                    'postEngagements': post_eng,
                    'erView': round(media_eng / media_views * 100, 2) if media_views else 0.0,
                    'erPost': round(post_eng / post_views * 100, 2) if post_views else 0.0,
                    'vrPost': round(media_views / post_views, 2) if post_views else 0.0,
                    'text': text,
                    'textPreview': text if len(text) < 120 else text[:119].rstrip() + '…',
                    'postUrl': row.get('Post Url') or '',
                })
    rows.sort(key=lambda r: (r['_ts'] or datetime.min, r['mediaViews']), reverse=True)
    return rows


def summarize(rows):
    if not rows:
        return {'posts': 0, 'accounts': 0, 'activeDays': 0, 'subscribersTotal': 0, 'totalMediaViews': 0, 'totalMediaLikes': 0, 'totalReposts': 0, 'totalComments': 0, 'totalEngagements': 0, 'avgMediaViews': 0.0, 'medianMediaViews': 0.0, 'weightedErView': 0.0, 'weightedErPost': 0.0, 'weightedVrPost': 0.0, 'macroErView': 0.0, 'macroErPost': 0.0, 'viewsPerSubscriber': 0.0, 'top3ViewShare': 0.0, 'startDay': 'Нет даты', 'endDay': 'Нет даты'}
    subs_by_account, days = {}, set()
    total_views = total_likes = total_reposts = total_comments = total_eng = 0
    total_post_views = total_post_eng = 0
    er_view_values, er_post_values, views = [], [], []
    dates = []
    for r in rows:
        subs_by_account[r['accountName']] = max(subs_by_account.get(r['accountName'], 0), r['subscribers'])
        if r['publishedDay']:
            days.add(r['publishedDay'])
        if r['_ts']:
            dates.append(r['_ts'])
        total_views += r['mediaViews']
        total_likes += r['mediaLikes']
        total_reposts += r['reposts']
        total_comments += r['comments']
        total_eng += r['mediaEngagements']
        total_post_views += r['postViews']
        total_post_eng += r['postEngagements']
        er_view_values.append(r['erView'])
        er_post_values.append(r['erPost'])
        views.append(r['mediaViews'])
    total_subs = sum(subs_by_account.values())
    return {
        'posts': len(rows), 'accounts': len(subs_by_account), 'activeDays': len(days), 'subscribersTotal': total_subs,
        'totalMediaViews': total_views, 'totalMediaLikes': total_likes, 'totalReposts': total_reposts, 'totalComments': total_comments,
        'totalEngagements': total_eng, 'avgMediaViews': round(total_views / len(rows), 2), 'medianMediaViews': round(statistics.median(views), 2),
        'weightedErView': round(total_eng / total_views * 100, 2) if total_views else 0.0,
        'weightedErPost': round(total_post_eng / total_post_views * 100, 2) if total_post_views else 0.0,
        'weightedVrPost': round(total_views / total_post_views, 2) if total_post_views else 0.0,
        'macroErView': round(sum(er_view_values) / len(er_view_values), 2) if er_view_values else 0.0,
        'macroErPost': round(sum(er_post_values) / len(er_post_values), 2) if er_post_values else 0.0,
        'viewsPerSubscriber': round(total_views / total_subs, 2) if total_subs else 0.0,
        'top3ViewShare': round(sum(sorted(views, reverse=True)[:3]) / total_views * 100, 2) if total_views else 0.0,
        'startDay': fmt_day(min(dates)) if dates else 'Нет даты', 'endDay': fmt_day(max(dates)) if dates else 'Нет даты',
    }


def daily_rows(rows, field):
    buckets = {}
    for r in rows:
        key = (r['publishedDay'] or 'Нет даты', r[field])
        if key not in buckets:
            buckets[key] = {'date': key[0], 'label': r['dayLabel'], 'group': r[field], 'views': 0, 'posts': 0}
        buckets[key]['views'] += r['mediaViews']
        buckets[key]['posts'] += 1
    return sorted(buckets.values(), key=lambda x: (str(x['date']), str(x['group'])))


def accounts_payload(rows):
    grouped = defaultdict(list)
    for r in rows:
        grouped[r['accountName']].append(r)
    out = []
    for name, group in grouped.items():
        s = summarize(group)
        out.append({'accountName': name, 'posts': s['posts'], 'subscribersTotal': s['subscribersTotal'], 'totalMediaViews': s['totalMediaViews'], 'avgMediaViews': s['avgMediaViews'], 'weightedErView': s['weightedErView'], 'weightedErPost': s['weightedErPost'], 'lastPostAt': group[0]['publishedAtLabel']})
    return sorted(out, key=lambda x: x['totalMediaViews'], reverse=True)


def payload():
    vk_rows = load_vk_posts()
    platforms = []
    for key in ORDER:
        rows = vk_rows if key == 'vk' else []
        platforms.append({'key': key, 'label': META[key]['label'], 'color': META[key]['color'], 'folder': META[key]['folder'], 'status': 'Активна' if rows else META[key]['status'], 'hasData': bool(rows), 'summary': summarize(rows)})
    summary = summarize(vk_rows)
    clean_rows = [{k: v for k, v in r.items() if k != '_ts'} for r in vk_rows]
    return {'generatedAt': datetime.now().strftime('%d.%m.%Y %H:%M'), 'summary': summary, 'platforms': platforms, 'overviewDaily': daily_rows(vk_rows, 'platformLabel'), 'topPosts': sorted(clean_rows, key=lambda x: x['mediaViews'], reverse=True)[:10], 'vkSummary': summary, 'vkDaily': daily_rows(vk_rows, 'accountName'), 'vkAccounts': accounts_payload(vk_rows), 'allPosts': clean_rows, 'accounts': sorted({r['accountName'] for r in clean_rows}), 'mediaKinds': sorted({r['mediaKind'] for r in clean_rows})}

HTML = r'''<!doctype html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Social Farm Analytics</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet"><style>:root{--bg:radial-gradient(circle at top left,rgba(0,119,255,.18),transparent 30%),radial-gradient(circle at top right,rgba(249,115,22,.18),transparent 26%),radial-gradient(circle at bottom left,rgba(45,212,191,.16),transparent 24%),linear-gradient(180deg,#f6f8f2 0%,#eff4ef 48%,#e8f1ee 100%);--surface:rgba(255,255,255,.8);--line:rgba(148,163,184,.18);--ink:#0f172a;--muted:#64748b;--copy:#475569}*{box-sizing:border-box}body{margin:0;font-family:Manrope,sans-serif;color:var(--ink);background:var(--bg)}body:before{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(15,23,42,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(15,23,42,.035) 1px,transparent 1px);background-size:34px 34px;mask-image:radial-gradient(circle at center,black 16%,transparent 78%);opacity:.65}.page{max-width:1380px;margin:0 auto;padding:24px 18px 48px;position:relative}.hero,.card{background:var(--surface);border:1px solid rgba(255,255,255,.92);box-shadow:0 24px 72px rgba(15,23,42,.08);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}.hero{border-radius:30px;padding:28px;background:radial-gradient(circle at 0% 0%,rgba(89,195,255,.35),transparent 28%),radial-gradient(circle at 100% 0%,rgba(249,115,22,.26),transparent 24%),linear-gradient(135deg,rgba(255,255,255,.92),rgba(244,249,247,.82))}.hero-grid,.grid2,.metrics{display:grid;gap:16px}.hero-grid{grid-template-columns:1.3fr .9fr}.metrics{grid-template-columns:repeat(4,minmax(0,1fr))}.kicker,.pill,.status{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.78);border:1px solid var(--line);color:#334155;font-size:13px;font-weight:700}.kicker{background:rgba(15,23,42,.05);font-size:12px;letter-spacing:.14em;text-transform:uppercase}.title,h2{font-family:'Space Grotesk',sans-serif;letter-spacing:-.04em}.title{margin:16px 0 0;font-size:clamp(2.6rem,5vw,4rem);line-height:.98}.copy{margin:16px 0 0;color:var(--copy);line-height:1.75}.pills{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}.mini,.metric{border-radius:24px;padding:16px;background:rgba(255,255,255,.84);border:1px solid rgba(255,255,255,.95);box-shadow:0 18px 54px rgba(15,23,42,.06)}.metric small,.muted{color:var(--muted)}.metric b,.mini b{display:block;margin-top:8px;font-size:30px;font-family:'Space Grotesk',sans-serif;letter-spacing:-.04em}.tabs{display:flex;flex-wrap:wrap;gap:12px;margin-top:20px}.tab{min-width:170px;padding:14px 16px;border-radius:22px;border:1px solid var(--line);background:rgba(255,255,255,.72);cursor:pointer;box-shadow:0 16px 40px rgba(15,23,42,.05);text-align:left}.tab.active{background:linear-gradient(135deg,rgba(0,119,255,.12),rgba(45,212,191,.18));border-color:rgba(0,119,255,.28)}.tab strong{display:block;font-family:'Space Grotesk',sans-serif;font-size:20px}.tab span{display:block;margin-top:6px;color:var(--copy);font-size:13px;line-height:1.55}.panel{display:none;margin-top:20px}.panel.active{display:block}.stack{display:grid;gap:16px}.grid2{grid-template-columns:repeat(2,minmax(0,1fr))}.card{border-radius:28px;padding:18px}.head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:14px}.head p{margin:6px 0 0;color:var(--muted);line-height:1.7}.chart{min-height:330px;position:relative}.table{overflow:auto;border-radius:20px;border:1px solid rgba(148,163,184,.16);background:rgba(255,255,255,.72)}table{width:100%;min-width:820px;border-collapse:collapse}th,td{padding:12px 14px;text-align:left;border-bottom:1px solid rgba(148,163,184,.14);vertical-align:top}th{position:sticky;top:0;background:rgba(241,245,249,.95);color:var(--muted);font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}td{color:var(--copy);font-size:14px;line-height:1.6}td strong{color:var(--ink)}.dot{display:inline-block;width:10px;height:10px;border-radius:999px;margin-right:8px;vertical-align:middle}.badge{display:inline-flex;align-items:center;padding:6px 10px;border-radius:999px;background:rgba(15,23,42,.05);font-size:12px;font-weight:700;color:#334155}.link{color:#0077FF;font-weight:700;text-decoration:none}.link:hover{text-decoration:underline}.controls{display:grid;grid-template-columns:1.4fr repeat(3,minmax(0,.8fr));gap:12px}.field{display:grid;gap:8px}.field label{color:var(--muted);font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.field input,.field select{width:100%;border:1px solid rgba(148,163,184,.22);border-radius:16px;padding:12px 13px;background:rgba(255,255,255,.88);font:inherit;color:var(--ink)}.empty{border-radius:24px;padding:22px;background:radial-gradient(circle at top left,rgba(249,115,22,.18),transparent 28%),linear-gradient(180deg,rgba(255,255,255,.92),rgba(247,250,252,.78));border:1px solid rgba(255,255,255,.9);color:var(--copy);line-height:1.8}.empty strong{display:block;margin-bottom:8px;color:var(--ink);font-family:'Space Grotesk',sans-serif;font-size:1.3rem}@media (max-width:1100px){.hero-grid,.grid2,.metrics,.controls{grid-template-columns:1fr 1fr}}@media (max-width:820px){.page{padding:14px 12px 36px}.hero,.card{padding:16px}.hero-grid,.grid2,.metrics,.controls,.tabs{grid-template-columns:1fr;display:grid}}</style></head><body><div class="page"><header class="hero"><div class="hero-grid"><div><div class="kicker">Static HTML • Streamlit style</div><h1 class="title">Social Farm Analytics</h1><p class="copy">Отдельный HTML-дашборд по тем же CSV, что и текущая Streamlit-витрина: overview, ВКонтакте, общая таблица всех постов и просмотры по дням прямо внутри страницы.</p><div class="pills"><span class="pill" id="g"></span><span class="pill" id="p"></span><span class="pill" id="v"></span><span class="pill" id="e"></span></div></div><div class="metrics" id="hero"></div></div></header><nav class="tabs"><button class="tab active" data-tab="overview"><strong>Обзор</strong><span>Общая картина по данным</span></button><button class="tab" data-tab="vk"><strong>ВКонтакте</strong><span>Активная платформа</span></button><button class="tab" data-tab="posts"><strong>Все посты</strong><span>Фильтры и дневные просмотры</span></button><button class="tab" data-tab="youtube"><strong>YouTube</strong><span>Папка уже готова</span></button><button class="tab" data-tab="instagram"><strong>Instagram</strong><span>Раздел на вырост</span></button><button class="tab" data-tab="tiktok"><strong>TikTok</strong><span>Ждет CSV</span></button></nav><section class="panel active" data-panel="overview"><div class="stack"><article class="card"><div class="head"><div><h2>Общий overview</h2><p>Суммарные метрики, дневная динамика и сравнение платформ по текущим данным.</p></div><span class="status" id="sum"></span></div><div class="metrics" id="overview-metrics"></div></article><div class="grid2"><article class="card"><div class="head"><div><h2>Просмотры по дням</h2><p>Динамика по всем активным платформам.</p></div></div><div class="chart"><canvas id="overview-chart"></canvas></div></article><article class="card"><div class="head"><div><h2>Сводка по платформам</h2><p>Totals и weighted-метрики по каждой соцсети.</p></div></div><div class="table"><table><thead><tr><th>Платформа</th><th>Статус</th><th>Папка</th><th>Посты</th><th>Просмотры</th><th>Средние</th><th>ER View</th><th>ER Post</th></tr></thead><tbody id="platform-body"></tbody></table></div></article></div><article class="card"><div class="head"><div><h2>Топ-посты</h2><p>Лучшие публикации по просмотрам среди всех активных CSV.</p></div></div><div class="table"><table><thead><tr><th>Пост</th><th>Дата</th><th>Просмотры</th><th>Лайки</th><th>Репосты</th><th>ER View</th></tr></thead><tbody id="top-body"></tbody></table></div></article></div></section><section class="panel" data-panel="vk"><div class="stack"><article class="card"><div class="head"><div><h2>ВКонтакте</h2><p>Текущий рабочий контур: три CSV, разбивка по аккаунтам и отдельный дневной график.</p></div><span class="status" id="vk-sum"></span></div><div class="metrics" id="vk-metrics"></div></article><div class="grid2"><article class="card"><div class="head"><div><h2>VK просмотры по дням</h2><p>Разбивка по аккаунтам внутри платформы.</p></div></div><div class="chart"><canvas id="vk-chart"></canvas></div></article><article class="card"><div class="head"><div><h2>Аккаунты VK</h2><p>Сводка по каждой ферме: просмотры, средние и weighted ER.</p></div></div><div class="table"><table><thead><tr><th>Аккаунт</th><th>Посты</th><th>Подписчики</th><th>Просмотры</th><th>Средние</th><th>ER View</th><th>ER Post</th><th>Последний пост</th></tr></thead><tbody id="accounts-body"></tbody></table></div></article></div></div></section><section class="panel" data-panel="posts"><div class="stack"><article class="card"><div class="head"><div><h2>Все посты</h2><p>Поиск по тексту, фильтры и просмотры по дням по текущей выборке.</p></div><span class="status" id="flt"></span></div><div class="controls"><div class="field"><label>Поиск</label><input id="q" type="search" placeholder="мем, AdsGram, wall-..."></div><div class="field"><label>Платформа</label><select id="platform"></select></div><div class="field"><label>Аккаунт</label><select id="account"></select></div><div class="field"><label>Тип</label><select id="kind"></select></div></div></article><article class="card"><div class="head"><div><h2>Просмотры по дням по фильтру</h2><p>График сразу реагирует на выбранные фильтры и поиск.</p></div></div><div class="chart"><canvas id="filter-chart"></canvas></div></article><article class="card"><div class="head"><div><h2>Таблица постов</h2><p>Новые публикации сверху, текст сокращен до превью.</p></div><span class="status" id="count"></span></div><div class="table"><table><thead><tr><th>Платформа</th><th>Аккаунт</th><th>Дата</th><th>Тип</th><th>Media Views</th><th>Likes</th><th>Репосты</th><th>Комментарии</th><th>ER View</th><th>ER Post</th><th>Текст</th><th>Пост</th></tr></thead><tbody id="posts-body"></tbody></table></div></article></div></section><section class="panel" data-panel="youtube"><div class="card"><div class="empty" id="youtube-empty"></div></div></section><section class="panel" data-panel="instagram"><div class="card"><div class="empty" id="instagram-empty"></div></div></section><section class="panel" data-panel="tiktok"><div class="card"><div class="empty" id="tiktok-empty"></div></div></section></div><script id="data" type="application/json">__DATA__</script><script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script><script>const db=JSON.parse(document.getElementById('data').textContent),pm=Object.fromEntries(db.platforms.map(p=>[p.key,p])),charts={};const fi=v=>new Intl.NumberFormat('ru-RU').format(Math.round(Number(v||0))),ff=(v,d=2)=>new Intl.NumberFormat('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d}).format(Number(v||0)),fp=(v,d=2)=>`${ff(v,d)}%`,fc=v=>new Intl.NumberFormat('ru-RU',{notation:'compact',maximumFractionDigits:1}).format(Number(v||0)),esc=v=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');function grad(ctx,a,b){const g=ctx.createLinearGradient(0,0,0,320);g.addColorStop(0,a);g.addColorStop(1,b);return g}function opts(){return{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#334155',font:{family:'Manrope',weight:700}}},tooltip:{backgroundColor:'rgba(15,23,42,.92)',titleColor:'#fff',bodyColor:'#E2E8F0',padding:12,cornerRadius:14}},scales:{x:{ticks:{color:'#64748b',maxRotation:0,autoSkip:true},grid:{display:false}},y:{ticks:{color:'#64748b',callback:v=>fc(v)},grid:{color:'rgba(148,163,184,.16)'}}}}}function kill(k){if(charts[k])charts[k].destroy()}function tab(t){document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===t));document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.dataset.panel===t))}document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>tab(b.dataset.tab));document.getElementById('g').textContent=`Сгенерировано: ${db.generatedAt}`;document.getElementById('p').textContent=`Период: ${db.summary.startDay} → ${db.summary.endDay}`;document.getElementById('v').textContent=`Просмотры: ${fc(db.summary.totalMediaViews)}`;document.getElementById('e').textContent=`Weighted ER View: ${fp(db.summary.weightedErView)}`;document.getElementById('sum').textContent=`${fi(db.summary.posts)} постов`;document.getElementById('vk-sum').textContent=`${fi(db.vkSummary.posts)} постов`;function cards(node,items){document.getElementById(node).innerHTML=items.map(i=>`<div class="metric"><small>${esc(i.l)}</small><b>${esc(i.v)}</b><div class="muted">${esc(i.n)}</div></div>`).join('')}cards('hero',[{l:'Всего просмотров',v:fc(db.summary.totalMediaViews),n:`${fi(db.summary.posts)} постов и ${fi(db.summary.accounts)} аккаунтов`},{l:'Средние просмотры',v:fi(db.summary.avgMediaViews),n:`Медиана ${fi(db.summary.medianMediaViews)}`},{l:'Weighted ER Post',v:fp(db.summary.weightedErPost),n:`Macro ER Post ${fp(db.summary.macroErPost)}`},{l:'Weighted VR Post',v:ff(db.summary.weightedVrPost,2),n:`Views/sub ${ff(db.summary.viewsPerSubscriber,2)}`}]);cards('overview-metrics',[{l:'Подписчики',v:fi(db.summary.subscribersTotal),n:'Сумма максимумов по аккаунтам'},{l:'Engagements',v:fc(db.summary.totalEngagements),n:`Лайки ${fi(db.summary.totalMediaLikes)} • Репосты ${fi(db.summary.totalReposts)}`},{l:'Top 3 share',v:fp(db.summary.top3ViewShare),n:'Доля трех самых крупных постов'},{l:'Weighted ER View',v:fp(db.summary.weightedErView),n:`Macro ER View ${fp(db.summary.macroErView)}`}]);cards('vk-metrics',[{l:'VK просмотры',v:fc(db.vkSummary.totalMediaViews),n:`Подписчики ${fi(db.vkSummary.subscribersTotal)}`},{l:'Средние просмотры',v:fi(db.vkSummary.avgMediaViews),n:`Медиана ${fi(db.vkSummary.medianMediaViews)}`},{l:'Weighted ER View',v:fp(db.vkSummary.weightedErView),n:`Macro ${fp(db.vkSummary.macroErView)}`},{l:'Weighted ER Post',v:fp(db.vkSummary.weightedErPost),n:`Top 3 share ${fp(db.vkSummary.top3ViewShare)}`}]);document.getElementById('platform-body').innerHTML=db.platforms.map(p=>`<tr><td><span class="badge"><span class="dot" style="background:${p.color}"></span>${esc(p.label)}</span></td><td><strong>${esc(p.status)}</strong></td><td>${esc(p.folder)}</td><td>${fi(p.summary.posts)}</td><td>${fi(p.summary.totalMediaViews)}</td><td>${fi(p.summary.avgMediaViews)}</td><td>${fp(p.summary.weightedErView)}</td><td>${fp(p.summary.weightedErPost)}</td></tr>`).join('');document.getElementById('top-body').innerHTML=db.topPosts.map(p=>`<tr><td><span class="badge"><span class="dot" style="background:${p.platformColor}"></span>${esc(p.platformLabel)}</span><div><strong>${esc(p.accountName)}</strong></div><div class="muted">${esc(p.textPreview||'Без текста')}</div></td><td>${esc(p.publishedAtLabel)}</td><td><strong>${fi(p.mediaViews)}</strong></td><td>${fi(p.mediaLikes)}</td><td>${fi(p.reposts)}</td><td>${fp(p.erView)}</td></tr>`).join('');document.getElementById('accounts-body').innerHTML=db.vkAccounts.map(a=>`<tr><td><strong>${esc(a.accountName)}</strong></td><td>${fi(a.posts)}</td><td>${fi(a.subscribersTotal)}</td><td>${fi(a.totalMediaViews)}</td><td>${fi(a.avgMediaViews)}</td><td>${fp(a.weightedErView)}</td><td>${fp(a.weightedErPost)}</td><td>${esc(a.lastPostAt)}</td></tr>`).join('');['youtube','instagram','tiktok'].forEach(k=>{document.getElementById(`${k}-empty`).innerHTML=`<strong>${pm[k].label} пока не активирован</strong>Папка <strong>${pm[k].folder}</strong> уже готова. Как только туда попадут CSV, в этот раздел можно будет подключить те же totals, средние показатели и просмотры по дням.`});function lineChart(id,rows){kill(id);const labels=[...new Set(rows.map(r=>r.label))],groups=[...new Set(rows.map(r=>r.group))],ctx=document.getElementById(id).getContext('2d');charts[id]=new Chart(ctx,{type:'line',data:{labels,datasets:groups.map((g,i)=>{const vals=new Map(rows.filter(r=>r.group===g).map(r=>[r.label,r.views]));const color=(Object.values(pm).find(p=>p.label===g)||{}).color||['#0077FF','#14B8A6','#F97316','#EF4444','#8B5CF6'][i%5];return{label:g,data:labels.map(l=>vals.get(l)||0),borderColor:color,backgroundColor:grad(ctx,`${color}33`,`${color}03`),fill:i===0,tension:.35,borderWidth:2.4,pointRadius:0,pointHoverRadius:4}})},options:opts()})}lineChart('overview-chart',db.overviewDaily);lineChart('vk-chart',db.vkDaily);const ps=document.getElementById('platform'),ac=document.getElementById('account'),kd=document.getElementById('kind'),qq=document.getElementById('q');function fill(sel,items,label,map){sel.innerHTML=['<option value="all">'+label+'</option>'].concat(items.map(v=>`<option value="${esc(v)}">${esc(map?map(v):v)}</option>`)).join('')}fill(ps,db.platforms.filter(p=>p.hasData).map(p=>p.key),'Все платформы',v=>pm[v].label);fill(ac,db.accounts,'Все аккаунты');fill(kd,db.mediaKinds,'Все типы');[ps,ac,kd].forEach(el=>el.onchange=renderPosts);qq.oninput=renderPosts;function filtered(){const q=qq.value.trim().toLowerCase();return db.allPosts.filter(p=>(ps.value==='all'||p.platformKey===ps.value)&&(ac.value==='all'||p.accountName===ac.value)&&(kd.value==='all'||p.mediaKind===kd.value)&&(!q||[p.platformLabel,p.accountName,p.mediaKind,p.text,p.postUrl].join(' ').toLowerCase().includes(q)))}function daily(posts){const m=new Map();posts.forEach(p=>{const k=p.publishedDay||'Нет даты';if(!m.has(k))m.set(k,{date:k,label:p.dayLabel,views:0,posts:0});const r=m.get(k);r.views+=Number(p.mediaViews||0);r.posts+=1});return [...m.values()].sort((a,b)=>String(a.date).localeCompare(String(b.date)))}function renderPosts(){const rows=filtered(),views=rows.reduce((s,p)=>s+Number(p.mediaViews||0),0);document.getElementById('flt').textContent=`${fi(rows.length)} постов • ${fc(views)} views`;document.getElementById('count').textContent=`${fi(rows.length)} строк`;document.getElementById('posts-body').innerHTML=rows.length?rows.map(p=>`<tr><td><span class="badge"><span class="dot" style="background:${p.platformColor}"></span>${esc(p.platformLabel)}</span></td><td><strong>${esc(p.accountName)}</strong></td><td>${esc(p.publishedAtLabel)}</td><td>${esc(p.mediaKind)}</td><td><strong>${fi(p.mediaViews)}</strong></td><td>${fi(p.mediaLikes)}</td><td>${fi(p.reposts)}</td><td>${fi(p.comments)}</td><td>${fp(p.erView)}</td><td>${fp(p.erPost)}</td><td title="${esc(p.text)}">${esc(p.textPreview||'Без текста')}</td><td>${p.postUrl?`<a class="link" href="${esc(p.postUrl)}" target="_blank" rel="noreferrer">Открыть</a>`:'<span class="muted">Нет ссылки</span>'}</td></tr>`).join(''):`<tr><td colspan="12"><div class="empty"><strong>Ничего не найдено</strong>Сними часть фильтров или очисти поиск, чтобы снова увидеть публикации.</div></td></tr>`;kill('filter');const d=daily(rows),ctx=document.getElementById('filter-chart').getContext('2d');charts.filter=new Chart(ctx,{data:{labels:d.map(r=>r.label),datasets:[{type:'line',label:'Media views',data:d.map(r=>r.views),borderColor:'#0077FF',backgroundColor:grad(ctx,'rgba(0,119,255,.28)','rgba(0,119,255,.02)'),fill:true,tension:.35,borderWidth:2.4,pointRadius:0,pointHoverRadius:4,yAxisID:'y'},{type:'bar',label:'Посты',data:d.map(r=>r.posts),backgroundColor:'rgba(20,184,166,.3)',borderRadius:999,maxBarThickness:18,yAxisID:'y1'}]},options:{...opts(),scales:{x:{ticks:{color:'#64748b',maxRotation:0,autoSkip:true},grid:{display:false}},y:{ticks:{color:'#64748b',callback:v=>fc(v)},grid:{color:'rgba(148,163,184,.16)'}},y1:{position:'right',beginAtZero:true,ticks:{color:'#94a3b8',precision:0},grid:{display:false}}}}})}renderPosts();</script></body></html>'''

def build_dashboard_html() -> str:
    return HTML.replace('__DATA__', json.dumps(payload(), ensure_ascii=False))


def write_dashboard_html(output_path: Path = OUT) -> Path:
    output_path.write_text(build_dashboard_html(), encoding='utf-8')
    return output_path


if __name__ == '__main__':
    print(write_dashboard_html())



