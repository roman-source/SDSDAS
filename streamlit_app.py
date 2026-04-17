from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Callable

import altair as alt
import pandas as pd
import streamlit as st

from app.analytics import PLATFORM_META, PLATFORM_ORDER, load_repository_data, summarize_groups, summarize_posts


BASE_DIR = Path(__file__).resolve().parent
PALETTE = ["#0077FF", "#2DD4BF", "#F97316", "#EF4444", "#A855F7", "#0EA5E9"]


st.set_page_config(
    page_title="Social Farm Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

alt.data_transformers.disable_max_rows()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
            --bg:
                radial-gradient(circle at top left, rgba(0,119,255,0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(249,115,22,0.18), transparent 26%),
                radial-gradient(circle at bottom left, rgba(45,212,191,0.16), transparent 24%),
                linear-gradient(180deg, #f6f8f2 0%, #eff4ef 48%, #e8f1ee 100%);
            --surface: rgba(255,255,255,0.80);
            --line: rgba(148,163,184,0.18);
            --ink: #0f172a;
            --muted: #64748b;
            --copy: #475569;
        }

        html, body, [class*="css"] {
            font-family: "Manrope", sans-serif;
            color: var(--ink);
        }

        [data-testid="stAppViewContainer"] {
            background: var(--bg);
        }

        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(15,23,42,0.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(15,23,42,0.035) 1px, transparent 1px);
            background-size: 34px 34px;
            mask-image: radial-gradient(circle at center, black 16%, transparent 78%);
            opacity: 0.65;
        }

        [data-testid="stHeader"] {
            background: rgba(0, 0, 0, 0);
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }

        .block-container {
            max-width: 1380px;
            padding: 24px 18px 48px;
            position: relative;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.04em;
            color: var(--ink);
        }

        .hero {
            border-radius: 30px;
            padding: 28px;
            background:
                radial-gradient(circle at 0% 0%, rgba(89,195,255,0.35), transparent 28%),
                radial-gradient(circle at 100% 0%, rgba(249,115,22,0.26), transparent 24%),
                linear-gradient(135deg, rgba(255,255,255,0.92), rgba(244,249,247,0.82));
            border: 1px solid rgba(255,255,255,0.92);
            box-shadow: 0 24px 72px rgba(15,23,42,0.08);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            margin-bottom: 20px;
        }

        .hero-grid, .metric-grid, .hero-metrics {
            display: grid;
            gap: 16px;
        }

        .hero-grid {
            grid-template-columns: 1.3fr 0.9fr;
            align-items: start;
        }

        .hero-metrics,
        .metric-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .kicker, .pill, .status, .link-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            border: 1px solid var(--line);
            color: #334155;
            font-size: 13px;
            font-weight: 700;
            text-decoration: none;
        }

        .kicker {
            background: rgba(15,23,42,0.05);
            font-size: 12px;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .pill, .status, .link-pill {
            background: rgba(255,255,255,0.78);
        }

        .title {
            margin: 16px 0 0;
            font-size: clamp(2.6rem, 5vw, 4rem);
            line-height: 0.98;
        }

        .copy {
            margin: 16px 0 0;
            color: var(--copy);
            line-height: 1.75;
            max-width: 760px;
        }

        .pills {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }

        .mini,
        .metric-card {
            border-radius: 24px;
            padding: 16px;
            background: rgba(255,255,255,0.84);
            border: 1px solid rgba(255,255,255,0.95);
            box-shadow: 0 18px 54px rgba(15,23,42,0.06);
        }

        .mini-label,
        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .mini-value,
        .metric-value {
            display: block;
            margin-top: 8px;
            font-size: 30px;
            line-height: 1.05;
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.04em;
        }

        .mini-note,
        .metric-note {
            margin-top: 10px;
            color: var(--copy);
            line-height: 1.65;
            font-size: 0.92rem;
        }

        [data-baseweb="tab-list"] {
            gap: 12px;
            margin-top: 20px;
            margin-bottom: 20px;
            background: transparent;
        }

        [data-baseweb="tab"] {
            min-height: 60px;
            padding: 0 18px;
            border-radius: 22px;
            background: rgba(255,255,255,0.72);
            border: 1px solid var(--line);
            box-shadow: 0 16px 40px rgba(15,23,42,0.05);
            color: var(--ink);
            font-family: "Space Grotesk", sans-serif;
            font-size: 1rem;
        }

        [aria-selected="true"][data-baseweb="tab"] {
            background: linear-gradient(135deg, rgba(0,119,255,0.12), rgba(45,212,191,0.18));
            border-color: rgba(0,119,255,0.28);
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface);
            border: 1px solid rgba(255,255,255,0.92);
            border-radius: 28px;
            box-shadow: 0 24px 72px rgba(15,23,42,0.08);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            padding: 8px 12px 14px;
        }

        .card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 18px;
        }

        .card-head h2 {
            margin: 0;
            font-size: 1.5rem;
        }

        .card-head p {
            margin: 8px 0 0;
            color: var(--copy);
            line-height: 1.7;
        }

        .table-wrap {
            overflow-x: auto;
            border-radius: 22px;
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.72);
        }

        .dashboard-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 720px;
        }

        .dashboard-table th,
        .dashboard-table td {
            padding: 12px 14px;
            text-align: left;
            font-size: 0.92rem;
            border-bottom: 1px solid rgba(148,163,184,0.14);
            vertical-align: top;
        }

        .dashboard-table th {
            font-family: "Space Grotesk", sans-serif;
            font-size: 0.95rem;
            background: rgba(248,250,252,0.92);
            position: sticky;
            top: 0;
            z-index: 1;
        }

        .dashboard-table tr:hover td {
            background: rgba(248,250,252,0.72);
        }

        .table-note {
            margin-top: 12px;
            color: var(--muted);
            font-size: 0.88rem;
        }

        .empty {
            border-radius: 24px;
            padding: 22px;
            background:
                radial-gradient(circle at top left, rgba(249,115,22,0.18), transparent 28%),
                linear-gradient(180deg, rgba(255,255,255,0.92), rgba(247,250,252,0.78));
            border: 1px solid rgba(255,255,255,0.9);
            color: var(--copy);
            line-height: 1.8;
        }

        .empty strong {
            display: block;
            color: var(--ink);
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.35rem;
            margin-bottom: 6px;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input {
            border-radius: 18px !important;
            background: rgba(255,255,255,0.78) !important;
            border: 1px solid var(--line) !important;
            min-height: 48px;
        }

        label[data-testid="stWidgetLabel"] p {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        [data-testid="stVegaLiteChart"] {
            background: transparent;
        }

        [data-testid="stDownloadButton"] button {
            width: 100%;
            min-height: 50px;
            border-radius: 18px;
            border: 1px solid rgba(0,119,255,0.18);
            background: linear-gradient(135deg, rgba(0,119,255,0.92), rgba(14,165,233,0.88));
            color: white;
            font-weight: 700;
            box-shadow: 0 18px 40px rgba(0,119,255,0.22);
        }

        @media (max-width: 980px) {
            .hero-grid,
            .hero-metrics,
            .metric-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def get_repository_data(base_dir: str) -> dict[str, object]:
    return load_repository_data(Path(base_dir))


def fmt_int(value: float | int) -> str:
    if pd.isna(value):
        return "0"
    return f"{int(round(float(value))):,}".replace(",", " ")


def fmt_float(value: float | int, digits: int = 2) -> str:
    if pd.isna(value):
        return "0"
    return f"{float(value):,.{digits}f}".replace(",", " ").replace(".", ",")


def fmt_pct(value: float | int, digits: int = 2) -> str:
    return f"{fmt_float(value, digits)}%"


def fmt_date(value: object, pattern: str = "%d.%m.%Y") -> str:
    if pd.isna(value):
        return "Нет даты"
    return pd.Timestamp(value).strftime(pattern)


def clip_text(value: object, limit: int = 120) -> str:
    if value is None or pd.isna(value):
        return "—"
    text = str(value).strip()
    if not text:
        return "—"
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 1].rstrip()}…"


def metric_card_html(label: str, value: str, note: str) -> str:
    return f"""
        <div class="metric-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
            <div class="metric-note">{escape(note)}</div>
        </div>
    """


def mini_metric_html(label: str, value: str, note: str) -> str:
    return f"""
        <div class="mini">
            <div class="mini-label">{escape(label)}</div>
            <div class="mini-value">{escape(value)}</div>
            <div class="mini-note">{escape(note)}</div>
        </div>
    """


def render_metric_grid(metrics: list[tuple[str, str, str]]) -> None:
    cards = "".join(metric_card_html(label, value, note) for label, value, note in metrics)
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_card_header(title: str, subtitle: str, status: str | None = None) -> None:
    status_html = f'<span class="status">{escape(status)}</span>' if status else ""
    st.markdown(
        f"""
        <div class="card-head">
            <div>
                <h2>{escape(title)}</h2>
                <p>{escape(subtitle)}</p>
            </div>
            {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty(message: str, title: str = "Пока пусто") -> None:
    st.markdown(
        f"""
        <div class="empty">
            <strong>{escape(title)}</strong>
            {escape(message)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def link_html(label: str, url: object) -> str:
    if url is None or pd.isna(url) or not str(url).strip():
        return escape(label)
    return f'<a class="link-pill" href="{escape(str(url))}" target="_blank">{escape(label)}</a>'


def safe_str(value: object, fallback: str = "—") -> str:
    if value is None or pd.isna(value):
        return fallback
    text = str(value).strip()
    return text or fallback


def render_html_table(
    frame: pd.DataFrame,
    *,
    formatters: dict[str, Callable[[object], str]] | None = None,
    raw_html_columns: set[str] | None = None,
    truncate_columns: dict[str, int] | None = None,
    empty_message: str = "Под текущую выборку нет строк.",
    note: str | None = None,
) -> None:
    if frame.empty:
        render_empty(empty_message)
        return

    formatters = formatters or {}
    raw_html_columns = raw_html_columns or set()
    truncate_columns = truncate_columns or {}

    header_html = "".join(f"<th>{escape(str(column))}</th>" for column in frame.columns)
    rows: list[str] = []

    for _, row in frame.iterrows():
        cells: list[str] = []
        for column in frame.columns:
            value = row[column]
            if column in formatters:
                rendered = formatters[column](value)
            elif value is None or pd.isna(value):
                rendered = "—"
            else:
                rendered = str(value)

            if column not in raw_html_columns:
                rendered = clip_text(rendered, truncate_columns.get(column, 10_000))
                rendered_html = escape(rendered)
            else:
                rendered_html = str(rendered)

            cells.append(f"<td>{rendered_html}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")

    note_html = f'<div class="table-note">{escape(note)}</div>' if note else ""
    st.markdown(
        f"""
        <div class="table-wrap">
            <table class="dashboard-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
        {note_html}
        """,
        unsafe_allow_html=True,
    )


def build_platform_summary_frame(posts: pd.DataFrame, platforms: dict[str, dict[str, object]]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key in PLATFORM_ORDER:
        platform_posts = posts[posts["platform_key"] == key] if not posts.empty else posts
        summary = summarize_posts(platform_posts)
        meta = platforms[key]
        rows.append(
            {
                "Платформа": meta["label"],
                "Статус": "Активна" if meta["has_data"] else "Ждет CSV",
                "Папка": meta["folder_path"],
                "Посты": summary["posts"],
                "Просмотры": summary["total_media_views"],
                "Средние": summary["avg_media_views"],
                "ER View": summary["weighted_er_view"],
                "ER Post": summary["weighted_er_post"],
            }
        )
    return pd.DataFrame(rows)


def build_top_posts_table(posts: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    if posts.empty:
        return pd.DataFrame(columns=["Пост", "Дата", "Просмотры", "Лайки", "Репосты", "ER View"])

    top_posts = (
        posts.sort_values(["media_views", "published_at"], ascending=[False, False])
        .head(limit)
        .copy()
    )
    labels = top_posts.apply(
        lambda row: link_html(
            f"{safe_str(row['account_name'], 'Аккаунт')} / {safe_str(row['post_code'], 'post')}",
            row["post_url"],
        ),
        axis=1,
    )
    return pd.DataFrame(
        {
            "Пост": labels,
            "Дата": top_posts["published_at"].map(lambda value: fmt_date(value, "%d.%m.%Y %H:%M")),
            "Просмотры": top_posts["media_views"],
            "Лайки": top_posts["media_likes"],
            "Репосты": top_posts["reposts"],
            "ER View": top_posts["er_view_calc"],
        }
    )


def build_vk_accounts_table(vk_posts: pd.DataFrame) -> pd.DataFrame:
    account_summary = summarize_groups(vk_posts, "account_name")
    if account_summary.empty:
        return pd.DataFrame(
            columns=["Аккаунт", "Посты", "Подписчики", "Просмотры", "Средние", "ER View", "ER Post", "Последний пост"]
        )

    return pd.DataFrame(
        {
            "Аккаунт": account_summary["account_name"],
            "Посты": account_summary["posts"],
            "Подписчики": account_summary["subscribers_total"],
            "Просмотры": account_summary["total_media_views"],
            "Средние": account_summary["avg_media_views"],
            "ER View": account_summary["weighted_er_view"],
            "ER Post": account_summary["weighted_er_post"],
            "Последний пост": account_summary["last_post_at"].map(lambda value: fmt_date(value, "%d.%m.%Y %H:%M")),
        }
    )


def filter_posts_for_posts_tab(
    posts: pd.DataFrame,
    *,
    query: str,
    platform_label: str,
    account_name: str,
    media_kind: str,
) -> pd.DataFrame:
    if posts.empty:
        return posts.copy()

    filtered = posts.copy()
    if platform_label != "Все":
        filtered = filtered[filtered["platform_label"] == platform_label]
    if account_name != "Все":
        filtered = filtered[filtered["account_name"] == account_name]
    if media_kind != "Все":
        filtered = filtered[filtered["media_kind"].fillna("без типа") == media_kind]

    if query.strip():
        haystack = (
            filtered["text_clean"].fillna("")
            + " "
            + filtered["post_url"].fillna("")
            + " "
            + filtered["account_name"].fillna("")
            + " "
            + filtered["platform_label"].fillna("")
        )
        filtered = filtered[haystack.str.casefold().str.contains(query.strip().casefold(), na=False)]

    return filtered.sort_values(["published_at", "media_views"], ascending=[False, False]).reset_index(drop=True)


def build_posts_table(posts: pd.DataFrame) -> pd.DataFrame:
    if posts.empty:
        return pd.DataFrame(
            columns=[
                "Платформа",
                "Аккаунт",
                "Дата",
                "Тип",
                "Media Views",
                "Likes",
                "Репосты",
                "Комментарии",
                "ER View",
                "ER Post",
                "Текст",
                "Пост",
            ]
        )

    return pd.DataFrame(
        {
            "Платформа": posts["platform_label"],
            "Аккаунт": posts["account_name"],
            "Дата": posts["published_at"].map(lambda value: fmt_date(value, "%d.%m.%Y %H:%M")),
            "Тип": posts["media_kind"].fillna("без типа"),
            "Media Views": posts["media_views"],
            "Likes": posts["media_likes"],
            "Репосты": posts["reposts"],
            "Комментарии": posts["comments"],
            "ER View": posts["er_view_calc"],
            "ER Post": posts["er_post_calc"],
            "Текст": posts["text_clean"].map(lambda value: clip_text(value, 160)),
            "Пост": posts.apply(lambda row: link_html("Открыть", row["post_url"]), axis=1),
        }
    )


def build_daily_views(posts: pd.DataFrame, series_field: str | None = None) -> pd.DataFrame:
    if posts.empty:
        columns = ["published_day", "media_views"]
        if series_field:
            columns.append(series_field)
        return pd.DataFrame(columns=columns)

    dated_posts = posts[posts["published_day"].notna()].copy()
    if dated_posts.empty:
        columns = ["published_day", "media_views"]
        if series_field:
            columns.append(series_field)
        return pd.DataFrame(columns=columns)

    group_fields = ["published_day"]
    if series_field:
        group_fields.append(series_field)

    return (
        dated_posts.groupby(group_fields, dropna=False)
        .agg(media_views=("media_views", "sum"))
        .reset_index()
        .sort_values("published_day")
    )


def apply_chart_theme(chart: alt.Chart) -> alt.Chart:
    return (
        chart.properties(height=320)
        .configure_view(strokeOpacity=0)
        .configure_axis(
            domain=False,
            tickColor="transparent",
            gridColor="rgba(148,163,184,0.18)",
            gridOpacity=1,
            labelColor="#64748b",
            titleColor="#64748b",
            labelFont="Manrope",
            titleFont="Manrope",
            titleFontWeight="normal",
        )
        .configure_legend(
            orient="top",
            title=None,
            labelColor="#475569",
            labelFont="Manrope",
        )
        .configure_background(color=None)
    )


def render_total_views_chart(posts: pd.DataFrame, color: str = "#0077FF") -> None:
    daily = build_daily_views(posts)
    if daily.empty:
        render_empty("В текущем наборе нет строк с датами, поэтому график пока не из чего строить.")
        return

    base = alt.Chart(daily).encode(
        x=alt.X("published_day:T", title=None, axis=alt.Axis(format="%d.%m", grid=False)),
        y=alt.Y("media_views:Q", title="Просмотры"),
        tooltip=[
            alt.Tooltip("published_day:T", title="Дата", format="%d.%m.%Y"),
            alt.Tooltip("media_views:Q", title="Просмотры", format=",.0f"),
        ],
    )
    area = base.mark_area(color=color, opacity=0.14)
    line = base.mark_line(color=color, strokeWidth=3)
    points = base.mark_circle(color=color, size=54)
    st.altair_chart(apply_chart_theme(area + line + points), use_container_width=True)


def render_multi_series_chart(posts: pd.DataFrame, series_field: str, color_map: dict[str, str]) -> None:
    daily = build_daily_views(posts, series_field=series_field)
    if daily.empty:
        render_empty("В текущем наборе нет строк с датами, поэтому график пока не из чего строить.")
        return

    ordered_keys = [key for key in color_map if key in daily[series_field].astype(str).tolist()]
    scale = alt.Scale(
        domain=ordered_keys or list(color_map.keys()),
        range=[color_map[key] for key in (ordered_keys or color_map.keys())],
    )
    base = alt.Chart(daily).encode(
        x=alt.X("published_day:T", title=None, axis=alt.Axis(format="%d.%m", grid=False)),
        y=alt.Y("media_views:Q", title="Просмотры"),
        color=alt.Color(f"{series_field}:N", scale=scale),
        tooltip=[
            alt.Tooltip("published_day:T", title="Дата", format="%d.%m.%Y"),
            alt.Tooltip(f"{series_field}:N", title="Серия"),
            alt.Tooltip("media_views:Q", title="Просмотры", format=",.0f"),
        ],
    )
    chart = base.mark_line(strokeWidth=3, point=alt.OverlayMarkDef(size=60, filled=True))
    st.altair_chart(apply_chart_theme(chart), use_container_width=True)


def render_hero(summary: dict[str, object], platforms: dict[str, dict[str, object]]) -> None:
    active_platforms = sum(1 for key in PLATFORM_ORDER if platforms[key]["has_data"])
    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")

    metrics_html = "".join(
        [
            mini_metric_html("Посты", fmt_int(summary["posts"]), f"Аккаунтов: {fmt_int(summary['accounts'])}"),
            mini_metric_html(
                "Подписчики",
                fmt_int(summary["subscribers_total"]),
                "Сумма максимальных подписчиков по текущим аккаунтам.",
            ),
            mini_metric_html(
                "Средние просмотры",
                fmt_float(summary["avg_media_views"]),
                f"Медиана: {fmt_float(summary['median_media_views'])}",
            ),
            mini_metric_html(
                "Top-3 share",
                fmt_pct(summary["top3_view_share"]),
                "Насколько общий охват держится на самых вирусных постах.",
            ),
        ]
    )

    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-grid">
                <div>
                    <div class="kicker">Streamlit Cloud • HTML-style dashboard</div>
                    <h1 class="title">Social Farm Analytics</h1>
                    <p class="copy">
                        Витрина по тем же CSV, что и в статическом HTML: общий overview, ВКонтакте,
                        отдельная вкладка со всеми постами, фильтрами и просмотрами по дням.
                    </p>
                    <div class="pills">
                        <span class="pill">Собрано: {escape(generated_at)}</span>
                        <span class="pill">Платформ активных: {fmt_int(active_platforms)}</span>
                        <span class="pill">Постов: {fmt_int(summary["posts"])}</span>
                        <span class="pill">Просмотров: {fmt_int(summary["total_media_views"])}</span>
                        <span class="pill">ER View: {fmt_pct(summary["weighted_er_view"])}</span>
                    </div>
                </div>
                <div class="hero-metrics">{metrics_html}</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_overview_tab(posts: pd.DataFrame, platforms: dict[str, dict[str, object]]) -> None:
    summary = summarize_posts(posts)

    with st.container(border=True):
        render_card_header(
            "Общий overview",
            "Суммарные метрики, дневная динамика и сравнение платформ по текущим данным.",
            f"{fmt_int(summary['posts'])} постов • {fmt_date(summary['start_at'])} → {fmt_date(summary['end_at'])}",
        )
        render_metric_grid(
            [
                ("Суммарные просмотры", fmt_int(summary["total_media_views"]), "Все охваты по активным CSV."),
                ("Суммарные реакции", fmt_int(summary["total_media_engagements"]), "Лайки + репосты + комментарии."),
                ("Weighted ER View", fmt_pct(summary["weighted_er_view"]), "Итог по totals, а не среднее средних."),
                ("Weighted ER Post", fmt_pct(summary["weighted_er_post"]), "Сумма реакций / сумма post_views."),
            ]
        )

    left, right = st.columns([1.3, 1])
    with left:
        with st.container(border=True):
            render_card_header("Просмотры по дням", "Динамика по всем активным платформам.")
            color_map = {PLATFORM_META[key]["label"]: PLATFORM_META[key]["color"] for key in PLATFORM_ORDER}
            render_multi_series_chart(posts, "platform_label", color_map)

    with right:
        with st.container(border=True):
            render_card_header("Сводка по платформам", "Totals и weighted-метрики по каждой соцсети.")
            render_html_table(
                build_platform_summary_frame(posts, platforms),
                formatters={
                    "Посты": fmt_int,
                    "Просмотры": fmt_int,
                    "Средние": lambda value: fmt_float(value, 2),
                    "ER View": lambda value: fmt_pct(value, 2),
                    "ER Post": lambda value: fmt_pct(value, 2),
                },
                note="Даже пустые платформы остаются в структуре проекта и оживают автоматически, когда ты добавляешь CSV в свою папку.",
            )

    with st.container(border=True):
        render_card_header("Топ-посты", "Лучшие публикации по просмотрам среди всех активных CSV.")
        render_html_table(
            build_top_posts_table(posts, limit=12),
            formatters={
                "Просмотры": fmt_int,
                "Лайки": fmt_int,
                "Репосты": fmt_int,
                "ER View": lambda value: fmt_pct(value, 2),
            },
            raw_html_columns={"Пост"},
            note="Ссылки ведут прямо на исходные посты.",
        )


def render_vk_tab(vk_posts: pd.DataFrame, vk_has_data: bool) -> None:
    if vk_posts.empty and not vk_has_data:
        with st.container(border=True):
            render_empty("В папке data/vk пока нет CSV. Как только добавишь их, раздел сам оживет.", title="ВКонтакте пока не подключен")
        return

    if vk_posts.empty:
        with st.container(border=True):
            render_empty("Во ВК данные есть, но текущий набор строк пуст. Проверь CSV или фильтры поиска.", title="Нет строк для отображения")
        return

    summary = summarize_posts(vk_posts)

    with st.container(border=True):
        render_card_header(
            "ВКонтакте",
            "Текущий рабочий контур: три CSV, разбивка по аккаунтам и отдельный дневной график.",
            f"{fmt_int(summary['accounts'])} аккаунта • {fmt_int(summary['posts'])} постов",
        )
        render_metric_grid(
            [
                ("Посты", fmt_int(summary["posts"]), "Количество публикаций в текущем VK-контуре."),
                ("Подписчики", fmt_int(summary["subscribers_total"]), "Сумма максимальных подписчиков по каждой ферме."),
                ("Средние просмотры", fmt_float(summary["avg_media_views"]), f"Медиана: {fmt_float(summary['median_media_views'])}"),
                ("Top-3 share", fmt_pct(summary["top3_view_share"]), "Доля просмотров, приходящаяся на три сильнейших поста."),
            ]
        )

    left, right = st.columns([1.3, 1])
    with left:
        with st.container(border=True):
            render_card_header("VK просмотры по дням", "Разбивка по аккаунтам внутри платформы.")
            account_names = vk_posts["account_name"].dropna().astype(str).unique().tolist()
            account_color_map = {
                account: PALETTE[index % len(PALETTE)]
                for index, account in enumerate(account_names)
            }
            render_multi_series_chart(vk_posts, "account_name", account_color_map)

    with right:
        with st.container(border=True):
            render_card_header("Аккаунты VK", "Сводка по каждой ферме: просмотры, средние и weighted ER.")
            render_html_table(
                build_vk_accounts_table(vk_posts),
                formatters={
                    "Посты": fmt_int,
                    "Подписчики": fmt_int,
                    "Просмотры": fmt_int,
                    "Средние": lambda value: fmt_float(value, 2),
                    "ER View": lambda value: fmt_pct(value, 2),
                    "ER Post": lambda value: fmt_pct(value, 2),
                },
            )

    with st.container(border=True):
        render_card_header("Топ-посты ВКонтакте", "Быстрый просмотр сильнейших публикаций и прямые переходы в посты.")
        render_html_table(
            build_top_posts_table(vk_posts, limit=18),
            formatters={
                "Просмотры": fmt_int,
                "Лайки": fmt_int,
                "Репосты": fmt_int,
                "ER View": lambda value: fmt_pct(value, 2),
            },
            raw_html_columns={"Пост"},
        )

    st.download_button(
        "Скачать все текущие строки ВК в CSV",
        vk_posts.to_csv(index=False).encode("utf-8-sig"),
        file_name="vk_posts_export.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_posts_tab(all_posts: pd.DataFrame) -> None:
    if all_posts.empty:
        with st.container(border=True):
            render_empty("Пока нет ни одной активной CSV-выгрузки, поэтому раздел со всеми постами еще пуст.", title="Все посты пока недоступны")
        return

    platform_options = ["Все"] + sorted(all_posts["platform_label"].dropna().astype(str).unique().tolist())
    account_options = ["Все"] + sorted(all_posts["account_name"].dropna().astype(str).unique().tolist())
    kind_options = ["Все"] + sorted(all_posts["media_kind"].fillna("без типа").astype(str).unique().tolist())

    with st.container(border=True):
        render_card_header("Все посты", "Поиск по тексту, фильтры и просмотры по дням по текущей выборке.")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            query = st.text_input("Поиск", placeholder="мем, AdsGram, wall-...", key="posts_query")
        with col2:
            selected_platform = st.selectbox("Платформа", options=platform_options, key="posts_platform")
        with col3:
            selected_account = st.selectbox("Аккаунт", options=account_options, key="posts_account")
        with col4:
            selected_kind = st.selectbox("Тип", options=kind_options, key="posts_kind")

    filtered_posts = filter_posts_for_posts_tab(
        all_posts,
        query=query,
        platform_label=selected_platform,
        account_name=selected_account,
        media_kind=selected_kind,
    )
    filtered_summary = summarize_posts(filtered_posts)

    with st.container(border=True):
        render_card_header(
            "Просмотры по дням по фильтру",
            "График сразу реагирует на выбранные фильтры и поиск.",
            f"{fmt_int(filtered_summary['posts'])} постов в выборке",
        )
        render_total_views_chart(filtered_posts, color="#0EA5E9")

    with st.container(border=True):
        render_card_header(
            "Таблица постов",
            "Новые публикации сверху, текст сокращен до превью.",
            f"{fmt_int(filtered_summary['total_media_views'])} просмотров в выборке",
        )
        render_html_table(
            build_posts_table(filtered_posts),
            formatters={
                "Media Views": fmt_int,
                "Likes": fmt_int,
                "Репосты": fmt_int,
                "Комментарии": fmt_int,
                "ER View": lambda value: fmt_pct(value, 2),
                "ER Post": lambda value: fmt_pct(value, 2),
            },
            raw_html_columns={"Пост"},
            truncate_columns={"Текст": 160},
            note="Таблица уже учитывает фильтры и поиск выше.",
        )

    st.download_button(
        "Скачать текущую выборку постов в CSV",
        filtered_posts.to_csv(index=False).encode("utf-8-sig"),
        file_name="filtered_posts_export.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_future_platform_tab(platform: dict[str, object]) -> None:
    with st.container(border=True):
        render_empty(
            f"Папка {platform['folder_path']} уже создана. Как только ты положишь туда один или несколько CSV, эта вкладка автоматически станет активной и появится в общей сводке.",
            title=f"{platform['label']} ждет CSV",
        )
        st.markdown(
            f"""
            <div class="table-note">
                Текущий статус: <strong>{'Активна' if platform['has_data'] else 'Ждет CSV'}</strong>.
                Приложение сканирует директорию <code>{escape(str(platform['folder_path']))}</code> без ручной настройки.
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    inject_styles()

    repository = get_repository_data(str(BASE_DIR))
    platforms: dict[str, dict[str, object]] = repository["platforms"]  # type: ignore[assignment]
    all_posts: pd.DataFrame = repository["all_posts"]  # type: ignore[assignment]
    summary = summarize_posts(all_posts)

    render_hero(summary, platforms)

    tabs = st.tabs(["Обзор", "ВКонтакте", "Все посты", "YouTube", "Instagram", "TikTok"])

    with tabs[0]:
        render_overview_tab(all_posts, platforms)
    with tabs[1]:
        render_vk_tab(all_posts[all_posts["platform_key"] == "vk"].copy(), bool(platforms["vk"]["has_data"]))
    with tabs[2]:
        render_posts_tab(all_posts.copy())
    with tabs[3]:
        render_future_platform_tab(platforms["youtube"])
    with tabs[4]:
        render_future_platform_tab(platforms["instagram"])
    with tabs[5]:
        render_future_platform_tab(platforms["tiktok"])


if __name__ == "__main__":
    main()
