"""
Spider 2: wikipedia_spider.py
==============================
Website BESAR: Wikipedia Bahasa Inggris (https://en.wikipedia.org)

Karakteristik website ini:
- Jutaan artikel yang saling terhubung (graph besar)
- Setiap artikel punya puluhan hingga ratusan internal links
- Crawling mudah "meledak" jika tidak dibatasi depth/jumlah item
- Representasi nyata dari crawling website besar skala internet

Strategi crawling (BFS - Breadth First Search):
1. Mulai dari artikel "Web scraping" sebagai seed
2. Ekstrak judul, ringkasan, kategori, dan internal links
3. Ikuti internal links ke kedalaman maksimal (max_depth)
4. Hentikan setelah mencapai batas item atau depth

Cara menjalankan:
    scrapy crawl wikipedia
    scrapy crawl wikipedia -s CLOSESPIDER_ITEMCOUNT=30
    scrapy crawl wikipedia -a max_depth=2 -a seed=Artificial_intelligence
"""

import re
import scrapy
from tugas.items import ArticleItem


class WikipediaSpider(scrapy.Spider):
    name = "wikipedia"
    allowed_domains = ["en.wikipedia.org"]

    # Artikel seed awal yang di-crawl
    DEFAULT_SEED = "Web_scraping"

    custom_settings = {
        # Batasi item agar tidak crawl jutaan halaman
        "CLOSESPIDER_ITEMCOUNT": 50,
        # Kedalaman maksimal link yang diikuti
        "DEPTH_LIMIT": 3,
        # Jeda lebih lama untuk website besar, sopan terhadap server
        "DOWNLOAD_DELAY": 1.0,
        # Wikipedia robots.txt memblokir bots umum, tapi kontennya open-access.
        # Untuk keperluan akademis/tugas dengan jumlah kecil, ini diizinkan.
        "ROBOTSTXT_OBEY": False,
    }

    def __init__(self, seed=None, *args, **kwargs):
        """
        Parameter:
            seed : nama artikel awal (tanpa spasi, ganti dengan _)
                   Contoh: 'Machine_learning', 'Data_mining'
        """
        super().__init__(*args, **kwargs)
        self.seed_article = seed or self.DEFAULT_SEED
        self.visited_urls = set()  # Hindari crawl URL yang sama dua kali

    def start_requests(self):
        """
        Override start_requests untuk URL awal yang dinamis (berdasarkan
        parameter seed). Ini cara yang benar menggantikan @property start_urls
        karena Scrapy 2.14 mencoba set self.start_urls=[] di __init__.
        """
        url = f"https://en.wikipedia.org/wiki/{self.seed_article}"
        self.logger.info(f"[WIKI] Seed artikel: {self.seed_article} | {url}")
        yield scrapy.Request(url, callback=self.parse, meta={"depth": 0})

    def parse(self, response):
        """
        Parsing satu halaman artikel Wikipedia.
        Ekstrak info artikel, lalu ikuti internal links.
        """
        url = response.url

        # Lewati halaman bukan artikel (Special:, User:, Talk:, File:, dll.)
        if any(prefix in url for prefix in [
            "Special:", "User:", "Talk:", "File:", "Wikipedia:",
            "Help:", "Template:", "Portal:", "Category:", "action="
        ]):
            return

        if url in self.visited_urls:
            return
        self.visited_urls.add(url)

        # ---- Ekstrak data artikel ----
        item = ArticleItem()

        # Judul artikel
        item["judul"] = response.css("#firstHeading span::text").get(
            default=response.css("#firstHeading::text").get(default="")
        ).strip()

        # Ringkasan: paragraf pertama yang tidak kosong & bukan tabel
        ringkasan = ""
        for paragraf in response.css("div.mw-parser-output > p"):
            teks = paragraf.css("::text").getall()
            teks_bersih = " ".join(t.strip() for t in teks if t.strip())
            # Hapus referensi [1], [2], dll.
            teks_bersih = re.sub(r'\[\d+\]', '', teks_bersih).strip()
            if len(teks_bersih) > 50:  # Abaikan paragraf sangat pendek
                ringkasan = teks_bersih
                break
        item["ringkasan"] = ringkasan[:500] + "..." if len(ringkasan) > 500 else ringkasan

        # Kategori artikel
        kategori_list = response.css(
            "div#mw-normal-catlinks ul li a::text"
        ).getall()
        item["kategori"] = [k.strip() for k in kategori_list]

        # URL artikel ini
        item["url"] = url

        # Kedalaman (depth) dari halaman awal
        item["kedalaman"] = response.meta.get("depth", 0)

        # Estimasi jumlah kata dari seluruh konten artikel
        semua_teks = response.css(
            "div.mw-parser-output p::text"
        ).getall()
        item["jumlah_kata"] = len(" ".join(semua_teks).split())

        # Internal links ke artikel lain (maks 10 per halaman agar tidak meledak)
        internal_links = []
        for link in response.css("div.mw-parser-output a[href^='/wiki/']"):
            href = link.attrib.get("href", "")
            # Filter: hanya artikel normal (bukan file, special, dll.)
            if ":" not in href and href.startswith("/wiki/"):
                full_url = response.urljoin(href)
                link_text = link.css("::text").get("").strip()
                if link_text:
                    internal_links.append(f"{link_text} ({full_url})")

        item["link_terkait"] = internal_links[:10]  # Simpan maks 10 link

        self.logger.info(
            f"[WIKI] ✓ Artikel: '{item['judul']}' | "
            f"Depth: {item['kedalaman']} | "
            f"Kata: {item['jumlah_kata']} | "
            f"Kategori: {len(item['kategori'])}"
        )

        yield item

        # ---- Ikuti internal links (BFS crawl) ----
        # Batasi: hanya 5 link pertama per halaman agar tidak meledak
        link_diikuti = 0
        for link in response.css("div.mw-parser-output a[href^='/wiki/']"):
            if link_diikuti >= 5:
                break

            href = link.attrib.get("href", "")
            if ":" in href:  # Skip Special:, File:, dll.
                continue

            next_url = response.urljoin(href)
            if next_url not in self.visited_urls:
                link_diikuti += 1
                yield response.follow(
                    next_url,
                    callback=self.parse,
                    meta={"depth": item["kedalaman"] + 1},
                )
