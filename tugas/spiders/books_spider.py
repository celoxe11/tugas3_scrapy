"""
Spider 1: books_spider.py
=========================
Website KECIL: Books to Scrape (https://books.toscrape.com)

Karakteristik website ini:
- ~1.000 buku dalam 50 halaman listing
- 50 kategori berbeda
- Struktur HTML yang bersih dan konsisten
- Tidak memerlukan login / JavaScript
- Ideal sebagai contoh crawling website kecil-sedang

Strategi crawling:
1. Mulai dari halaman listing semua buku (catalogue page 1)
2. Ambil data tiap buku: judul, harga, rating, stok, kategori
3. Ikuti link "next" untuk crawl halaman berikutnya (pagination)

Cara menjalankan:
    scrapy crawl books
    scrapy crawl books -o output/books.csv
    scrapy crawl books -s CLOSESPIDER_ITEMCOUNT=50   (hanya 50 item)
"""

import scrapy
from tugas.items import BookItem


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    current_scraped_count = 0

    # Override settings khusus untuk spider ini
    custom_settings = {
        "CLOSESPIDER_ITEMCOUNT": 0,  # 0 = tidak ada batas (crawl semua)
        "DOWNLOAD_DELAY": 0.5,       # website kecil, toleran lebih cepat
    }

    # Konversi rating kata ke angka
    RATING_MAP = {
        "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5
    }

    def parse(self, response):
        limit = int(self.settings.get('CLOSESPIDER_ITEMCOUNT', 99999))
        if limit == 0: limit = 99999

        """
        Parse halaman listing buku. Setiap halaman berisi 20 buku.
        Setelah mengambil semua buku, ikuti tombol 'next' ke halaman berikutnya.
        """
        # Dapatkan nomor halaman dari URL untuk logging
        nomor_halaman = response.url.split("page-")[-1].replace(".html", "")
        self.logger.info(
            f"[BOOKS] Memproses halaman {nomor_halaman} | {response.url}"
        )

        # ---- Loop setiap artikel/buku di halaman ini ----
        for artikel in response.css("article.product_pod"):
            # Cek apakah sudah mencapai limit sebelum yield
            if self.current_scraped_count >= limit:
                self.logger.info(f"--- LIMIT {limit} TERCAPAI. BERHENTI ---")
                return # Hentikan fungsi parse

            item = BookItem()

            # Judul lengkap (ada di attribute 'title', bukan teks yang terpotong)
            item["judul"] = artikel.css("h3 a::attr(title)").get("").strip()

            # Harga termasuk simbol mata uang (£)
            item["harga"] = artikel.css("p.price_color::text").get("").strip()

            # Rating: diambil dari class CSS seperti "star-rating Three"
            rating_class = artikel.css("p.star-rating::attr(class)").get("")
            rating_kata = rating_class.replace("star-rating", "").strip()
            item["rating"] = self.RATING_MAP.get(rating_kata, 0)

            # Ketersediaan stok (True/False)
            teks_stok = " ".join(
                t.strip()
                for t in artikel.css("p.availability::text").getall()
                if t.strip()
            )
            item["tersedia"] = "In stock" in teks_stok

            # Kategori: tidak tersedia di halaman listing → diisi "Umum"
            # (untuk kategori spesifik, perlu crawl per-kategori)
            item["kategori"] = "Semua Kategori"

            # URL halaman detail buku
            rel_url = artikel.css("h3 a::attr(href)").get("")
            item["url"] = response.urljoin(rel_url)

            yield item

        # ---- Pagination: ikuti tombol "next" ----
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            next_url = response.urljoin(next_page)
            self.logger.debug(f"[BOOKS] → Halaman berikutnya: {next_url}")
            yield response.follow(next_url, callback=self.parse)
