# Scrapy settings for tugas project
#
# Tugas 3 Web Mining - Konfigurasi Crawling 2 Website
# =====================================================
#   Website Kecil : books.toscrape.com  (~1.000 buku, 50 halaman)
#   Website Besar : en.wikipedia.org    (jutaan artikel, graph crawl)

BOT_NAME = "tugas"

SPIDER_MODULES = ["tugas.spiders"]
NEWSPIDER_MODULE = "tugas.spiders"

ADDONS = {}

# ---- Identitas Bot ----
USER_AGENT = (
    "TugasWebMining/1.0 Scrapy/2.x "
    "(+https://docs.scrapy.org)"
)

# ---- Kepatuhan robots.txt ----
ROBOTSTXT_OBEY = True

# ---- Rate Limiting: sopan terhadap server target ----
DOWNLOAD_DELAY = 1                   # jeda 1 detik antar request
RANDOMIZE_DOWNLOAD_DELAY = True      # variasikan antara 0.5 - 1.5 detik
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2  # maks 2 request paralel per domain

# ---- Item Pipelines ----
# Nomor = prioritas eksekusi (urut dari kecil ke besar)
ITEM_PIPELINES = {
    "tugas.pipelines.BersihkanDataPipeline": 100,   # 1. Bersihkan data
    "tugas.pipelines.ValidasiDataPipeline":  200,   # 2. Validasi
    "tugas.pipelines.SimpanCSVPipeline":     300,   # 3. Simpan CSV
    "tugas.pipelines.SimpanJSONPipeline":    400,   # 4. Simpan JSON
    "tugas.pipelines.StatistikPipeline":     500,   # 5. Statistik akhir
}

# ---- AutoThrottle: adaptasi kecepatan crawling secara otomatis ----
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.5

# ---- Retry untuk request yang gagal ----
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 429]

# ---- Cache HTTP (aktifkan untuk development/testing) ----
# Berguna agar tidak perlu re-download halaman yang sama berulang kali
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 3600
# HTTPCACHE_DIR = "httpcache"

# ---- Encoding & Export ----
FEED_EXPORT_ENCODING = "utf-8"

# ---- Default Request Headers ----
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ---- Log Level ----
LOG_LEVEL = "INFO"

# ---- Suppress DeprecationWarning di Python 3.14 ----
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
