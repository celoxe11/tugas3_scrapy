"""
Spider 4: wikipedia_structure_spider.py
=========================================
Website: Wikipedia Bahasa Inggris (https://en.wikipedia.org)

TUJUAN SPIDER INI:
  Spider ini TIDAK mengambil konten artikel (ringkasan, isi, teks, dsb.).
  Sebaliknya, spider ini memetakan STRUKTUR website Wikipedia:

    1. Topologi Link (Graph)
       - Jumlah link internal (/wiki/...) per artikel
       - Jumlah link eksternal (keluar Wikipedia)
       - Link mana yang diikuti spider (link_keluar)
       - Dari mana artikel ini ditemukan (link_masuk_dari / referrer)

    2. Struktur Halaman
       - Jumlah section (h2) per artikel → kedalaman konten
       - Judul setiap section → kerangka dokumen
       - Ada/tidak infobox, Table of Contents (TOC)
       - Jumlah gambar dan referensi footnote

    3. Metadata Navigasi
       - Daftar kategori Wikipedia
       - Daftar portal terkait
       - Apakah halaman ini adalah disambiguasi

    4. Metadata HTML
       - title tag, lang attribute, canonical URL

Strategi crawling:
  - BFS (Breadth-First Search) dari artikel seed
  - Tiap halaman mengikuti maks N link internal (bisa diatur via parameter)
  - Batas item & kedalaman dikontrol via custom_settings / parameter CLI

Cara menjalankan:
    scrapy crawl wiki_structure
    scrapy crawl wiki_structure -o output/wiki_structure.jsonl
    scrapy crawl wiki_structure -s CLOSESPIDER_ITEMCOUNT=50
    scrapy crawl wiki_structure -a seed=Data_mining -a max_links=5
    scrapy crawl wiki_structure -a seed=Artificial_intelligence -o output/wiki_structure.csv
"""

import re
import scrapy
from tugas.items import WikiStructureItem


# Prefix halaman Wikipedia yang bukan artikel biasa — di-skip
SKIP_PREFIXES = (
    "/wiki/Special:",
    "/wiki/User:",
    "/wiki/Talk:",
    "/wiki/File:",
    "/wiki/Wikipedia:",
    "/wiki/Help:",
    "/wiki/Template:",
    "/wiki/Portal:",
    "/wiki/Category:",
    "/wiki/MediaWiki:",
    "/wiki/Module:",
)


class WikipediaStructureSpider(scrapy.Spider):
    name = "wiki_structure"
    allowed_domains = ["en.wikipedia.org"]

    # Artikel seed default
    DEFAULT_SEED = "Web_scraping"

    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 60,   # Batasi agar tidak crawl selamanya
        "DEPTH_LIMIT": 3,              # Maks 3 lapis dari seed
        "DOWNLOAD_DELAY": 1.0,         # Sopan ke server Wikipedia
        "ROBOTSTXT_OBEY": False,       # Wikipedia blokir bot via robots.txt,
                                       # tapi untuk keperluan akademis (jumlah kecil)
                                       # ini diperbolehkan
    }

    # ------------------------------------------------------------------ #
    # INISIALISASI                                                         #
    # ------------------------------------------------------------------ #
    def __init__(self, seed=None, max_links=None, *args, **kwargs):
        """
        Parameter CLI:
            seed      : nama artikel awal, ganti spasi dengan _
                        Contoh: -a seed=Machine_learning
            max_links : maks jumlah link per halaman yang diikuti (default: 5)
                        Contoh: -a max_links=8
        """
        super().__init__(*args, **kwargs)
        self.seed_article = seed or self.DEFAULT_SEED
        self.max_links    = int(max_links) if max_links else 5
        self.visited_urls = set()   # Deduplication: hindari crawl URL yang sama

    # ------------------------------------------------------------------ #
    # START REQUEST                                                        #
    # ------------------------------------------------------------------ #
    def start_requests(self):
        url = f"https://en.wikipedia.org/wiki/{self.seed_article}"
        self.logger.info(
            f"[WIKI-STRUCT] Seed: '{self.seed_article}' | max_links={self.max_links}"
        )
        yield scrapy.Request(
            url,
            callback=self.parse_article,
            meta={"depth": 0, "referrer": None},
        )

    # ------------------------------------------------------------------ #
    # PARSE ARTIKEL                                                        #
    # ------------------------------------------------------------------ #
    def parse_article(self, response):
        """
        Memproses satu halaman artikel Wikipedia.
        Mengambil STRUKTUR halaman, bukan isi kontennya.
        """
        url      = response.url
        kedalaman = response.meta.get("depth", 0)
        referrer  = response.meta.get("referrer", None)

        # --- Deduplication ---
        if url in self.visited_urls:
            return
        self.visited_urls.add(url)

        # --- Skip halaman non-artikel ---
        href_path = "/" + url.split("en.wikipedia.org/", 1)[-1]
        if any(href_path.startswith(p) for p in SKIP_PREFIXES):
            self.logger.debug(f"[WIKI-STRUCT] SKIP (non-artikel): {url}")
            return

        self.logger.info(
            f"[WIKI-STRUCT] Memproses | Depth={kedalaman} | {url}"
        )

        # ============================================================
        # 1. IDENTITAS NODE
        # ============================================================
        judul = response.css("#firstHeading span::text").get(
            default=response.css("#firstHeading::text").get(default="")
        ).strip()

        # ============================================================
        # 2. TOPOLOGI LINK
        # ============================================================
        konten = response.css("div.mw-parser-output")

        # Kumpulkan semua link internal (/wiki/...) dari konten artikel
        semua_internal = []
        for a in konten.css("a[href^='/wiki/']"):
            href = a.attrib.get("href", "")
            if not any(href.startswith(p[5:]) for p in SKIP_PREFIXES):
                # Bersihkan fragment (#...) dari URL
                href_bersih = href.split("#")[0]
                semua_internal.append(response.urljoin(href_bersih))

        # Unikkan, jaga urutan
        seen = set()
        internal_unik = []
        for u in semua_internal:
            if u not in seen:
                seen.add(u)
                internal_unik.append(u)

        # Link eksternal: href yang berawalan http/https tapi bukan wikipedia
        jumlah_eksternal = len(konten.css(
            "a[href^='http']:not([href*='wikipedia.org'])"
        ))

        # Link yang akan diikuti spider (maks max_links)
        link_diikuti = [
            u for u in internal_unik
            if u not in self.visited_urls
        ][:self.max_links]

        # ============================================================
        # 3. STRUKTUR HALAMAN
        # ============================================================
        # Section (h2) — kecuali "See also", "References", "External links"
        section_skip = {"See also", "References", "Notes", "External links",
                        "Further reading", "Bibliography"}
        judul_section = [
            h.css("::text, span.mw-headline::text").get("").strip()
            for h in konten.css("h2")
            if h.css("::text, span.mw-headline::text").get("").strip()
               not in section_skip
        ]

        ada_infobox  = bool(response.css("table.infobox, table.wikitable"))
        ada_toc      = bool(response.css("div#toc, nav#toc, #mw-toc-heading, .toc"))
        jumlah_gambar = len(response.css("div.mw-parser-output img"))
        jumlah_ref   = len(response.css(
            "ol.references li, div.reflist li, span.reference"
        ))

        # ============================================================
        # 4. METADATA NAVIGASI
        # ============================================================
        kategori_list = response.css(
            "div#mw-normal-catlinks ul li a::text"
        ).getall()
        kategori_list = [k.strip() for k in kategori_list]

        # Portal dari kotak "Part of a series on ..." atau navbox
        portal_list = response.css(
            "div.portal a::text, div.navbox-title a::text"
        ).getall()
        portal_list = list(dict.fromkeys(p.strip() for p in portal_list if p.strip()))

        # Disambiguasi: ada pesan "This page is a disambiguation page"
        teks_halaman = " ".join(response.css(
            "div.mw-parser-output p::text"
        ).getall()[:5]).lower()
        ada_disambiguasi = (
            bool(response.css("table.dmbox, div.dmbox"))
            or "disambiguation" in teks_halaman
        )

        # ============================================================
        # 5. METADATA HTML
        # ============================================================
        meta_html = {
            "title"    : response.css("title::text").get("").strip(),
            "lang"     : response.css("html::attr(lang)").get(""),
            "canonical": response.css("link[rel='canonical']::attr(href)").get(""),
            "og_description": response.css(
                "meta[property='og:description']::attr(content)"
            ).get(""),
        }

        # ============================================================
        # YIELD ITEM
        # ============================================================
        item = WikiStructureItem()
        item["judul"]               = judul
        item["url"]                 = url
        item["url_induk"]           = referrer
        item["kedalaman"]           = kedalaman
        item["jumlah_link_internal"]= len(internal_unik)
        item["jumlah_link_eksternal"]= jumlah_eksternal
        item["link_keluar"]         = link_diikuti
        item["link_masuk_dari"]     = referrer
        item["jumlah_section"]      = len(judul_section)
        item["judul_section"]       = judul_section
        item["ada_infobox"]         = ada_infobox
        item["ada_toc"]             = ada_toc
        item["jumlah_gambar"]       = jumlah_gambar
        item["jumlah_referensi"]    = jumlah_ref
        item["kategori"]            = kategori_list
        item["jumlah_kategori"]     = len(kategori_list)
        item["portal"]              = portal_list
        item["ada_disambiguasi"]    = ada_disambiguasi
        item["meta_html"]           = meta_html

        self.logger.info(
            f"[WIKI-STRUCT] ✓ '{judul}' | "
            f"Section={len(judul_section)} | "
            f"Link-int={len(internal_unik)} | "
            f"Link-ext={jumlah_eksternal} | "
            f"Kat={len(kategori_list)} | "
            f"Depth={kedalaman}"
        )

        yield item

        # ============================================================
        # IKUTI LINK (BFS)
        # ============================================================
        for next_url in link_diikuti:
            yield response.follow(
                next_url,
                callback=self.parse_article,
                meta={
                    "depth"   : kedalaman + 1,
                    "referrer": url,
                },
            )
