# Define here the models for your scraped items
#
# Tugas 3 Web Mining - Percobaan Crawling dengan Scrapy
# ======================================================
# Dua website yang di-crawl:
#   1. Website KECIL : books.toscrape.com
#   2. Website BESAR : en.wikipedia.org (kategori Technology)

import scrapy

# ============================================================
# ITEM UNTUK WEBSITE KECIL: books.toscrape.com
# ============================================================
class BookItem(scrapy.Item):
    """
    Menyimpan data buku dari books.toscrape.com.
    Website ini punya ~1000 buku dalam 50 kategori — cocok sebagai
    contoh website kecil/sedang yang terstruktur rapi.
    """
    judul        = scrapy.Field()  # Judul buku
    harga        = scrapy.Field()  # Harga (string, contoh: £51.77)
    rating       = scrapy.Field()  # Rating bintang: One/Two/Three/Four/Five
    tersedia     = scrapy.Field()  # Boolean: apakah stok tersedia
    kategori     = scrapy.Field()  # Nama kategori / genre buku
    url          = scrapy.Field()  # URL halaman detail buku


# ============================================================
# ITEM UNTUK WEBSITE BESAR: en.wikipedia.org
# ============================================================
class ArticleItem(scrapy.Item):
    """
    Menyimpan data artikel dari Wikipedia bahasa Inggris.
    Wikipedia adalah contoh website sangat besar dengan jutaan halaman
    dan internal link yang saling terhubung (graph crawling).
    """
    judul        = scrapy.Field()  # Judul artikel
    ringkasan    = scrapy.Field()  # Paragraf pertama (intro)
    kategori     = scrapy.Field()  # Daftar kategori artikel (list)
    link_terkait = scrapy.Field()  # Internal links ke artikel lain (list)
    url          = scrapy.Field()  # URL artikel ini
    kedalaman    = scrapy.Field()  # Seberapa dalam dari halaman awal (depth)
    jumlah_kata  = scrapy.Field()  # Estimasi jumlah kata dalam artikel


# ============================================================
# ITEM UNTUK SPIDER STRUKTUR WEBSITE: books.toscrape.com
# ============================================================
class BookStructureItem(scrapy.Item):
    """
    Menyimpan data STRUKTUR website books.toscrape.com.
    Fokus pada navigasi, hierarki kategori, dan metadata halaman —
    bukan konten buku itu sendiri.
    """
    tipe           = scrapy.Field()  # Tipe node: 'kategori', 'listing', 'detail'
    nama           = scrapy.Field()  # Nama kategori / label halaman
    url            = scrapy.Field()  # URL halaman ini
    url_induk      = scrapy.Field()  # URL halaman induk (parent)
    kedalaman      = scrapy.Field()  # Kedalaman dari root (0 = home)
    jumlah_buku    = scrapy.Field()  # Jumlah buku di kategori (jika ada)
    jumlah_halaman = scrapy.Field()  # Jumlah halaman pagination (jika ada)
    nomor_halaman  = scrapy.Field()  # Nomor halaman saat ini (untuk listing)
    tag_navigasi   = scrapy.Field()  # Daftar tag/elemen navigasi yang ditemukan
    link_anak      = scrapy.Field()  # Daftar URL anak langsung (child links)
    meta_html      = scrapy.Field()  # Metadata HTML: title tag, meta description


# ============================================================
# ITEM UNTUK SPIDER STRUKTUR WEBSITE: en.wikipedia.org
# ============================================================
class WikiStructureItem(scrapy.Item):
    """
    Menyimpan data STRUKTUR halaman Wikipedia bahasa Inggris.
    Fokus pada topologi link, elemen navigasi, dan metadata halaman —
    bukan konten/ringkasan artikel.
    """
    # --- Identitas node ---
    judul          = scrapy.Field()  # Judul artikel (heading utama)
    url            = scrapy.Field()  # URL artikel ini
    url_induk      = scrapy.Field()  # URL artikel yang merujuk ke sini (referrer)
    kedalaman      = scrapy.Field()  # Kedalaman BFS dari seed (0 = seed)

    # --- Topologi link ---
    jumlah_link_internal = scrapy.Field()  # Total link /wiki/ dalam artikel
    jumlah_link_eksternal= scrapy.Field()  # Total link keluar (http/https non-wiki)
    link_keluar    = scrapy.Field()  # List URL internal yang diikuti spider
    link_masuk_dari= scrapy.Field()  # URL referrer (siapa yang mengarah ke sini)

    # --- Struktur halaman ---
    jumlah_section = scrapy.Field()  # Jumlah bagian/section (h2) dalam artikel
    judul_section  = scrapy.Field()  # List judul h2 (struktur konten)
    ada_infobox    = scrapy.Field()  # Boolean: apakah ada infobox/tabel info
    ada_toc        = scrapy.Field()  # Boolean: apakah ada Table of Contents
    jumlah_gambar  = scrapy.Field()  # Jumlah gambar dalam artikel
    jumlah_referensi = scrapy.Field()  # Jumlah referensi/footnote

    # --- Metadata navigasi ---
    kategori       = scrapy.Field()  # List kategori Wikipedia artikel ini
    jumlah_kategori= scrapy.Field()  # Jumlah kategori
    portal         = scrapy.Field()  # List portal yang terkait artikel
    ada_disambiguasi = scrapy.Field()  # Boolean: apakah ini halaman disambiguasi

    # --- Metadata HTML ---
    meta_html      = scrapy.Field()  # dict: title tag, lang, canonical URL
