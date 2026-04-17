from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import pandas as pd


PLATFORM_META: dict[str, dict[str, Any]] = {
    "vk": {
        "label": "ВКонтакте",
        "short_label": "VK",
        "folder": "data/vk",
        "color": "#0077FF",
        "accent": "#59C3FF",
        "description": "Активная платформа с тремя CSV-фермами.",
    },
    "youtube": {
        "label": "YouTube",
        "short_label": "YT",
        "folder": "data/youtube",
        "color": "#FF3131",
        "accent": "#FF8A8A",
        "description": "Папка подготовлена, ждёт первые CSV.",
    },
    "instagram": {
        "label": "Instagram",
        "short_label": "IG",
        "folder": "data/instagram",
        "color": "#F97316",
        "accent": "#FDBA74",
        "description": "Папка подготовлена, ждёт первые CSV.",
    },
    "tiktok": {
        "label": "TikTok",
        "short_label": "TT",
        "folder": "data/tiktok",
        "color": "#14B8A6",
        "accent": "#5EEAD4",
        "description": "Папка подготовлена, ждёт первые CSV.",
    },
}

PLATFORM_ORDER = list(PLATFORM_META.keys())

COLUMN_ALIASES = {
    "Social": "social",
    "Page url": "page_url",
    "Reg Date": "registered_at",
    "Subscribers": "subscribers",
    "media_kind": "media_kind",
    "Post Url": "post_url",
    "media_views": "media_views",
    "post_likes": "post_likes",
    "media_likes": "media_likes",
    "reposts": "reposts",
    "post_views": "post_views",
    "Comments": "comments",
    "ER Post": "er_post_raw",
    "ER View": "er_view_raw",
    "VR Post": "vr_post_raw",
    "Text": "text",
    "Date": "published_at_raw",
}

EXPECTED_COLUMNS = {
    "social",
    "page_url",
    "registered_at",
    "subscribers",
    "media_kind",
    "post_url",
    "media_views",
    "post_likes",
    "media_likes",
    "reposts",
    "post_views",
    "comments",
    "er_post_raw",
    "er_view_raw",
    "vr_post_raw",
    "text",
    "published_at_raw",
}

NUMERIC_COLUMNS = [
    "subscribers",
    "media_views",
    "post_likes",
    "media_likes",
    "reposts",
    "post_views",
    "comments",
    "er_post_raw",
    "er_view_raw",
    "vr_post_raw",
]

EMPTY_SUMMARY: dict[str, Any] = {
    "posts": 0,
    "accounts": 0,
    "active_days": 0,
    "available_post_view_rows": 0,
    "subscribers_total": 0,
    "total_media_views": 0,
    "total_post_views": 0,
    "total_media_likes": 0,
    "total_post_likes": 0,
    "total_reposts": 0,
    "total_comments": 0,
    "total_media_engagements": 0,
    "total_post_engagements": 0,
    "avg_media_views": 0.0,
    "median_media_views": 0.0,
    "avg_media_likes": 0.0,
    "avg_post_likes": 0.0,
    "avg_reposts": 0.0,
    "avg_comments": 0.0,
    "avg_post_views": 0.0,
    "avg_posts_per_day": 0.0,
    "weighted_er_view": 0.0,
    "macro_er_view": 0.0,
    "weighted_er_post": 0.0,
    "macro_er_post": 0.0,
    "weighted_vr_post": 0.0,
    "macro_vr_post": 0.0,
    "views_per_subscriber": 0.0,
    "top3_view_share": 0.0,
    "start_at": pd.NaT,
    "end_at": pd.NaT,
}


def _empty_posts_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "platform_key",
            "platform_label",
            "platform_color",
            "source_file",
            "source_path",
            "account_name",
            "social",
            "page_url",
            "registered_at",
            "subscribers",
            "media_kind",
            "post_url",
            "post_code",
            "media_views",
            "post_likes",
            "media_likes",
            "reposts",
            "post_views",
            "comments",
            "er_post_raw",
            "er_view_raw",
            "vr_post_raw",
            "er_post_calc",
            "er_view_calc",
            "vr_post_calc",
            "text",
            "text_clean",
            "published_at_raw",
            "published_at",
            "published_day",
            "post_engagements",
            "media_engagements",
        ]
    )


def _coerce_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("\u00a0", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({"": None, "nan": None, "None": None, "<NA>": None})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _strip_html(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = re.sub(r"<[^>]+>", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def _account_name_from_path(path: Path) -> str:
    stem = path.stem
    if " - " in stem:
        return stem.split(" - ", 1)[1].strip()
    return stem.replace("_", " ").strip()


def _post_code_from_url(url: Any) -> str:
    if pd.isna(url):
        return ""
    match = re.search(r"_([0-9]+)$", str(url))
    return match.group(1) if match else ""


def _safe_ratio(numerator: float, denominator: float, multiplier: float = 1.0) -> float:
    if denominator and denominator > 0:
        return float(numerator) / float(denominator) * multiplier
    return 0.0


def _to_total(series: pd.Series) -> int:
    return int(round(float(series.fillna(0).sum())))


def _to_avg(series: pd.Series) -> float:
    if series.dropna().empty:
        return 0.0
    return float(series.mean())


def _normalize_posts(frame: pd.DataFrame, base_dir: Path, platform_key: str, source_file: Path) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).replace("\ufeff", "").strip() for column in frame.columns]
    frame = frame.rename(columns=COLUMN_ALIASES)

    for column in EXPECTED_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA

    for column in NUMERIC_COLUMNS:
        frame[column] = _coerce_numeric(frame[column])

    registered_raw = frame["registered_at"].astype(str).str.replace(" MSK", "", regex=False)
    published_raw = frame["published_at_raw"].astype(str).str.replace(" MSK", "", regex=False)

    frame["registered_at"] = pd.to_datetime(registered_raw, errors="coerce")
    frame["published_at"] = pd.to_datetime(published_raw, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    frame["published_day"] = frame["published_at"].dt.normalize()

    frame["platform_key"] = platform_key
    frame["platform_label"] = PLATFORM_META[platform_key]["label"]
    frame["platform_color"] = PLATFORM_META[platform_key]["color"]
    frame["source_file"] = source_file.name
    frame["source_path"] = str(source_file.relative_to(base_dir))
    frame["account_name"] = _account_name_from_path(source_file)
    frame["post_code"] = frame["post_url"].map(_post_code_from_url)
    frame["text_clean"] = frame["text"].map(_strip_html)

    frame["post_engagements"] = (
        frame[["post_likes", "reposts", "comments"]].fillna(0).sum(axis=1)
    )
    frame["media_engagements"] = (
        frame[["media_likes", "reposts", "comments"]].fillna(0).sum(axis=1)
    )

    frame["er_post_calc"] = (
        frame["post_engagements"].div(frame["post_views"].where(frame["post_views"] > 0)).mul(100)
    )
    frame["er_view_calc"] = (
        frame["media_engagements"].div(frame["media_views"].where(frame["media_views"] > 0)).mul(100)
    )
    frame["vr_post_calc"] = frame["media_views"].div(frame["post_views"].where(frame["post_views"] > 0))

    frame = frame.sort_values(["published_at", "account_name", "post_url"], na_position="last")
    return frame.reset_index(drop=True)


def summarize_posts(posts: pd.DataFrame) -> dict[str, Any]:
    if posts.empty:
        return EMPTY_SUMMARY.copy()

    subscribers_total = int(
        round(float(posts.groupby("account_name", dropna=False)["subscribers"].max().fillna(0).sum()))
    )
    total_media_views = _to_total(posts["media_views"])
    total_post_views = _to_total(posts["post_views"])
    total_media_likes = _to_total(posts["media_likes"])
    total_post_likes = _to_total(posts["post_likes"])
    total_reposts = _to_total(posts["reposts"])
    total_comments = _to_total(posts["comments"])
    total_media_engagements = _to_total(posts["media_engagements"])
    total_post_engagements = _to_total(posts["post_engagements"])
    active_days = int(posts["published_day"].dropna().nunique())
    available_post_view_rows = int(posts["post_views"].fillna(0).gt(0).sum())
    top3_views = _to_total(posts.nlargest(3, "media_views")["media_views"])

    return {
        "posts": int(len(posts)),
        "accounts": int(posts["account_name"].nunique()),
        "active_days": active_days,
        "available_post_view_rows": available_post_view_rows,
        "subscribers_total": subscribers_total,
        "total_media_views": total_media_views,
        "total_post_views": total_post_views,
        "total_media_likes": total_media_likes,
        "total_post_likes": total_post_likes,
        "total_reposts": total_reposts,
        "total_comments": total_comments,
        "total_media_engagements": total_media_engagements,
        "total_post_engagements": total_post_engagements,
        "avg_media_views": _to_avg(posts["media_views"]),
        "median_media_views": float(posts["media_views"].median()) if not posts["media_views"].dropna().empty else 0.0,
        "avg_media_likes": _to_avg(posts["media_likes"]),
        "avg_post_likes": _to_avg(posts["post_likes"]),
        "avg_reposts": _to_avg(posts["reposts"]),
        "avg_comments": _to_avg(posts["comments"]),
        "avg_post_views": _to_avg(posts["post_views"]),
        "avg_posts_per_day": _safe_ratio(len(posts), active_days),
        "weighted_er_view": _safe_ratio(total_media_engagements, total_media_views, 100),
        "macro_er_view": _to_avg(posts["er_view_calc"]),
        "weighted_er_post": _safe_ratio(total_post_engagements, total_post_views, 100),
        "macro_er_post": _to_avg(posts["er_post_calc"]),
        "weighted_vr_post": _safe_ratio(total_media_views, total_post_views),
        "macro_vr_post": _to_avg(posts["vr_post_calc"]),
        "views_per_subscriber": _safe_ratio(total_media_views, subscribers_total),
        "top3_view_share": _safe_ratio(top3_views, total_media_views, 100),
        "start_at": posts["published_at"].min(),
        "end_at": posts["published_at"].max(),
    }


def summarize_groups(posts: pd.DataFrame, group_field: str) -> pd.DataFrame:
    if posts.empty:
        return pd.DataFrame(
            columns=[
                group_field,
                "posts",
                "subscribers_total",
                "total_media_views",
                "avg_media_views",
                "weighted_er_view",
                "weighted_er_post",
                "avg_media_likes",
                "avg_reposts",
                "avg_comments",
                "top_post_views",
                "last_post_at",
            ]
        )

    rows: list[dict[str, Any]] = []
    for group_name, group_posts in posts.groupby(group_field, dropna=False):
        summary = summarize_posts(group_posts)
        top_post_views = _to_total(group_posts.nlargest(1, "media_views")["media_views"])
        rows.append(
            {
                group_field: group_name,
                "posts": summary["posts"],
                "subscribers_total": summary["subscribers_total"],
                "total_media_views": summary["total_media_views"],
                "avg_media_views": summary["avg_media_views"],
                "weighted_er_view": summary["weighted_er_view"],
                "weighted_er_post": summary["weighted_er_post"],
                "avg_media_likes": summary["avg_media_likes"],
                "avg_reposts": summary["avg_reposts"],
                "avg_comments": summary["avg_comments"],
                "top_post_views": top_post_views,
                "last_post_at": summary["end_at"],
            }
        )

    result = pd.DataFrame(rows)
    return result.sort_values(["total_media_views", "avg_media_views"], ascending=[False, False]).reset_index(drop=True)


def load_platform_data(base_dir: Path, platform_key: str) -> dict[str, Any]:
    platform_dir = base_dir / PLATFORM_META[platform_key]["folder"]
    csv_files = sorted(platform_dir.glob("*.csv"))
    frames = [
        _normalize_posts(pd.read_csv(csv_path, encoding="utf-8-sig"), base_dir, platform_key, csv_path)
        for csv_path in csv_files
    ]
    posts = pd.concat(frames, ignore_index=True) if frames else _empty_posts_frame()
    posts = posts.sort_values(["published_at", "account_name"], na_position="last").reset_index(drop=True)

    return {
        **PLATFORM_META[platform_key],
        "key": platform_key,
        "folder_path": str(platform_dir.relative_to(base_dir)),
        "has_data": not posts.empty,
        "files": [path.name for path in csv_files],
        "posts": posts,
        "summary": summarize_posts(posts),
        "account_summary": summarize_groups(posts, "account_name"),
    }


def load_repository_data(base_dir: Path) -> dict[str, Any]:
    platforms = {key: load_platform_data(base_dir, key) for key in PLATFORM_ORDER}
    active_posts = [platforms[key]["posts"] for key in PLATFORM_ORDER if platforms[key]["has_data"]]
    all_posts = pd.concat(active_posts, ignore_index=True) if active_posts else _empty_posts_frame()

    return {
        "platforms": platforms,
        "all_posts": all_posts,
        "summary": summarize_posts(all_posts),
    }

