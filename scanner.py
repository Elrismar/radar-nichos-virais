
import os
import json
import time
import datetime
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
CUSTOM_QUERY = os.environ.get("CUSTOM_QUERY", "").strip()[:100]
BASE = "https://www.googleapis.com/youtube/v3"
TODAY = datetime.datetime.now(datetime.timezone.utc)
DAY = TODAY.strftime("%Y-%m-%d")

SEARCH_CALLS_MAX = 48
TRACKED_MAX = 1800
RESULTS_MAX = 500
WINDOW_DAYS = 30
SMALL_SUBSCRIBERS = 50000
FEW_VIDEOS = 30
TIMEOUT = 30

# Temas variados: entretenimento, negócios, esportes, cultura,
# tecnologia, jogos, educação, religião, beleza, culinária etc.
QUERIES = [
    # Histórias, mistérios e curiosidades
    "true stories", "untold history", "historical mysteries",
    "strange facts", "unsolved mysteries", "real life stories",
    "forgotten people", "dark history", "urban legends",
    "historias curiosas", "historias reales", "misterios sin resolver",
    "historias de terror", "curiosidades", "historia desconocida",
    "histoires vraies", "mystères historiques",
    "wahre Geschichten", "storie vere", "misteri irrisolti",

    # Ciência, tecnologia e espaço
    "science discoveries", "space discoveries", "technology explained",
    "artificial intelligence news", "future technology",
    "experiments explained", "engineering inventions",
    "curiosidades científicas", "descobertas científicas",
    "découvertes scientifiques", "Wissenschaft erklärt",
    "scoperte scientifiche", "科学の雑学", "科技揭秘",

    # Negócios, dinheiro e carreira
    "business case studies", "entrepreneurship stories",
    "personal finance education", "company success stories",
    "marketing strategies", "career advice", "economic explainers",
    "negocios rentables", "educacion financiera",
    "histórias de empreendedorismo", "finanças pessoais",
    "histoires d'entrepreneurs", "Unternehmergeschichten",

    # Esportes e competições
    "football stories", "basketball highlights analysis",
    "sports rivalries", "athlete biographies",
    "combat sports analysis", "extreme sports",
    "historias del futbol", "histórias do futebol",
    "histoires du sport", "Sportgeschichten",

    # Jogos e cultura gamer
    "gaming secrets", "video game lore", "game challenges",
    "gaming news", "retro gaming", "Minecraft builds",
    "Roblox stories", "historias de videojuegos",
    "jeux vidéo secrets", "Videospiel Fakten",

    # Cinema, música e entretenimento
    "movie analysis", "celebrity stories", "film trivia",
    "music history", "animation analysis", "TV show theories",
    "behind the scenes", "cultura pop",
    "curiosidades de filmes", "histórias da música",
    "coulisses du cinéma", "Filmgeheimnisse",

    # Culinária, beleza e estilo de vida
    "easy recipes", "street food", "food experiments",
    "beauty transformations", "skincare education",
    "fashion trends", "home organization", "DIY projects",
    "recetas faciles", "comida callejera",
    "receitas fáceis", "comida de rua",
    "recettes faciles", "einfache Rezepte",

    # Educação, psicologia e desenvolvimento pessoal
    "psychology explained", "learning techniques",
    "language learning tips", "life lessons",
    "communication skills", "philosophy explained",
    "productivity methods", "educacion y aprendizaje",
    "psicologia explicada", "dicas de estudo",
    "psychologie erklärt", "apprentissage facile",

    # Natureza, animais e meio ambiente
    "wildlife behavior", "ocean discoveries", "animal behavior",
    "natural disasters explained", "extreme weather",
    "environmental discoveries", "vida selvagem",
    "curiosidades de animales", "faune sauvage",

    # Religião, mitologia e arqueologia
    "biblical mysteries", "religious history",
    "mythology explained", "archaeological discoveries",
    "ancient civilizations", "religious curiosities",
    "misterios biblicos", "curiosidades da Bíblia",
    "mitologia", "descobertas arqueológicas",
    "mythologie", "archäologische Entdeckungen",

    # Notícias, sociedade, viagens e cotidiano
    "explained world events", "geography facts",
    "travel hidden gems", "cultural differences",
    "consumer product reviews", "everyday science",
    "historias de viajes", "curiosidades del mundo",
    "destinos escondidos", "kulturelle Unterschiede",

    # Formatos e públicos diversos
    "long-form documentaries", "video essays", "in-depth video essays",
    "satisfying videos", "restoration projects",
    "craftsmanship", "survival skills", "incredible inventions",
    "comedy sketches", "pranks and reactions",
    "relatable situations", "family entertainment",
    "animation stories", "stop motion animation",
    "asmr", "podcast clips", "interviews",
    "news commentary", "product comparisons",
    "tutorial for beginners", "how things are made",

    # Nichos dark e narrativas sem rosto
    "dark niche youtube channel", "faceless youtube channel ideas",
    "dark documentary", "dark stories explained", "disturbing facts explained",
    "forgotten crimes documentary", "criminal cases explained",
    "strange disappearances", "mysterious deaths history",
    "historical scandals explained", "forgotten disasters documentary",
    "dark side of history", "untold true crime stories",
    "internet mysteries explained", "lost media documentary",
    "dark facts about celebrities", "dark side of fame",
    "forgotten tragedies", "conspiracy theories debunked",
    "dark psychology stories", "psychological manipulation explained",
    "real stories that sound fake", "unbelievable true events",
    "documentary without narration", "faceless storytelling",
    "dark ambient music", "dark music mix", "dark classical music",
    "dark piano music", "dark cinematic music", "dark trap music",
    "dark phonk", "dark synthwave", "gothic music history",
    "dark music facts", "forgotten musicians", "musicians who disappeared",
    "music industry scandals", "untold music industry stories",
    "lost songs mysteries", "songs with dark meanings",
    "dark songs explained", "music lore explained",
    "histórias sombrias da música", "músicas com histórias macabras",
    "música dark sem voz", "mistérios da música",

    # Futebol, clubes, jogadores e histórias pouco conhecidas
    "football dark stories", "football scandals documentary",
    "football mysteries explained", "forgotten football players",
    "football clubs financial collapse", "football rivalries history",
    "football transfers that failed", "football corruption cases",
    "football stories nobody knows", "underrated football stories",
    "soccer business explained", "football tactics explained",
    "football wonderkids documentary", "football legends forgotten",
    "historias oscuras del futbol", "escándalos del fútbol",
    "histórias desconhecidas do futebol", "bastidores do futebol",
    "casos bizarros do futebol", "jogadores esquecidos futebol",
    "futebol feminino histórias", "história das torcidas",

    # Fórmula 1, automobilismo e transportes
    "Formula 1 dark stories", "Formula 1 scandals documentary",
    "F1 stories nobody knows", "forgotten Formula 1 drivers",
    "Formula 1 accidents explained", "F1 team failures history",
    "Formula 1 engineering explained", "F1 rivalries documentary",
    "Formula 1 business explained", "motorsport unsolved mysteries",
    "racing legends forgotten", "rally racing stories",
    "NASCAR dark history", "MotoGP rivalries",
    "histórias da Fórmula 1", "bastidores da F1",
    "acidentes históricos da Fórmula 1", "pilotos esquecidos da F1",

    # Outros esportes e competição
    "sports dark history", "sports scandals documentary",
    "Olympics controversies explained", "boxing dark stories",
    "MMA stories nobody knows", "WWE dark stories",
    "basketball scandals explained", "NBA forgotten players",
    "tennis scandals documentary", "cycling doping history",
    "cricket stories explained", "sports business scandals",
    "underdog sports stories", "athletes who lost everything",
    "histórias sombrias do esporte", "escândalos esportivos",

    # Crime, investigação, justiça e golpes
    "cold cases documentary", "forensic science cases",
    "fraud cases explained", "famous heists documentary",
    "art theft mysteries", "unsolved art crimes",
    "financial scams explained", "cult leaders documentary",
    "organized crime history", "mafia stories documentary",
    "cybercrime cases explained", "identity theft stories",
    "courtroom cases explained", "wrongful convictions documentary",
    "missing treasure mysteries", "historical assassinations explained",
    "true crime animation", "true crime maps",
    "casos criminais antigos", "golpes financeiros famosos",
    "crimes históricos explicados", "mistérios policiais reais",

    # Cultura adulta, prostituição e indústria sexual em contexto informativo
    "history of prostitution documentary", "sex work history",
    "prostitution laws around the world", "history of brothels",
    "adult industry business explained", "adult industry history",
    "famous scandals adult industry", "human trafficking awareness",
    "sex work policy debate", "história da prostituição",
    "prostituição na história", "legislação sobre trabalho sexual",
    "historia de la prostitución", "historia del trabajo sexual",

    # Celebridades, fama, internet e mídia
    "celebrity downfall documentary", "celebrity scandals explained",
    "influencer scandals documentary", "internet fame dark side",
    "youtuber rise and fall", "streamer controversies explained",
    "failed reality tv stars", "forgotten child stars",
    "celebrity feuds history", "cancelled celebrities explained",
    "viral trends that disappeared", "internet culture documentary",
    "histórias de influenciadores", "famosos que desapareceram",

    # Política, geopolítica e poder
    "political scandals documentary", "forgotten political events",
    "political propaganda explained", "dictators rise and fall",
    "political corruption cases", "geopolitical conflicts explained",
    "election controversies history", "intelligence agency history",
    "political leaders biographies", "government secrets declassified",
    "histórias políticas desconhecidas", "escândalos políticos históricos",

    # Economia, empresas, marcas e trabalho
    "company collapse documentary", "business failures explained",
    "brands that disappeared", "corporate scandals documentary",
    "marketing disasters history", "failed products documentary",
    "luxury industry secrets", "retail business dark side",
    "gig economy explained", "unusual jobs documentary",
    "workplace scandals history", "companies that went bankrupt",
    "empresas que faliram histórias", "marcas que desapareceram",

    # Relacionamentos, família e comportamento social
    "relationship psychology explained", "marriage customs around the world",
    "dating culture explained", "social experiments documentary",
    "family secrets true stories", "friendship psychology",
    "modern loneliness explained", "unusual communities documentary",
    "cult psychology explained", "social norms around the world",
    "psicologia dos relacionamentos", "costumes estranhos pelo mundo",

    # Saúde, corpo e medicina em formato educativo
    "medical mysteries explained", "medical history dark facts",
    "medical breakthroughs documentary", "rare conditions explained",
    "hospital history documentary", "medical fraud cases",
    "human body mysteries", "sleep science explained",
    "health myths debunked", "história sombria da medicina",
    "mistérios médicos explicados", "casos médicos históricos",

    # Ciência estranha, tecnologia obscura e futuro
    "failed inventions documentary", "technology disasters history",
    "AI scandals explained", "internet infrastructure explained",
    "cybersecurity stories documentary", "space mission failures",
    "abandoned technology projects", "weird engineering failures",
    "scientific fraud cases", "experiments that went wrong",
    "invenções fracassadas história", "projetos secretos desclassificados",

    # Horror, paranormal e lendas
    "paranormal investigations explained", "haunted places history",
    "creepy folklore around the world", "analog horror explained",
    "found footage horror lore", "horror game mysteries",
    "scary stories from history", "cryptid sightings explained",
    "ghost town documentary", "abandoned places dark history",
    "lendas urbanas brasileiras", "lugares abandonados histórias",
    "casos paranormais investigados", "terror analógico explicado",

    # Cinema, séries, animação e cultura pop
    "movie production disasters", "cancelled movies documentary",
    "lost television episodes", "animation studio scandals",
    "cartoon dark theories explained", "movie plot holes explained",
    "film endings explained", "forgotten science fiction films",
    "cinema history scandals", "failed TV shows documentary",
    "histórias sombrias do cinema", "filmes cancelados famosos",

    # Anime, mangá, quadrinhos e fandom
    "anime dark lore explained", "manga controversies explained",
    "anime production problems", "forgotten anime series",
    "comic book dark history", "superhero lore explained",
    "video game urban legends", "lost game prototypes",
    "histórias sombrias de animes", "mistérios de jogos antigos",

    # Jogos, apostas e competição digital (conteúdo informativo)
    "esports scandals documentary", "speedrunning controversies",
    "gaming industry failures", "video game lawsuits explained",
    "game studios that shut down", "gaming myths debunked",
    "competitive gaming dark stories", "forgotten esports teams",
    "histórias sombrias dos games", "estúdios de jogos que faliram",

    # Religião, seitas, mitologia e arqueologia controversa
    "religious scandals history", "lost religious texts explained",
    "ancient cults documentary", "mythology dark stories",
    "archaeological hoaxes explained", "forbidden archaeology claims",
    "religious mysteries documentary", "forgotten ancient religions",
    "seitas famosas história", "mistérios arqueológicos controversos",

    # Geografia, países, fronteiras e lugares extremos
    "strange borders around the world", "countries that no longer exist",
    "unrecognized countries explained", "forgotten towns documentary",
    "isolated communities documentary", "dangerous roads history",
    "abandoned islands documentary", "places people cannot visit",
    "fronteiras estranhas do mundo", "países que deixaram de existir",

    # Desastres, sobrevivência, aviação e mar
    "aviation disasters explained", "shipwreck mysteries documentary",
    "submarine disasters history", "survival stories documentary",
    "mountaineering tragedies explained", "industrial disasters history",
    "bridge failures documentary", "train disasters explained",
    "deep sea mysteries documentary", "disasters caused by human error",
    "desastres industriais históricos", "mistérios de naufrágios",

    # Moda, luxo, consumo e subculturas
    "fashion industry scandals", "luxury brands dark history",
    "sneaker culture documentary", "counterfeit market explained",
    "subcultures explained documentary", "streetwear history",
    "beauty industry controversies", "fashion trends that failed",
    "história sombria da moda", "subculturas urbanas explicadas",

    # Comédia, fracassos, reações e formatos de entretenimento
    "comedy history dark stories", "failed viral videos explained",
    "publicity stunts gone wrong", "pranks gone too far documentary",
    "awkward moments compilation analysis", "internet fails explained",
    "weird reality show moments", "strange competitions documentary",
    "histórias de fracassos virais", "pegadinhas que deram errado",

    # Temas em espanhol, francês, alemão, italiano e outros idiomas
    "historias oscuras de la música", "misterios del fútbol",
    "historias desconocidas de la Fórmula 1", "casos criminales sin resolver",
    "escándalos empresariales", "historias oscuras de famosos",
    "musique sombre histoires", "mystères du football",
    "histoires méconnues de la Formule 1", "affaires criminelles non résolues",
    "dunkle Musikgeschichte", "vergessene Fußballgeschichten",
    "unbekannte Formel 1 Geschichten", "wahre Kriminalfälle",
    "storie oscure della musica", "misteri del calcio",
    "storie sconosciute della Formula 1", "casi criminali irrisolti",
    "暗い音楽の歴史", "サッカーの知られざる話",
    "F1の知られざる物語", "足球历史故事", "音乐背后的黑暗故事"
]

# Idiomas e regiões de pesquisa.
# O país e o idioma são sinais de busca, não garantias de origem.
PAIRS = [
    ("en", "US"), ("en", "GB"), ("en", "CA"), ("en", "AU"),
    ("es", "MX"), ("es", "ES"), ("es", "AR"), ("pt", "BR"),
    ("pt", "PT"), ("fr", "FR"), ("fr", "CA"), ("de", "DE"),
    ("it", "IT"), ("hi", "IN"), ("ja", "JP"), ("ko", "KR"),
    ("id", "ID"), ("tr", "TR"), ("ar", "SA"), ("nl", "NL"),
    ("pl", "PL"), ("th", "TH"), ("vi", "VN"), ("sv", "SE"),
    ("ru", "RU"), ("zh", "TW"), ("zh", "HK"), ("da", "DK"),
    ("hr", "HR"), ("no", "NO"), ("fi", "FI"), ("cs", "CZ"),
    ("el", "GR"), ("he", "IL"), ("ro", "RO"), ("hu", "HU"),
    ("bn", "BD"), ("ta", "IN"), ("te", "IN"), ("ur", "PK")
]


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    temp.replace(path)


def api(endpoint, params, retries=3):
    if not API_KEY:
        raise RuntimeError("Falta o segredo YOUTUBE_API_KEY.")

    p = dict(params)
    p["key"] = API_KEY
    last_error = None

    for attempt in range(retries):
        try:
            response = requests.get(
                f"{BASE}/{endpoint}",
                params=p,
                timeout=TIMEOUT
            )

            if response.status_code == 403:
                try:
                    detail = response.json().get("error", {}).get(
                        "errors", [{}]
                    )[0].get("reason", "")
                except (ValueError, IndexError, AttributeError):
                    detail = ""

                raise RuntimeError(
                    f"YouTube API 403 ({detail or 'permissão ou cota'}). "
                    "Verifique a chave, a API ativada e a cota."
                )

            response.raise_for_status()
            return response.json()

        except RuntimeError:
            raise
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"Falha na API {endpoint}: {last_error}")


def chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_search_pool():
    # Distribui os temas por diferentes regiões em cada lote. A cada ciclo,
    # a região atribuída a cada tema avança, evitando concentrar uma execução
    # inteira em um único país.
    return [
        (query, *PAIRS[(query_index + region_offset) % len(PAIRS)])
        for region_offset in range(len(PAIRS))
        for query_index, query in enumerate(QUERIES)
    ]


def duration_seconds(value):
    """Converte duração ISO 8601 da API do YouTube para segundos."""
    match = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        str(value or "")
    )
    if not match:
        return 0
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


# Shorts podem ter até 3 minutos; a API não informa proporção 16:9.
# Mantemos apenas vídeos com mais de 180 segundos como filtro conservador.
MIN_LONG_FORM_SECONDS = 181


def score_candidate(video, channel, history):
    views = number(video.get("viewCount")) or 0
    subs = number(channel.get("subscriberCount"))
    video_count = number(channel.get("videoCount"))

    try:
        published = datetime.datetime.fromisoformat(
            video["publishedAt"].replace("Z", "+00:00")
        )
        video_age = max(
            0.25, (TODAY - published).total_seconds() / 86400
        )
    except (KeyError, TypeError, ValueError):
        video_age = 30

    try:
        created = datetime.datetime.fromisoformat(
            channel["publishedAt"].replace("Z", "+00:00")
        )
        channel_age = max(1, (TODAY - created).days)
    except (KeyError, TypeError, ValueError):
        channel_age = 9999

    prior = history.get(video["id"], [])
    velocity = None

    if prior:
        try:
            old = prior[-1]
            old_date = datetime.date.fromisoformat(old["date"])
            days_elapsed = max(
                1 / 24,
                (datetime.date.fromisoformat(DAY) - old_date).days
            )
            velocity = max(
                0, views - int(old.get("views", 0))
            ) / days_elapsed
        except (KeyError, TypeError, ValueError):
            velocity = None

    daily_average = views / video_age
    velocity_used = velocity if velocity is not None else daily_average

    reach_ratio = views / max(100, subs or 1000)
    ratio_score = min(30, 30 * min(10, reach_ratio) / 10)
    velocity_score = min(25, 25 * min(50000, velocity_used) / 50000)
    newness_score = 20 * max(0, 1 - min(channel_age, 730) / 730)
    few_videos_score = 15 * max(
        0, 1 - min(video_count or 1000, 100) / 100
    )
    recency_score = 10 * max(
        0, 1 - min(video_age, WINDOW_DAYS) / WINDOW_DAYS
    )
    score = round(
        ratio_score + velocity_score + newness_score
        + few_videos_score + recency_score, 1
    )

    signals = []
    if subs is not None and subs <= SMALL_SUBSCRIBERS:
        signals.append("canal pequeno")
    if video_count is not None and video_count <= FEW_VIDEOS:
        signals.append("poucos vídeos")
    if reach_ratio >= 3:
        signals.append("views ≥ 3× inscritos")
    if video_age <= 7:
        signals.append("publicado há até 7 dias")
    if velocity is not None and velocity > 0:
        signals.append("crescimento observado")

    return {
        "score": score,
        "signals": signals,
        "views": views,
        "subscribers": subs,
        "channelVideoCount": video_count,
        "channelAgeDays": channel_age,
        "videoAgeDays": round(video_age, 1),
        "viewsPerSubscriber": round(reach_ratio, 2),
        "viewsPerDayObserved": round(velocity, 1) if velocity is not None else None,
        "viewsPerDayAverage": round(daily_average, 1)
    }


def main():
    if not API_KEY:
        raise SystemExit("Defina o segredo YOUTUBE_API_KEY no GitHub.")

    candidates = read_json(DATA / "tracked.json", {})
    history = read_json(DATA / "history.json", {})
    run_meta = read_json(DATA / "run.json", {})

    run_count_value = number(run_meta.get("runCount"))
    # Migração segura do run.json antigo, que guardava apenas lastSearchCalls.
    # Como já houve coleta, começamos no segundo lote para evitar repetir
    # imediatamente a primeira faixa de buscas.
    run_count = run_count_value if run_count_value is not None else (
        1 if number(run_meta.get("lastSearchCalls")) else 0
    )
    pool = build_search_pool()

    # A cada execução, avança 48 posições na lista de combinações.
    # A rotação só reinicia depois de percorrer todo o conjunto.
    start = (run_count * SEARCH_CALLS_MAX) % len(pool)
    selected = [
        pool[(start + i) % len(pool)]
        for i in range(min(SEARCH_CALLS_MAX, len(pool)))
    ]
    # Uma busca personalizada opcional substitui a primeira busca do lote,
    # mantendo o limite total de chamadas search.list por execução.
    if CUSTOM_QUERY and selected:
        selected[0] = (CUSTOM_QUERY, "", "")

    since = (
        TODAY - datetime.timedelta(days=WINDOW_DAYS)
    ).isoformat(timespec="seconds").replace("+00:00", "Z")

    discovered = {}
    errors = []
    search_count = 0

    print(
        f"Execução {run_count + 1}: {len(selected)} buscas planejadas "
        f"entre {len(QUERIES)} temas e {len(PAIRS)} combinações "
        "de idioma/região."
    )

    for query, lang, region in selected:
        try:
            search_params = {
                "part": "snippet",
                "type": "video",
                "q": query,
                "publishedAfter": since,
                "order": "viewCount",
                "maxResults": 50,
                "safeSearch": "moderate"
            }
            if region:
                search_params["regionCode"] = region
            if lang:
                search_params["relevanceLanguage"] = lang
            data = api("search", search_params)
            search_count += 1

            for item in data.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if not video_id:
                    continue

                snippet = item.get("snippet", {})
                discovered[video_id] = {
                    "videoId": video_id,
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", "")[:500],
                    "channelId": snippet.get("channelId", ""),
                    "channelTitle": snippet.get("channelTitle", ""),
                    "publishedAt": snippet.get("publishedAt", ""),
                    "query": query,
                    "languageHint": lang,
                    "regionHint": region
                }

        except Exception as exc:
            errors.append(
                f"{query}/{lang}-{region}: {str(exc)[:180]}"
            )
            if "403" in str(exc):
                print("Erro de permissão/cota; interrompendo novas buscas.")
                break

    # Nunca marque uma coleta como recente se nenhuma busca foi bem-sucedida.
    # Isso evita publicar dados antigos com um timestamp novo quando a API falha.
    if search_count == 0:
        details = "; ".join(errors[:3]) or "A API não retornou buscas bem-sucedidas."
        raise SystemExit(
            "Coleta interrompida: nenhuma busca ao YouTube foi concluída; "
            "os resultados anteriores foram preservados. Detalhes: " + details
        )

    # Preserva candidatos antigos para comparar visualizações.
    for video_id, meta in candidates.items():
        discovered.setdefault(video_id, meta)

    video_details = {}
    video_ids = list(discovered.keys())

    for batch in chunks(video_ids, 50):
        try:
            data = api("videos", {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(batch),
                "maxResults": 50
            })
            for item in data.get("items", []):
                video_details[item["id"]] = item
        except Exception as exc:
            errors.append(f"videos.list: {str(exc)[:180]}")

    if video_ids and not video_details:
        details = "; ".join(errors[-3:]) or "videos.list não retornou detalhes."
        raise SystemExit(
            "Coleta interrompida: nenhum detalhe de vídeo foi recuperado; "
            "os resultados anteriores foram preservados. Detalhes: " + details
        )

    channel_ids = sorted({
        item.get("snippet", {}).get("channelId", "")
        for item in video_details.values()
        if item.get("snippet", {}).get("channelId")
    })

    channel_details = {}

    for batch in chunks(channel_ids, 50):
        try:
            data = api("channels", {
                "part": "snippet,statistics",
                "id": ",".join(batch),
                "maxResults": 50
            })
            for item in data.get("items", []):
                channel_details[item["id"]] = item
        except Exception as exc:
            errors.append(f"channels.list: {str(exc)[:180]}")

    results = []
    next_tracked = {}

    for video_id, item in video_details.items():
        duration = item.get("contentDetails", {}).get("duration")
        if duration_seconds(duration) < MIN_LONG_FORM_SECONDS:
            continue

        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        channel_id = snippet.get("channelId", "")
        channel = channel_details.get(channel_id, {})
        channel_stats = channel.get("statistics", {})
        channel_snippet = channel.get("snippet", {})
        meta = discovered.get(video_id, {})

        video_info = {
            "id": video_id,
            "title": snippet.get("title", meta.get("title", "")),
            "description": snippet.get(
                "description", meta.get("description", "")
            )[:500],
            "publishedAt": snippet.get(
                "publishedAt", meta.get("publishedAt", "")
            ),
            "defaultAudioLanguage": (
                snippet.get("defaultAudioLanguage")
                or snippet.get("defaultLanguage")
                or meta.get("languageHint")
            ),
            "duration": item.get("contentDetails", {}).get("duration"),
            "viewCount": stats.get("viewCount", 0)
        }

        channel_info = {
            "id": channel_id,
            "title": channel_snippet.get(
                "title", meta.get("channelTitle", "")
            ),
            "publishedAt": channel_snippet.get("publishedAt", ""),
            "subscriberCount": channel_stats.get("subscriberCount"),
            "videoCount": channel_stats.get("videoCount")
        }

        metrics = score_candidate(video_info, channel_info, history)

        row = {
            "videoId": video_id,
            "videoUrl": f"https://www.youtube.com/watch?v={video_id}",
            "title": video_info["title"],
            "description": video_info["description"],
            "publishedAt": video_info["publishedAt"],
            "duration": video_info["duration"],
            "language": video_info["defaultAudioLanguage"],
            "channelId": channel_id,
            "channelTitle": channel_info["title"],
            "channelUrl": (
                f"https://www.youtube.com/channel/{channel_id}"
                if channel_id else ""
            ),
            "channelCreatedAt": channel_info["publishedAt"],
            "thumbnail": (
                snippet.get("thumbnails", {}).get("medium", {}).get("url")
                or snippet.get("thumbnails", {}).get("default", {}).get("url")
            ),
            "query": meta.get("query"),
            "languageHint": meta.get("languageHint"),
            "regionHint": meta.get("regionHint"),
            **metrics
        }
        results.append(row)

        snapshots = history.get(video_id, [])
        snapshots.append({
            "date": DAY,
            "views": metrics["views"],
            "subscribers": metrics["subscribers"]
        })

        # Evita adicionar várias amostras iguais na mesma data.
        unique_dates = {}
        for snapshot in snapshots:
            unique_dates[snapshot.get("date", "")] = snapshot
        history[video_id] = list(unique_dates.values())[-30:]

        next_tracked[video_id] = {
            "videoId": video_id,
            "title": row["title"],
            "description": row["description"],
            "channelId": channel_id,
            "channelTitle": row["channelTitle"],
            "publishedAt": row["publishedAt"],
            "query": meta.get("query"),
            "languageHint": meta.get("languageHint"),
            "regionHint": meta.get("regionHint")
        }

    results.sort(key=lambda row: row["score"], reverse=True)

    next_tracked = {
        row["videoId"]: next_tracked[row["videoId"]]
        for row in results[:TRACKED_MAX]
        if row["videoId"] in next_tracked
    }

    cutoff = TODAY.date() - datetime.timedelta(days=30)
    pruned_history = {}

    for video_id in next_tracked:
        keep = []
        for snapshot in history.get(video_id, []):
            try:
                snapshot_date = datetime.date.fromisoformat(
                    snapshot.get("date", "")
                )
                if snapshot_date >= cutoff:
                    keep.append(snapshot)
            except (TypeError, ValueError):
                continue

        if keep:
            pruned_history[video_id] = keep[-30:]

    write_json(DATA / "tracked.json", next_tracked)
    write_json(DATA / "history.json", pruned_history)
    # candidateCount corresponde ao número realmente entregue ao painel.
    # totalCandidates mantém a quantidade processada antes do limite de saída.
    write_json(DATA / "results.json", {
        "generatedAt": TODAY.isoformat(),
        "date": DAY,
        "searchCalls": search_count,
        "searchCallsPlanned": SEARCH_CALLS_MAX,
        "candidateCount": min(len(results), RESULTS_MAX),
        "totalCandidates": len(results),
        "trackedCount": len(next_tracked),
        "errors": errors[:20],
        "results": results[:RESULTS_MAX]
    })
    write_json(DATA / "run.json", {
        "date": DAY,
        "lastSearchCalls": search_count,
        "runCount": run_count + 1,
        "nextSearchOffset": ((run_count + 1) * SEARCH_CALLS_MAX) % len(pool)
    })

    print(
        f"Concluído: {search_count} buscas, "
        f"{len(results)} vídeos processados, {len(errors)} avisos."
    )


if __name__ == "__main__":
    main()
