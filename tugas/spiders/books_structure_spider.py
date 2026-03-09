"""
Spider 3: books_structure_spider.py
=====================================
Website: Books to Scrape (https://books.toscrape.com)

TUJUAN SPIDER INI:
  Spider ini TIDAK mengambil konten buku (judul, harga, rating, dsb.).
  Sebaliknya, spider ini memetakan STRUKTUR website:
    - Hirarki navigasi (home → kategori → listing → pagination)
    - Daftar semua kategori beserta URL-nya
    - Jumlah halaman pagination per kategori
    - Jumlah buku per kategori
    - Metadata HTML tiap halaman (title tag, breadcrumb)
    - Peta link (link_anak) per node halaman

Struktur yang dihasilkan menggambarkan "kerangka" website, bukan isinya.

Output fields (BookStructureItem):
  tipe           : 'home' | 'kategori' | 'listing'
  nama           : nama halaman / kategori
  url            : URL halaman ini
  url_induk      : URL halaman parent
  kedalaman      : kedalaman dari root (home = 0)
  jumlah_buku    : total buku di kategori (dari teks "X results")
  jumlah_halaman : total halaman pagination di kategori
  nomor_halaman  : nomor halaman saat ini (1-based)
  tag_navigasi   : list elemen nav yang ditemukan di halaman
  link_anak      : list URL child langsung (sub-halaman atau next-page)
  meta_html      : dict berisi title, meta description, breadcrumb

Cara menjalankan:
    scrapy crawl books_structure
    scrapy crawl books_structure -o output/books_structure.jsonl
    scrapy crawl books_structure -o output/books_structure.csv
"""

import re
import scrapy
from tugas.items import BookStructureItem


class BooksStructureSpider(scrapy.Spider):
    name = "books_structure"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]

    # Override settings khusus spider ini
    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 0,   # 0 = tanpa batas
        "DOWNLOAD_DELAY": 0.5,
        "DEPTH_LIMIT": 5,             # Batas kedalaman crawl
        # Pipeline khusus bisa ditambahkan di sini jika diperlukan
    }

    # ------------------------------------------------------------------ #
    # HALAMAN UTAMA (HOME)                                                 #
    # ------------------------------------------------------------------ #
    def parse(self, response, **kwargs):
        """
        Entry point: halaman utama books.toscrape.com
        Tugas:
          1. Yield item untuk node 'home'
          2. Ambil semua kategori dari sidebar navigasi
          3. Crawl tiap kategori
        """
        self.logger.info("[STRUCTURE] Memproses halaman HOME")

        # --- Kumpulkan semua kategori dari sidebar ---
        kategori_links = response.css("div.side_categories ul li a")
        child_urls = []

        for link in kategori_links:
            nama_kat = link.css("::text").get("").strip()
            url_kat  = response.urljoin(link.attrib.get("href", ""))

            # Skip link "Books" (root kategori) jika muncul
            if nama_kat.lower() == "books":
                continue

            child_urls.append(url_kat)

        # --- Yield item untuk HOME ---
        yield self._build_item(
            tipe="home",
            nama="Home",
            url=response.url,
            url_induk=None,
            kedalaman=0,
            jumlah_buku=self._extract_jumlah_buku(response),
            jumlah_halaman=self._hitung_total_halaman(response),
            nomor_halaman=1,
            response=response,
            link_anak=child_urls,
        )

        # --- Crawl tiap halaman kategori ---
        for link in kategori_links:
            nama_kat = link.css("::text").get("").strip()
            url_kat  = response.urljoin(link.attrib.get("href", ""))

            if nama_kat.lower() == "books":
                continue

            yield response.follow(
                url_kat,
                callback=self.parse_kategori,
                cb_kwargs={
                    "nama_kategori": nama_kat,
                    "url_induk": response.url,
                    "kedalaman": 1,
                },
            )

    # ------------------------------------------------------------------ #
    # HALAMAN KATEGORI / LISTING (halaman 1)                              #
    # ------------------------------------------------------------------ #
    def parse_kategori(self, response, nama_kategori, url_induk, kedalaman):
        """
        Memproses halaman pertama suatu kategori.
        Tugas:
          1. Hitung total buku & total halaman pagination
          2. Yield item untuk node 'kategori'
          3. Ikuti semua halaman pagination berikutnya
        """
        self.logger.info(
            f"[STRUCTURE] Kategori: '{nama_kategori}' | "
            f"Halaman 1 | Kedalaman {kedalaman} | {response.url}"
        )

        total_halaman = self._hitung_total_halaman(response)
        jumlah_buku   = self._extract_jumlah_buku(response)

        # Link anak = semua halaman pagination selanjutnya
        child_urls = []
        if total_halaman > 1:
            next_href = response.css("li.next a::attr(href)").get()
            if next_href:
                child_urls.append(response.urljoin(next_href))

        # Yield item halaman listing pertama kategori
        yield self._build_item(
            tipe="kategori",
            nama=nama_kategori,
            url=response.url,
            url_induk=url_induk,
            kedalaman=kedalaman,
            jumlah_buku=jumlah_buku,
            jumlah_halaman=total_halaman,
            nomor_halaman=1,
            response=response,
            link_anak=child_urls,
        )

        # Ikuti halaman-halaman berikutnya (pagination)
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_listing_page,
                cb_kwargs={
                    "nama_kategori": nama_kategori,
                    "url_induk": response.url,
                    "kedalaman": kedalaman,
                    "nomor_halaman": 2,
                    "total_halaman": total_halaman,
                    "jumlah_buku": jumlah_buku,
                },
            )

    # ------------------------------------------------------------------ #
    # HALAMAN LISTING (halaman 2, 3, ... dari suatu kategori)             #
    # ------------------------------------------------------------------ #
    def parse_listing_page(
        self, response, nama_kategori, url_induk, kedalaman,
        nomor_halaman, total_halaman, jumlah_buku
    ):
        """
        Memproses halaman listing ke-N (N > 1) dari suatu kategori.
        Hanya merekam metadata struktur, TIDAK mengambil data buku.
        """
        self.logger.info(
            f"[STRUCTURE] Kategori: '{nama_kategori}' | "
            f"Halaman {nomor_halaman}/{total_halaman} | {response.url}"
        )

        # Link anak = halaman berikutnya (jika ada)
        child_urls = []
        next_href  = response.css("li.next a::attr(href)").get()
        if next_href:
            child_urls.append(response.urljoin(next_href))

        yield self._build_item(
            tipe="listing",
            nama=f"{nama_kategori} — Halaman {nomor_halaman}",
            url=response.url,
            url_induk=url_induk,
            kedalaman=kedalaman,
            jumlah_buku=jumlah_buku,
            jumlah_halaman=total_halaman,
            nomor_halaman=nomor_halaman,
            response=response,
            link_anak=child_urls,
        )

        # Ikuti halaman berikutnya
        if next_href:
            yield response.follow(
                next_href,
                callback=self.parse_listing_page,
                cb_kwargs={
                    "nama_kategori": nama_kategori,
                    "url_induk": response.url,
                    "kedalaman": kedalaman,
                    "nomor_halaman": nomor_halaman + 1,
                    "total_halaman": total_halaman,
                    "jumlah_buku": jumlah_buku,
                },
            )

    # ------------------------------------------------------------------ #
    # HELPER: Bangun item BookStructureItem                                #
    # ------------------------------------------------------------------ #
    def _build_item(
        self, tipe, nama, url, url_induk, kedalaman,
        jumlah_buku, jumlah_halaman, nomor_halaman, response, link_anak
    ):
        item = BookStructureItem()
        item["tipe"]           = tipe
        item["nama"]           = nama
        item["url"]            = url
        item["url_induk"]      = url_induk
        item["kedalaman"]      = kedalaman
        item["jumlah_buku"]    = jumlah_buku
        item["jumlah_halaman"] = jumlah_halaman
        item["nomor_halaman"]  = nomor_halaman
        item["tag_navigasi"]   = self._extract_nav_tags(response)
        item["link_anak"]      = link_anak
        item["meta_html"]      = self._extract_meta(response)
        return item

    # ------------------------------------------------------------------ #
    # HELPER: Ekstrak jumlah buku dari teks "X results"                   #
    # ------------------------------------------------------------------ #
    def _extract_jumlah_buku(self, response):
        teks = response.css("form.form-horizontal strong::text").get("")
        angka = re.search(r"(\d+)", teks)
        return int(angka.group(1)) if angka else None

    # ------------------------------------------------------------------ #
    # HELPER: Hitung total halaman dari pagination atau jumlah buku        #
    # ------------------------------------------------------------------ #
    def _hitung_total_halaman(self, response):
        # Coba dari teks "Page X of Y"
        teks_pager = response.css("li.current::text").get("").strip()
        cocok = re.search(r"Page\s+\d+\s+of\s+(\d+)", teks_pager, re.IGNORECASE)
        if cocok:
            return int(cocok.group(1))

        # Fallback: hitung dari jumlah buku (20 buku per halaman)
        jumlah = self._extract_jumlah_buku(response)
        if jumlah:
            import math
            return math.ceil(jumlah / 20)

        # Jika tidak ada pagination = 1 halaman
        return 1

    # ------------------------------------------------------------------ #
    # HELPER: Kumpulkan elemen navigasi yang ada di halaman               #
    # ------------------------------------------------------------------ #
    def _extract_nav_tags(self, response):
        nav_info = []

        # Breadcrumb
        breadcrumbs = response.css("ul.breadcrumb li a::text").getall()
        if breadcrumbs:
            nav_info.append(f"breadcrumb:{' > '.join(b.strip() for b in breadcrumbs)}")

        # Sidebar kategori
        sidebar_count = len(response.css("div.side_categories ul li a"))
        if sidebar_count:
            nav_info.append(f"sidebar_kategori:{sidebar_count} item")

        # Pagination
        if response.css("ul.pager"):
            prev_exists = bool(response.css("li.previous"))
            next_exists = bool(response.css("li.next"))
            nav_info.append(
                f"pagination:prev={'ada' if prev_exists else 'tidak'},"
                f"next={'ada' if next_exists else 'tidak'}"
            )

        # Header/logo
        if response.css("div.header-bar"):
            nav_info.append("header:ada")

        return nav_info

    # ------------------------------------------------------------------ #
    # HELPER: Ekstrak metadata HTML halaman                               #
    # ------------------------------------------------------------------ #
    def _extract_meta(self, response):
        title        = response.css("title::text").get("").strip()
        meta_desc    = response.css(
            "meta[name='description']::attr(content)"
        ).get("").strip()

        breadcrumbs  = [
            b.strip()
            for b in response.css("ul.breadcrumb li::text, ul.breadcrumb li a::text").getall()
            if b.strip()
        ]

        # Hitung jumlah artikel buku di halaman (div/article product_pod)
        jumlah_artikel = len(response.css("article.product_pod"))

        return {
            "title"          : title,
            "meta_description": meta_desc,
            "breadcrumb"     : " > ".join(breadcrumbs) if breadcrumbs else None,
            "jumlah_artikel_di_halaman": jumlah_artikel,
        }
