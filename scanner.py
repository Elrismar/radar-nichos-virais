import os, json, time, hashlib, datetime
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
BASE = "https://www.googleapis.com/youtube/v3"
TODAY = datetime.datetime.now(datetime.timezone.utc)
DAY = TODAY.strftime("%Y-%m-%d")
SEARCH_CALLS_MAX = 48
TRACKED_MAX = 1800
TIMEOUT = 30

# Intentionally varied themes and language/region pairs. Each run rotates the pairs.
QUERIES = [
    "true stories", "history mysteries", "science facts", "forgotten history",
    "strange facts", "space discoveries", "psychology facts", "survival stories",
    "ancient civilizations", "animal facts", "unsolved mysteries", "documentary",
    "historias curiosas", "mistérios históricos", "casos inexplicáveis",
    "historias reales", "curiosidades científicas", "historias de terror",
    "histoires vraies", "mystères historiques", "faits scientifiques",
    "wahre Geschichten", "Geschichte Geheimnisse", "Wissenschaft Fakten",
    "storie vere", "misteri storici", "fatti scientifici",
    "true crime stories", "mythology explained", "personal finance stories",
    "short documentary", "life lessons stories"
]
PAIRS = [
    ("en", "US"), ("en", "GB"), ("en", "CA"), ("en", "AU"),
    ("es", "MX"), ("es", "ES"), ("es", "AR"), ("pt", "BR"),
    ("pt", "PT"), ("fr", "FR"), ("fr", "CA"), ("de", "DE"),
    ("it", "IT"), ("hi", "IN"), ("ja", "JP"), ("ko", "KR"),
    ("id", "ID"), ("tr", "TR"), ("ar", "SA"), ("nl", "NL"),
    ("pl", "PL"), ("th", "TH"), ("vi", "VN"), ("sv", "SE")
]
WINDOW_DAYS = 30
SMALL_SUBSCRIBERS = 50000
FEW_VIDEOS = 30

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def api(endpoint, params, retries=3):
    if not API_KEY:
        raise RuntimeError("Falta o segredo YOUTUBE_API_KEY no ambiente.")
    p = dict(params)
    p["key"] = API_KEY
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE}/{endpoint}", params=p, timeout=TIMEOUT)
            if r.status_code == 403:
                raise RuntimeError("YouTube API retornou 403. Verifique a chave, API ativada e cota diária.")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise last

def chunks(items, n):
    for i in range(0, len(items), n):
        yield items[i:i+n]

def number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def score_candidate(video, channel, previous):
    views = number(video.get("viewCount")) or 0
    subs = number(channel.get("subscriberCount"))
    video_count = number(channel.get("videoCount"))
    published = video.get("publishedAt")
    channel_created = channel.get("publishedAt")
    now = TODAY
    try:
        video_age = max(0.25, (now - datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))).total_seconds()/86400)
    except Exception:
        video_age = 30
    try:
        channel_age = max(1, (now - datetime.datetime.fromisoformat(channel_created.replace("Z", "+00:00"))).days)
    except Exception:
        channel_age = 9999

    # Views/day is only a rough average until we have multiple snapshots.
    prior = previous.get(video["id"], [])
    velocity = None
    if prior:
        old = prior[-1]
        try:
            old_date = datetime.date.fromisoformat(old["date"])
            days = max(1/24, (datetime.date.fromisoformat(DAY) - old_date).days)
            velocity = max(0, views - int(old.get("views", 0))) / days
        except Exception:
            velocity = None
    daily_avg = views / video_age
    velocity_used = velocity if velocity is not None else daily_avg

    # Bounded components, intentionally transparent rather than pretending to predict virality.
    reach_ratio = views / max(100, subs or 1000)
    ratio_score = min(30, 30 * (min(10, reach_ratio) / 10))
    velocity_score = min(25, 25 * (min(50000, velocity_used) / 50000))
    newness_score = 20 * max(0, 1 - min(channel_age, 730) / 730)
    few_videos_score = 15 * max(0, 1 - min(video_count or 1000, 100) / 100)
    recency_score = 10 * max(0, 1 - min(video_age, WINDOW_DAYS) / WINDOW_DAYS)
    score = round(ratio_score + velocity_score + newness_score + few_videos_score + recency_score, 1)

    signals = []
    if subs is not None and subs <= SMALL_SUBSCRIBERS: signals.append("canal pequeno")
    if video_count is not None and video_count <= FEW_VIDEOS: signals.append("poucos vídeos")
    if reach_ratio >= 3: signals.append("views ≥ 3× inscritos")
    if video_age <= 7: signals.append("publicado há até 7 dias")
    if velocity is not None and velocity > 0: signals.append("crescimento observado")
    return {
        "score": score, "signals": signals, "views": views, "subscribers": subs,
        "channelVideoCount": video_count, "channelAgeDays": channel_age,
        "videoAgeDays": round(video_age, 1), "viewsPerSubscriber": round(reach_ratio, 2),
        "viewsPerDayObserved": round(velocity, 1) if velocity is not None else None,
        "viewsPerDayAverage": round(daily_avg, 1)
    }

def main():
    if not API_KEY:
        raise SystemExit("Defina YOUTUBE_API_KEY como variável de ambiente.")
    candidates = read_json(DATA / "tracked.json", {})
    history = read_json(DATA / "history.json", {})
    run_meta = read_json(DATA / "run.json", {})
    since = (TODAY - datetime.timedelta(days=WINDOW_DAYS)).isoformat(timespec="seconds").replace("+00:00", "Z")

    # Rotate the global language/region combinations daily; 48 searches max.
    seed = int(TODAY.strftime("%j"))
    selected = []
    for i in range(SEARCH_CALLS_MAX):
        q = QUERIES[(seed * 7 + i * 5) % len(QUERIES)]
        lang, region = PAIRS[(seed * 3 + i * 7) % len(PAIRS)]
        selected.append((q, lang, region))

    discovered = {}
    search_errors = []
    search_count = 0
    for q, lang, region in selected:
        try:
            data = api("search", {
                "part": "snippet", "type": "video", "q": q,
                "publishedAfter": since, "order": "viewCount", "maxResults": 50,
                "regionCode": region, "relevanceLanguage": lang,
                "safeSearch": "moderate"
            })
            search_count += 1
            for item in data.get("items", []):
                vid = item.get("id", {}).get("videoId")
                if not vid: continue
                discovered[vid] = {
                    "videoId": vid, "title": item.get("snippet", {}).get("title", ""),
                    "description": item.get("snippet", {}).get("description", "")[:500],
                    "channelId": item.get("snippet", {}).get("channelId", ""),
                    "channelTitle": item.get("snippet", {}).get("channelTitle", ""),
                    "publishedAt": item.get("snippet", {}).get("publishedAt", ""),
                    "query": q, "languageHint": lang, "regionHint": region
                }
        except Exception as e:
            search_errors.append(f"{q}/{lang}-{region}: {str(e)[:180]}")

    # Keep previously tracked candidates so that daily snapshots reveal growth.
    for vid, meta in candidates.items():
        discovered.setdefault(vid, meta)

    video_details = {}
    for batch in chunks(list(discovered.keys()), 50):
        try:
            data = api("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(batch), "maxResults": 50})
            for item in data.get("items", []):
                video_details[item["id"]] = item
        except Exception as e:
            search_errors.append("videos.list: " + str(e)[:180])

    channel_ids = list({v.get("snippet", {}).get("channelId") or discovered.get(vid, {}).get("channelId")
                        for vid, v in video_details.items()})
    channel_ids = [x for x in channel_ids if x]
    channel_details = {}
    for batch in chunks(channel_ids, 50):
        try:
            data = api("channels", {"part": "snippet,statistics", "id": ",".join(batch), "maxResults": 50})
            for item in data.get("items", []):
                channel_details[item["id"]] = item
        except Exception as e:
            search_errors.append("channels.list: " + str(e)[:180])

    results = []
    next_tracked = {}
    for vid, v in video_details.items():
        sn = v.get("snippet", {})
        st = v.get("statistics", {})
        ch_id = sn.get("channelId", "")
        ch = channel_details.get(ch_id, {})
        cs = ch.get("statistics", {})
        c_sn = ch.get("snippet", {})
        meta = discovered.get(vid, {})
        vinfo = {
            "id": vid, "title": sn.get("title", meta.get("title", "")),
            "description": sn.get("description", meta.get("description", ""))[:500],
            "publishedAt": sn.get("publishedAt", meta.get("publishedAt", "")),
            "defaultAudioLanguage": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or meta.get("languageHint"),
            "duration": v.get("contentDetails", {}).get("duration"),
            "viewCount": st.get("viewCount", 0)
        }
        cinfo = {
            "id": ch_id, "title": c_sn.get("title", meta.get("channelTitle", "")),
            "publishedAt": c_sn.get("publishedAt", ""),
            "subscriberCount": cs.get("subscriberCount"),
            "videoCount": cs.get("videoCount")
        }
        prev = history.get(vid, [])
        metrics = score_candidate(vinfo, cinfo, history)
        row = {
            "videoId": vid, "videoUrl": f"https://www.youtube.com/watch?v={vid}",
            "title": vinfo["title"], "description": vinfo["description"],
            "publishedAt": vinfo["publishedAt"], "duration": vinfo["duration"],
            "language": vinfo["defaultAudioLanguage"],
            "channelId": ch_id, "channelTitle": cinfo["title"],
            "channelUrl": f"https://www.youtube.com/channel/{ch_id}" if ch_id else "",
            "channelCreatedAt": cinfo["publishedAt"],
            "thumbnail": sn.get("thumbnails", {}).get("medium", {}).get("url") or sn.get("thumbnails", {}).get("default", {}).get("url"),
            "query": meta.get("query"), "languageHint": meta.get("languageHint"), "regionHint": meta.get("regionHint"),
            **metrics
        }
        results.append(row)
        snap = {"date": DAY, "views": metrics["views"], "subscribers": metrics["subscribers"]}
        new_hist = (prev + [snap])[-30:]
        history[vid] = new_hist
        next_tracked[vid] = {
            "videoId": vid, "title": row["title"], "description": row["description"],
            "channelId": ch_id, "channelTitle": row["channelTitle"], "publishedAt": row["publishedAt"],
            "query": meta.get("query"), "languageHint": meta.get("languageHint"), "regionHint": meta.get("regionHint")
        }

    results.sort(key=lambda x: x["score"], reverse=True)
    # Retain a bounded candidate set; prefer highest-scoring candidates for next day's tracking.
    next_tracked = {r["videoId"]: next_tracked[r["videoId"]] for r in results[:TRACKED_MAX] if r["videoId"] in next_tracked}
    # Retain only snapshots for tracked videos and no more than 30 days of history.
    cutoff = TODAY.date() - datetime.timedelta(days=30)
    pruned_history = {}
    for tracked_id in next_tracked:
        snaps = history.get(tracked_id, [])
        keep = []
        for snap_item in snaps:
            try:
                if datetime.date.fromisoformat(snap_item.get("date", "")) >= cutoff:
                    keep.append(snap_item)
            except Exception:
                continue
        if keep:
            pruned_history[tracked_id] = keep[-30:]
    write_json(DATA / "tracked.json", next_tracked)
    write_json(DATA / "history.json", pruned_history)
    write_json(DATA / "results.json", {
        "generatedAt": TODAY.isoformat(), "date": DAY, "searchCalls": search_count,
        "searchCallsPlanned": SEARCH_CALLS_MAX, "candidateCount": len(results),
        "errors": search_errors[:20], "results": results[:500]
    })
    write_json(DATA / "run.json", {"date": DAY, "lastSearchCalls": search_count})
    print(f"Concluído: {search_count} buscas, {len(results)} vídeos processados, {len(search_errors)} avisos.")

if __name__ == "__main__":
    main()
