from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.analytics import PLATFORM_META, PLATFORM_ORDER, load_repository_data, summarize_groups, summarize_posts


BASE_DIR = Path(__file__).resolve().parent
PALETTE = ["#0077FF", "#2DD4BF", "#F97316", "#EF4444", "#A855F7", "#0EA5E9"]


st.set_page_config(
    page_title="Social Farm Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        html, body, [class*="css"] {
            font-family: "Manrope", sans-serif;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(0,119,255,0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(249,115,22,0.18), transparent 26%),
                radial-gradient(circle at bottom left, rgba(45,212,191,0.16), transparent 24%),
                linear-gradient(180deg, #f6f8f2 0%, #eff4ef 48%, #e8f1ee 100%);
        }

        [data-testid="stHeader"] {
            background: rgba(0, 0, 0, 0);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.04em;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.92), rgba(240,247,244,0.88));
            border-right: 1px solid rgba(15, 23, 42, 0.06);
        }

        [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 1rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(148,163,184,0.16);
        }

        [aria-selected="true"][data-baseweb="tab"] {
            background: linear-gradient(135deg, rgba(0,119,255,0.12), rgba(45,212,191,0.18));
            border-color: rgba(0,119,255,0.28);
        }

        .hero-shell {
            position: relative;
            overflow: hidden;
            border-radius: 30px;
            padding: 2rem 2rem 1.8rem 2rem;
            background:
                radial-gradient(circle at 0% 0%, rgba(89,195,255,0.35), transparent 28%),
                radial-gradient(circle at 100% 0%, rgba(249,115,22,0.26), transparent 24%),
                linear-gradient(135deg, rgba(255,255,255,0.92), rgba(244,249,247,0.82));
            border: 1px solid rgba(255,255,255,0.85);
            box-shadow: 0 28px 80px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.25rem;
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.05);
            color: #334155;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .hero-title {
            margin-top: 1rem;
            font-family: "Space Grotesk", sans-serif;
            font-size: 3rem;
            line-height: 1;
            font-weight: 700;
            color: #0f172a;
        }

        .hero-copy {
            margin-top: 1rem;
            max-width: 56rem;
            color: #475569;
            font-size: 1rem;
            line-height: 1.8;
        }

        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1.25rem;
        }

        .hero-pill, .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.48rem 0.82rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(148,163,184,0.18);
            color: #334155;
            font-size: 0.82rem;
            font-weight: 700;
        }

        .metric-card {
            position: relative;
            overflow: hidden;
            min-height: 9rem;
            border-radius: 26px;
            padding: 1.2rem 1.2rem 1.15rem 1.2rem;
            background: rgba(255,255,255,0.80);
            border: 1px solid rgba(255,255,255,0.92);
            box-shadow: 0 20px 54px rgba(15, 23, 42, 0.06);
        }

        .metric-label {
            color: #64748b;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .metric-value {
            margin-top: 0.65rem;
            color: #0f172a;
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            line-height: 1.05;
            font-weight: 700;
        }

        .metric-note {
            margin-top: 0.65rem;
            color: #475569;
            font-size: 0.92rem;
            line-height: 1.6;
        }

        .section-card {
            border-radius: 28px;
            padding: 1.1rem 1.1rem 0.9rem 1.1rem;
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(255,255,255,0.9);
            box-shadow: 0 22px 60px rgba(15, 23, 42, 0.06);
        }

        .section-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: #0f172a;
        }

        .section-copy {
            color: #64748b;
            margin-top: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .platform-card {
            border-radius: 24px;
            padding: 1rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(247,250,252,0.72));
            border: 1px solid rgba(148,163,184,0.14);
        }

        .platform-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: #0f172a;
        }

        .platform-meta {
            margin-top: 0.45rem;
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.6;
        }

        .empty-state {
            border-radius: 28px;
            padding: 1.6rem;
            background:
                radial-gradient(circle at top left, rgba(249,115,22,0.18), transparent 28%),
                linear-gradient(180deg, rgba(255,255,255,0.92), rgba(247,250,252,0.78));
            border: 1px solid rgba(255,255,255,0.9);
            box-shadow: 0 20px 58px rgba(15, 23, 42, 0.06);
        }

        .empty-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: #0f172a;
        }

        .empty-copy {
            margin-top: 0.8rem;
            color: #475569;
            line-height: 1.8;
        }

        .formula-box {
            border-radius: 22px;
            padding: 1rem;
            background: rgba(15, 23, 42, 0.03);
            border: 1px solid rgba(148,163,184,0.16);
            font-size: 0.95rem;
            line-height: 1.7;
            color: #334155;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def get_repository_data(base_dir: str) -> dict[str, object]:
    return load_repository_data(Path(base_dir))


def fmt_int(value: float | int) -> str:
    return f"{int(round(float(value))):,}".replace(",", " ")


def fmt_float(value: float | int, digits: int = 2) -> str:
    return f"{float(value):,.{digits}f}".replace(",", " ").replace(".", ",")


def fmt_pct(value: float | int, digits: int = 2) -> str:
    return f"{fmt_float(value, digits)}%"


def fmt_date(value: object) -> str:
    if pd.isna(value):
        return "нет данных"
    return pd.Timestamp(value).strftime("%d.%m.%Y")


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=14, r=14, t=24, b=14),
        font=dict(family="Manrope", color="#334155"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        hoverlabel=dict(
            bgcolor="rgba(15,23,42,0.92)",
            bordercolor="rgba(255,255,255,0.14)",
            font=dict(color="#E2E8F0"),
        ),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.18)", zeroline=False)
    return fig


def metric_card(label: str, value: str, note: str) -> str:
    return f"""
        <div class="metric-card">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
            <div class="metric-note">{escape(note)}</div>
        </div>
    """


def platform_status_card(platform: dict[str, object], summary: dict[str, object]) -> str:
    status = "Активна" if platform["has_data"] else "Ждёт CSV"
    accent = platform["color"] if platform["has_data"] else "#94A3B8"
    files_label = f"{len(platform['files'])} CSV"
    return f"""
        <div class="platform-card" style="box-shadow: inset 0 0 0 1px {accent}18;">
            <div class="status-pill" style="border-color:{accent}33;">{escape(status)} • {escape(files_label)}</div>
            <div class="platform-title" style="margin-top:0.8rem;">{escape(platform['label'])}</div>
            <div class="platform-meta">
                {escape(platform['description'])}<br/>
                Папка: {escape(platform['folder_path'])}
            </div>
            <div class="platform-meta" style="margin-top:0.8rem;">
                Постов: {fmt_int(summary['posts'])} • Просмотров: {fmt_int(summary['total_media_views'])}
            </div>
        </div>
    """


def filter_posts(
    posts: pd.DataFrame,
    platform_keys: list[str],
    account_names: list[str],
    media_kinds: list[str],
    period_start: date,
    period_end: date,
) -> pd.DataFrame:
    if posts.empty:
        return posts.copy()

    filtered = posts.copy()
    filtered = filtered[filtered["platform_key"].isin(platform_keys)]
    if account_names:
        filtered = filtered[filtered["account_name"].isin(account_names)]
    if media_kinds:
        filtered = filtered[filtered["media_kind"].fillna("без типа").isin(media_kinds)]

    start_ts = pd.Timestamp(period_start)
    end_ts = pd.Timestamp(period_end)
    filtered = filtered[filtered["published_day"].between(start_ts, end_ts)]
    return filtered.reset_index(drop=True)


def render_hero(summary: dict[str, object], active_platforms_count: int) -> None:
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">Streamlit Cloud Ready</div>
            <div class="hero-title">Social Farm Analytics</div>
            <div class="hero-copy">
                Единая витрина по соцсетям с корректной агрегацией метрик, отдельными папками под платформы
                и красивыми дашбордами для детализации по CSV. Сейчас активен ВК-контур, а YouTube,
                Instagram и TikTok уже готовы к подключению.
            </div>
            <div class="hero-pills">
                <span class="hero-pill">Активных платформ: {fmt_int(active_platforms_count)}</span>
                <span class="hero-pill">Постов в текущем фильтре: {fmt_int(summary["posts"])}</span>
                <span class="hero-pill">Период: {fmt_date(summary["start_at"])} → {fmt_date(summary["end_at"])}</span>
                <span class="hero-pill">Weighted ER View: {fmt_pct(summary["weighted_er_view"])}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_platform_summary_frame(
    filtered_posts: pd.DataFrame, platforms: dict[str, dict[str, object]]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key in PLATFORM_ORDER:
        platform_posts = filtered_posts[filtered_posts["platform_key"] == key]
        summary = summarize_posts(platform_posts)
        meta = platforms[key]
        rows.append(
            {
                "Платформа": meta["label"],
                "Статус": "Активна" if meta["has_data"] else "Ждёт CSV",
                "Папка": meta["folder"],
                "Посты": summary["posts"],
                "Аккаунты": summary["accounts"],
                "Подписчики": summary["subscribers_total"],
                "Просмотры": summary["total_media_views"],
                "Лайки": summary["total_media_likes"],
                "Репосты": summary["total_reposts"],
                "Комментарии": summary["total_comments"],
                "Средние просмотры": summary["avg_media_views"],
                "Weighted ER View": summary["weighted_er_view"],
                "Weighted ER Post": summary["weighted_er_post"],
                "Weighted VR Post": summary["weighted_vr_post"],
            }
        )
    return pd.DataFrame(rows)


def build_overview_timeseries(filtered_posts: pd.DataFrame) -> pd.DataFrame:
    if filtered_posts.empty:
        return pd.DataFrame(columns=["published_day", "platform_label", "media_views", "media_engagements", "posts"])
    return (
        filtered_posts.groupby(["published_day", "platform_label"], dropna=False)
        .agg(
            media_views=("media_views", "sum"),
            media_engagements=("media_engagements", "sum"),
            posts=("post_url", "count"),
        )
        .reset_index()
        .sort_values("published_day")
    )


def build_overview_charts(
    filtered_posts: pd.DataFrame, platforms: dict[str, dict[str, object]]
) -> tuple[go.Figure, go.Figure]:
    overview_ts = build_overview_timeseries(filtered_posts)
    if overview_ts.empty:
        return go.Figure(), go.Figure()

    platform_color_map = {PLATFORM_META[key]["label"]: PLATFORM_META[key]["color"] for key in PLATFORM_ORDER}

    fig_area = px.area(
        overview_ts,
        x="published_day",
        y="media_views",
        color="platform_label",
        color_discrete_map=platform_color_map,
        markers=False,
        labels={
            "published_day": "Дата",
            "media_views": "Просмотры",
            "platform_label": "Платформа",
        },
    )
    fig_area.update_traces(mode="lines", line_width=3)
    style_figure(fig_area)

    summary_frame = build_platform_summary_frame(filtered_posts, platforms)
    fig_bar = px.bar(
        summary_frame,
        x="Платформа",
        y="Просмотры",
        color="Платформа",
        color_discrete_map=platform_color_map,
        text="Посты",
        labels={"Просмотры": "Просмотры", "Посты": "Посты"},
    )
    fig_bar.update_traces(textposition="outside")
    style_figure(fig_bar)
    return fig_area, fig_bar


def build_vk_daily_charts(vk_posts: pd.DataFrame) -> tuple[go.Figure, go.Figure, go.Figure]:
    if vk_posts.empty:
        return go.Figure(), go.Figure(), go.Figure()

    daily_account = (
        vk_posts.groupby(["published_day", "account_name"], dropna=False)
        .agg(
            media_views=("media_views", "sum"),
            media_engagements=("media_engagements", "sum"),
            posts=("post_url", "count"),
        )
        .reset_index()
        .sort_values("published_day")
    )

    account_colors = {
        account: PALETTE[index % len(PALETTE)]
        for index, account in enumerate(daily_account["account_name"].dropna().unique())
    }

    fig_views = px.area(
        daily_account,
        x="published_day",
        y="media_views",
        color="account_name",
        color_discrete_map=account_colors,
        labels={"published_day": "Дата", "media_views": "Просмотры", "account_name": "Аккаунт"},
    )
    fig_views.update_traces(mode="lines", line_width=2.8)
    style_figure(fig_views)

    fig_eng = px.bar(
        daily_account,
        x="published_day",
        y="media_engagements",
        color="account_name",
        color_discrete_map=account_colors,
        barmode="stack",
        labels={"published_day": "Дата", "media_engagements": "Реакции", "account_name": "Аккаунт"},
    )
    style_figure(fig_eng)

    fig_scatter = px.scatter(
        vk_posts.sort_values("published_at"),
        x="published_at",
        y="media_views",
        size="media_engagements",
        color="account_name",
        color_discrete_map=account_colors,
        hover_name="account_name",
        hover_data={
            "published_at": "|%d.%m.%Y %H:%M",
            "media_views": ":,.0f",
            "media_engagements": ":,.0f",
            "post_url": True,
        },
        labels={
            "published_at": "Дата",
            "media_views": "Просмотры",
            "media_engagements": "Реакции",
            "account_name": "Аккаунт",
        },
    )
    fig_scatter.update_traces(marker=dict(line=dict(width=1, color="rgba(255,255,255,0.65)"), opacity=0.8))
    style_figure(fig_scatter)

    return fig_views, fig_eng, fig_scatter


def build_vk_account_bar(account_summary: pd.DataFrame) -> go.Figure:
    if account_summary.empty:
        return go.Figure()

    chart_frame = account_summary.rename(
        columns={
            "account_name": "Аккаунт",
            "total_media_views": "Просмотры",
            "avg_media_views": "Средние просмотры",
            "weighted_er_view": "Weighted ER View",
        }
    )
    fig = px.bar(
        chart_frame,
        x="Аккаунт",
        y="Просмотры",
        color="Аккаунт",
        color_discrete_sequence=PALETTE,
        hover_data={"Средние просмотры": ":,.2f", "Weighted ER View": ":,.2f"},
        labels={"Просмотры": "Просмотры"},
    )
    fig.update_traces(texttemplate="%{y:,.0f}", textposition="outside")
    style_figure(fig)
    return fig


def build_top_posts_table(posts: pd.DataFrame, limit: int = 15) -> pd.DataFrame:
    if posts.empty:
        return pd.DataFrame(
            columns=[
                "Платформа",
                "Аккаунт",
                "Дата",
                "Просмотры",
                "Лайки",
                "Репосты",
                "Комментарии",
                "Weighted ER View",
                "Ссылка",
            ]
        )

    top_posts = (
        posts.sort_values(["media_views", "media_engagements", "published_at"], ascending=[False, False, False])
        .head(limit)
        .copy()
    )
    top_posts["Дата"] = top_posts["published_at"].dt.strftime("%d.%m.%Y %H:%M")
    top_posts["Weighted ER View"] = top_posts["er_view_calc"].round(2)
    return top_posts.rename(
        columns={
            "platform_label": "Платформа",
            "account_name": "Аккаунт",
            "media_views": "Просмотры",
            "media_likes": "Лайки",
            "reposts": "Репосты",
            "comments": "Комментарии",
            "post_url": "Ссылка",
        }
    )[
        ["Платформа", "Аккаунт", "Дата", "Просмотры", "Лайки", "Репосты", "Комментарии", "Weighted ER View", "Ссылка"]
    ]


def build_raw_export(posts: pd.DataFrame) -> pd.DataFrame:
    if posts.empty:
        return posts.copy()

    export = posts.copy()
    export["published_at"] = export["published_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    export["published_day"] = export["published_day"].dt.strftime("%Y-%m-%d")
    return export


def render_overview_tab(
    filtered_posts: pd.DataFrame,
    platforms: dict[str, dict[str, object]],
    has_source_data: bool,
) -> None:
    summary = summarize_posts(filtered_posts)
    if filtered_posts.empty:
        if has_source_data:
            st.warning("Под текущие фильтры ничего не попало. Ослабь фильтры слева, и данные снова появятся.")
        else:
            st.info("Пока нет ни одной активной CSV-выгрузки. Начни с папки `data/vk`.")
    metrics = [
        ("Суммарные просмотры", fmt_int(summary["total_media_views"]), "Все охваты по активным CSV в текущем фильтре."),
        ("Суммарные реакции", fmt_int(summary["total_media_engagements"]), "Лайки + репосты + комментарии по всем постам."),
        ("Weighted ER View", fmt_pct(summary["weighted_er_view"]), "Корректный общий ER по фактическим totals, а не среднее средних."),
        ("Weighted ER Post", fmt_pct(summary["weighted_er_post"]), "Сумма post_likes + reposts + comments делится на сумму post_views."),
    ]

    metric_columns = st.columns(4)
    for column, (label, value, note) in zip(metric_columns, metrics):
        with column:
            st.markdown(metric_card(label, value, note), unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Статус платформ</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">ВК уже подключён, остальные папки готовы и автоматически подхватят CSV после добавления.</div>', unsafe_allow_html=True)
    status_html = "".join(
        platform_status_card(platforms[key], summarize_posts(filtered_posts[filtered_posts["platform_key"] == key]))
        for key in PLATFORM_ORDER
    )
    st.markdown(f'<div class="status-grid">{status_html}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    area_chart, bar_chart = build_overview_charts(filtered_posts, platforms)
    chart_left, chart_right = st.columns([1.4, 1])
    with chart_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Динамика по платформам</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Показывает, как распределяется суммарный охват по дням.</div>', unsafe_allow_html=True)
        st.plotly_chart(area_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Сводка по просмотрам</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Даже пустые платформы видны отдельно и не теряются из структуры проекта.</div>', unsafe_allow_html=True)
        st.plotly_chart(bar_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    summary_table = build_platform_summary_frame(filtered_posts, platforms)
    top_posts = build_top_posts_table(filtered_posts, limit=20)

    table_left, table_right = st.columns([1.1, 1])
    with table_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Таблица по платформам</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Здесь уже лежат totals и правильные weighted-метрики для суммарного режима.</div>', unsafe_allow_html=True)
        st.dataframe(
            summary_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Посты": st.column_config.NumberColumn(format="%d"),
                "Аккаунты": st.column_config.NumberColumn(format="%d"),
                "Подписчики": st.column_config.NumberColumn(format="%d"),
                "Просмотры": st.column_config.NumberColumn(format="%d"),
                "Лайки": st.column_config.NumberColumn(format="%d"),
                "Репосты": st.column_config.NumberColumn(format="%d"),
                "Комментарии": st.column_config.NumberColumn(format="%d"),
                "Средние просмотры": st.column_config.NumberColumn(format="%.2f"),
                "Weighted ER View": st.column_config.NumberColumn(format="%.2f%%"),
                "Weighted ER Post": st.column_config.NumberColumn(format="%.2f%%"),
                "Weighted VR Post": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with table_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Топ-посты по всему стеку</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Лидеры по охвату из всех активных платформ и аккаунтов.</div>', unsafe_allow_html=True)
        st.dataframe(
            top_posts,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Просмотры": st.column_config.NumberColumn(format="%d"),
                "Лайки": st.column_config.NumberColumn(format="%d"),
                "Репосты": st.column_config.NumberColumn(format="%d"),
                "Комментарии": st.column_config.NumberColumn(format="%d"),
                "Weighted ER View": st.column_config.NumberColumn(format="%.2f%%"),
                "Ссылка": st.column_config.LinkColumn(display_text="Открыть"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Как считаются суммарные метрики", expanded=False):
        st.markdown(
            """
            <div class="formula-box">
                <strong>Weighted ER View</strong> = сумма <code>media_likes + reposts + comments</code> / сумма <code>media_views</code> × 100.<br/>
                <strong>Weighted ER Post</strong> = сумма <code>post_likes + reposts + comments</code> / сумма <code>post_views</code> × 100.<br/>
                <strong>Weighted VR Post</strong> = сумма <code>media_views</code> / сумма <code>post_views</code>.<br/>
                Это важнее обычного среднего по строкам, потому что большие посты получают больший вес и итог получается математически корректным для общей сводки.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_vk_tab(vk_posts: pd.DataFrame, vk_has_data: bool) -> None:
    if vk_posts.empty:
        if vk_has_data:
            st.info("Во ВК есть данные, но текущие фильтры скрыли все строки. Ослабь фильтры слева.")
        else:
            st.info("В папке `data/vk` пока нет CSV. Как только добавишь их, вкладка оживёт автоматически.")
        return

    summary = summarize_posts(vk_posts)
    account_summary = summarize_groups(vk_posts, "account_name")
    account_cards = st.columns(max(1, min(len(account_summary), 3)))

    for column, (_, row) in zip(account_cards, account_summary.head(3).iterrows()):
        with column:
            st.markdown(
                metric_card(
                    str(row["account_name"]),
                    fmt_int(row["total_media_views"]),
                    f"Постов: {fmt_int(row['posts'])} • Weighted ER View: {fmt_pct(row['weighted_er_view'])}",
                ),
                unsafe_allow_html=True,
            )

    summary_row = st.columns(4)
    summary_row[0].markdown(
        metric_card("Постов", fmt_int(summary["posts"]), f"Аккаунтов: {fmt_int(summary['accounts'])}"),
        unsafe_allow_html=True,
    )
    summary_row[1].markdown(
        metric_card("Подписчики", fmt_int(summary["subscribers_total"]), "Сумма максимальных подписчиков по каждой ферме."),
        unsafe_allow_html=True,
    )
    summary_row[2].markdown(
        metric_card("Средние просмотры", fmt_float(summary["avg_media_views"]), f"Медиана: {fmt_float(summary['median_media_views'])}"),
        unsafe_allow_html=True,
    )
    summary_row[3].markdown(
        metric_card("Топ-3 доля", fmt_pct(summary["top3_view_share"]), "Насколько охват сконцентрирован в вирусных выбросах."),
        unsafe_allow_html=True,
    )

    views_chart, eng_chart, scatter_chart = build_vk_daily_charts(vk_posts)
    chart_bar = build_vk_account_bar(account_summary)

    chart_left, chart_right = st.columns([1.2, 1])
    with chart_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Дневной охват по аккаунтам ВК</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Area chart удобно показывает и массу охвата, и изменение ритма публикаций.</div>', unsafe_allow_html=True)
        st.plotly_chart(views_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Просмотры по фермам</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Сравнение общей массы трафика между тремя текущими CSV.</div>', unsafe_allow_html=True)
        st.plotly_chart(chart_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    second_left, second_right = st.columns([1, 1])
    with second_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Состав реакций по дням</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Stacked bar помогает быстро увидеть всплески вовлечения.</div>', unsafe_allow_html=True)
        st.plotly_chart(eng_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with second_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Посты: охват против реакций</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Размер точки показывает сумму реакций, а цвет — аккаунт-источник.</div>', unsafe_allow_html=True)
        st.plotly_chart(scatter_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    account_table = account_summary.rename(
        columns={
            "account_name": "Аккаунт",
            "posts": "Посты",
            "subscribers_total": "Подписчики",
            "total_media_views": "Просмотры",
            "avg_media_views": "Средние просмотры",
            "weighted_er_view": "Weighted ER View",
            "weighted_er_post": "Weighted ER Post",
            "avg_media_likes": "Средние лайки",
            "avg_reposts": "Средние репосты",
            "avg_comments": "Средние комментарии",
            "top_post_views": "Лучший пост",
            "last_post_at": "Последний пост",
        }
    )
    if not account_table.empty:
        account_table["Последний пост"] = pd.to_datetime(account_table["Последний пост"]).dt.strftime("%d.%m.%Y %H:%M")

    top_vk_posts = build_top_posts_table(vk_posts, limit=20)

    table_left, table_right = st.columns([1, 1])
    with table_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Сводка по ВК-аккаунтам</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Все ключевые средние и weighted-показатели по каждой ферме.</div>', unsafe_allow_html=True)
        st.dataframe(
            account_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Посты": st.column_config.NumberColumn(format="%d"),
                "Подписчики": st.column_config.NumberColumn(format="%d"),
                "Просмотры": st.column_config.NumberColumn(format="%d"),
                "Средние просмотры": st.column_config.NumberColumn(format="%.2f"),
                "Weighted ER View": st.column_config.NumberColumn(format="%.2f%%"),
                "Weighted ER Post": st.column_config.NumberColumn(format="%.2f%%"),
                "Средние лайки": st.column_config.NumberColumn(format="%.2f"),
                "Средние репосты": st.column_config.NumberColumn(format="%.2f"),
                "Средние комментарии": st.column_config.NumberColumn(format="%.2f"),
                "Лучший пост": st.column_config.NumberColumn(format="%d"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with table_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Топ-посты ВК</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Таблица для ручной проверки лучших публикаций и быстрых переходов по ссылкам.</div>', unsafe_allow_html=True)
        st.dataframe(
            top_vk_posts,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Просмотры": st.column_config.NumberColumn(format="%d"),
                "Лайки": st.column_config.NumberColumn(format="%d"),
                "Репосты": st.column_config.NumberColumn(format="%d"),
                "Комментарии": st.column_config.NumberColumn(format="%d"),
                "Weighted ER View": st.column_config.NumberColumn(format="%.2f%%"),
                "Ссылка": st.column_config.LinkColumn(display_text="Открыть"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        "Скачать текущий фильтр ВК в CSV",
        build_raw_export(vk_posts).to_csv(index=False).encode("utf-8-sig"),
        file_name="vk_filtered_export.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_future_platform_tab(platform_key: str, platform: dict[str, object]) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-title">{escape(platform['label'])} пока не подключён</div>
            <div class="empty-copy">
                Папка <code>{escape(platform['folder_path'])}</code> уже создана в проекте. Как только ты положишь туда
                один или несколько <code>.csv</code>, вкладка автоматически станет активной и появится в общей сводке.
                Приложение сканирует все файлы в этой директории без ручной настройки.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(f"{platform['folder_path']}/your_export.csv", language="bash")
    with st.expander(f"Что уже готово для {platform['label']}", expanded=True):
        st.markdown(
            f"""
            - Структура папок уже создана.
            - Вкладка уже заведена в интерфейсе.
            - Общая сводка автоматически учитывает платформу, как только в `{platform['folder_path']}` появятся CSV.
            - Сейчас статус: `{"Активна" if platform['has_data'] else "Ждёт CSV"}`.
            """
        )


def main() -> None:
    inject_styles()

    repository = get_repository_data(str(BASE_DIR))
    platforms: dict[str, dict[str, object]] = repository["platforms"]  # type: ignore[assignment]
    all_posts: pd.DataFrame = repository["all_posts"]  # type: ignore[assignment]

    active_platform_keys = [key for key in PLATFORM_ORDER if platforms[key]["has_data"]]
    available_platform_options = active_platform_keys or ["vk"]

    if all_posts.empty:
        min_date = max_date = pd.Timestamp.today().date()
        available_accounts: list[str] = []
        available_media_kinds: list[str] = []
    else:
        min_date = all_posts["published_day"].min().date()
        max_date = all_posts["published_day"].max().date()
        available_accounts = sorted(all_posts["account_name"].dropna().unique().tolist())
        available_media_kinds = sorted(all_posts["media_kind"].fillna("без типа").unique().tolist())

    with st.sidebar:
        st.markdown("## Фильтры")
        selected_platform_keys = st.multiselect(
            "Активные платформы",
            options=available_platform_options,
            default=available_platform_options,
            format_func=lambda key: PLATFORM_META[key]["label"],
        )
        selected_accounts = st.multiselect(
            "Аккаунты",
            options=available_accounts,
            default=available_accounts,
        )
        selected_media_kinds = st.multiselect(
            "Тип медиа",
            options=available_media_kinds,
            default=available_media_kinds,
        )
        period_value = st.date_input(
            "Период",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        st.markdown("---")
        st.caption("Общая вкладка и вкладка ВК пересчитываются по этим фильтрам. Будущие платформы просто ждут CSV в своих папках.")

    if isinstance(period_value, tuple):
        period_start, period_end = period_value
    else:
        period_start = period_end = period_value

    filtered_posts = filter_posts(
        all_posts,
        platform_keys=selected_platform_keys,
        account_names=selected_accounts,
        media_kinds=selected_media_kinds,
        period_start=period_start,
        period_end=period_end,
    )
    filtered_summary = summarize_posts(filtered_posts)

    render_hero(filtered_summary, active_platforms_count=len(active_platform_keys))

    tabs = st.tabs(["Обзор", "ВКонтакте", "YouTube", "Instagram", "TikTok"])

    with tabs[0]:
        render_overview_tab(filtered_posts, platforms, has_source_data=not all_posts.empty)
    with tabs[1]:
        render_vk_tab(
            filtered_posts[filtered_posts["platform_key"] == "vk"].copy(),
            vk_has_data=bool(platforms["vk"]["has_data"]),
        )
    with tabs[2]:
        render_future_platform_tab("youtube", platforms["youtube"])
    with tabs[3]:
        render_future_platform_tab("instagram", platforms["instagram"])
    with tabs[4]:
        render_future_platform_tab("tiktok", platforms["tiktok"])


if __name__ == "__main__":
    main()
