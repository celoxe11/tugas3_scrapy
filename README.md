# Tugas 3 Web Mining — Percobaan Crawling dengan Scrapy

## 🎯 Deskripsi Proyek

Proyek ini berisi percobaan crawling menggunakan **Scrapy** terhadap **2 website**
dengan **2 pendekatan berbeda** — crawling **konten** dan crawling **struktur**:

| | Website Kecil | Website Besar |
|---|---|---|
| **URL** | books.toscrape.com | en.wikipedia.org |
| **Skala** | ~1.000 buku, 50 halaman | Jutaan artikel |
| **Spider Konten** | `books` | `wikipedia` |
| **Spider Struktur** | `books_structure` | `wiki_structure` |

---

## 📁 Struktur Proyek

```
tugas3_scrapy/
├── scrapy.cfg
├── output/                        # Hasil crawling (CSV, JSONL, log)
└── tugas/
    ├── items.py          # Definisi item: BookItem, ArticleItem,
    │                     #   BookStructureItem, WikiStructureItem
    ├── settings.py       # Konfigurasi Scrapy (rate limit, pipeline, dll.)
    ├── pipelines.py      # 5 pipeline: bersihkan, validasi, CSV, JSON, statistik
    ├── middlewares.py    # Middleware default Scrapy
    └── spiders/
        ├── books_spider.py              # 🔹 Konten website kecil (buku)
        ├── books_structure_spider.py    # 🔷 Struktur website kecil (kategori & nav)
        ├── wikipedia_spider.py          # 🔸 Konten website besar (artikel)
        └── wikipedia_structure_spider.py# 🔶 Struktur website besar (graph link)
```

---

## 🕷️ Daftar Spider

### 🔹 Spider 1 — `books` (Konten)

Mengambil data **konten** setiap buku: judul, harga, rating, stok, kategori, URL.

- **Strategi**: Pagination listing (page-1 → page-50)
- **Item**: `BookItem`

```bash
scrapy crawl books
scrapy crawl books -s CLOSESPIDER_ITEMCOUNT=50
scrapy crawl books -o output/books.csv
scrapy crawl books -o output/books.jsonl
```

---

### 🔷 Spider 2 — `books_structure` (Struktur)

Memetakan **struktur** website — hierarki kategori, navigasi, pagination,
dan metadata HTML. **Tidak mengambil konten buku sama sekali.**

- **Strategi**: Home → tiap kategori → semua halaman pagination
- **Item**: `BookStructureItem`
- **Field yang dikumpulkan**:
  - `tipe` — `home` / `kategori` / `listing`
  - `nama` — nama kategori atau halaman
  - `url` / `url_induk` — posisi dalam hierarki
  - `kedalaman` — jarak dari halaman utama
  - `jumlah_buku` — total buku per kategori
  - `jumlah_halaman` — total halaman pagination per kategori
  - `nomor_halaman` — nomor halaman listing saat ini
  - `tag_navigasi` — elemen nav yang ditemukan (breadcrumb, sidebar, pagination)
  - `link_anak` — daftar URL child langsung
  - `meta_html` — title tag, meta description, breadcrumb, jumlah artikel per halaman

```bash
scrapy crawl books_structure
scrapy crawl books_structure -o output/books_structure.jsonl
scrapy crawl books_structure -o output/books_structure.csv
```

---

### 🔸 Spider 3 — `wikipedia` (Konten)

Mengambil data **konten** artikel Wikipedia: judul, ringkasan, kategori,
link terkait, jumlah kata, kedalaman BFS.

- **Strategi**: BFS dari artikel seed, maks 5 link per halaman
- **Item**: `ArticleItem`

```bash
scrapy crawl wikipedia
scrapy crawl wikipedia -a seed=Machine_learning
scrapy crawl wikipedia -s CLOSESPIDER_ITEMCOUNT=100
scrapy crawl wikipedia -o output/wikipedia.csv
```

---

### 🔶 Spider 4 — `wiki_structure` (Struktur)

Memetakan **struktur graph** Wikipedia — topologi link antar artikel,
elemen navigasi, dan metadata halaman.
**Tidak mengambil isi/ringkasan artikel.**

- **Strategi**: BFS dari artikel seed, ikuti maks N link per halaman
- **Item**: `WikiStructureItem`
- **Field yang dikumpulkan**:

| Kelompok | Field | Keterangan |
|---|---|---|
| **Identitas** | `judul`, `url`, `url_induk`, `kedalaman` | Posisi node dalam graph |
| **Topologi Link** | `jumlah_link_internal`, `jumlah_link_eksternal` | Jumlah link masuk/keluar |
| | `link_keluar`, `link_masuk_dari` | Link yang diikuti & referrer |
| **Struktur Halaman** | `jumlah_section`, `judul_section` | Kerangka dokumen (h2) |
| | `ada_infobox`, `ada_toc` | Kehadiran elemen navigasi khas |
| | `jumlah_gambar`, `jumlah_referensi` | Kelengkapan konten |
| **Navigasi** | `kategori`, `jumlah_kategori`, `portal` | Taksonomi Wikipedia |
| | `ada_disambiguasi` | Apakah halaman disambiguasi |
| **Metadata HTML** | `meta_html` | title, lang, canonical, og:description |

```bash
# Default: seed=Web_scraping, 30 item, max 5 link/halaman
scrapy crawl wiki_structure

# Simpan ke file
scrapy crawl wiki_structure -o output/wiki_structure.jsonl
scrapy crawl wiki_structure -o output/wiki_structure.csv

# Ganti seed artikel
scrapy crawl wiki_structure -a seed=Data_mining

# Ganti jumlah link yang diikuti per halaman
scrapy crawl wiki_structure -a max_links=8

# Kombinasi parameter
scrapy crawl wiki_structure -a seed=Artificial_intelligence -a max_links=3 -s CLOSESPIDER_ITEMCOUNT=50
```

---

## 📊 Output

Hasil crawling disimpan di folder `output/`:

| File | Spider | Keterangan |
|---|---|---|
| `books_<ts>.csv` / `.jsonl` | `books` | Data konten buku |
| `books_structure.jsonl` | `books_structure` | Struktur & navigasi website buku |
| `wikipedia_<ts>.csv` / `.jsonl` | `wikipedia` | Data konten artikel Wikipedia |
| `wiki_structure.jsonl` | `wiki_structure` | Graph & struktur halaman Wikipedia |
| `*.log` | semua | Log crawling masing-masing spider |

---

## 🔧 Konfigurasi Penting (settings.py)

| Setting | Nilai | Penjelasan |
|---|---|---|
| `DOWNLOAD_DELAY` | 1 detik | Jeda antar request |
| `ROBOTSTXT_OBEY` | True | Patuhi robots.txt (default) |
| `AUTOTHROTTLE_ENABLED` | True | Auto-adaptasi kecepatan crawl |
| `RETRY_TIMES` | 3 | Retry otomatis jika request gagal |
| `CONCURRENT_REQUESTS_PER_DOMAIN` | 2 | Maks 2 request paralel per domain |

> ⚠️ **Catatan**: Spider `wikipedia` dan `wiki_structure` meng-override
> `ROBOTSTXT_OBEY = False` secara lokal di `custom_settings` karena
> Wikipedia memblokir bot lewat robots.txt, namun kontennya open-access
> dan crawling skala kecil untuk keperluan akademis diperbolehkan.

---

## 📦 Pipeline (urutan eksekusi)

1. **BersihkanDataPipeline** — Trim whitespace, normalisasi tipe data
2. **ValidasiDataPipeline** — Drop item yang tidak lengkap / invalid
3. **SimpanCSVPipeline** — Ekspor ke `.csv` dengan timestamp
4. **SimpanJSONPipeline** — Ekspor ke `.jsonl` dengan timestamp
5. **StatistikPipeline** — Cetak ringkasan statistik di akhir crawling
