# Define your item pipelines here
#
# Tugas 3 Web Mining - Pipeline untuk memproses dan menyimpan hasil crawling
# ==========================================================================

import csv
import json
import os
from datetime import datetime
from itemadapter import ItemAdapter
from tugas.items import BookItem, ArticleItem


# ------------------------------------------------------------------
# 1. Pipeline: Membersihkan Data
# ------------------------------------------------------------------
class BersihkanDataPipeline:
    """
    Membersihkan whitespace dan nilai kosong dari setiap field item.
    Dijalankan pertama sebelum pipeline lainnya.
    """

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Bersihkan string fields — hanya jika field ada dan bertipe string
        string_fields = ["judul", "harga", "kategori", "url", "ringkasan"]
        for field in string_fields:
            nilai = adapter.get(field)
            if nilai and isinstance(nilai, str):
                adapter[field] = nilai.strip()

        # Pastikan list fields (ArticleItem) benar-benar bertipe list
        list_fields = ["link_terkait"]
        for field in list_fields:
            nilai = adapter.get(field)
            if nilai is not None and isinstance(nilai, str):
                adapter[field] = [nilai]

        return item


# ------------------------------------------------------------------
# 2. Pipeline: Validasi Data
# ------------------------------------------------------------------
class ValidasiDataPipeline:
    """
    Memastikan field wajib ada dan tidak kosong.
    Item yang tidak valid akan di-drop (dibuang).
    """

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Validasi BookItem
        if isinstance(item, BookItem):
            if not adapter.get("judul") or not adapter.get("harga"):
                spider.logger.warning(
                    f"[VALIDASI] BookItem dibuang - field wajib kosong: {dict(item)}"
                )
                from scrapy.exceptions import DropItem
                raise DropItem(f"BookItem tidak lengkap: {item}")

        # Validasi ArticleItem
        if isinstance(item, ArticleItem):
            if not adapter.get("judul") or not adapter.get("url"):
                spider.logger.warning(
                    f"[VALIDASI] ArticleItem dibuang - field wajib kosong: {dict(item)}"
                )
                from scrapy.exceptions import DropItem
                raise DropItem(f"ArticleItem tidak lengkap: {item}")

        return item


# ------------------------------------------------------------------
# 3. Pipeline: Simpan ke CSV
# ------------------------------------------------------------------
class SimpanCSVPipeline:
    """
    Menyimpan hasil crawling ke file CSV yang terpisah per spider.
    File disimpan di folder output/ dengan timestamp.
    """

    def open_spider(self, spider):
        # Buat folder output jika belum ada
        os.makedirs("output", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/{spider.name}_{timestamp}.csv"
        self.file = open(filename, "w", newline="", encoding="utf-8")
        self.writer = None
        self.filename = filename
        spider.logger.info(f"[CSV] Output akan disimpan ke: {filename}")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        row = {}
        for field, value in adapter.items():
            if isinstance(value, list):
                row[field] = " | ".join(str(v) for v in value)
            elif isinstance(value, bool):
                row[field] = "Ya" if value else "Tidak"
            else:
                row[field] = value

        # Inisialisasi writer dengan header dari item pertama
        if self.writer is None:
            fieldnames = list(row.keys())
            self.writer = csv.DictWriter(
                self.file, fieldnames=fieldnames, extrasaction="ignore"
            )
            self.writer.writeheader()

        self.writer.writerow(row)
        return item

    def close_spider(self, spider):
        self.file.close()
        spider.logger.info(f"[CSV] Selesai. File tersimpan: {self.filename}")


# ------------------------------------------------------------------
# 4. Pipeline: Simpan ke JSON Lines
# ------------------------------------------------------------------
class SimpanJSONPipeline:
    """
    Menyimpan hasil crawling ke format JSON Lines (.jsonl).
    Setiap baris = satu item JSON.
    """

    def open_spider(self, spider):
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/{spider.name}_{timestamp}.jsonl"
        self.file = open(filename, "w", encoding="utf-8")
        self.filename = filename

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        line = json.dumps(dict(adapter), ensure_ascii=False)
        self.file.write(line + "\n")
        return item

    def close_spider(self, spider):
        self.file.close()
        spider.logger.info(f"[JSON] File tersimpan: {self.filename}")


# ------------------------------------------------------------------
# 5. Pipeline: Statistik Crawling
# ------------------------------------------------------------------
class StatistikPipeline:
    """
    Menampilkan statistik ringkasan di akhir crawling:
    jumlah item per tipe, spider yang digunakan, durasi, dll.
    """

    def open_spider(self, spider):
        self.mulai = datetime.now()
        self.hitung = {}
        spider.logger.info(
            f"\n{'='*50}\n"
            f"  MULAI CRAWLING: {spider.name}\n"
            f"  Waktu mulai   : {self.mulai.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*50}"
        )

    def process_item(self, item, spider):
        tipe = type(item).__name__
        self.hitung[tipe] = self.hitung.get(tipe, 0) + 1
        return item

    def close_spider(self, spider):
        selesai = datetime.now()
        durasi = selesai - self.mulai
        total = sum(self.hitung.values())

        ringkasan = "\n" + "=" * 50
        ringkasan += f"\n  SELESAI CRAWLING: {spider.name}"
        ringkasan += f"\n  Waktu selesai   : {selesai.strftime('%Y-%m-%d %H:%M:%S')}"
        ringkasan += f"\n  Durasi          : {durasi}"
        ringkasan += f"\n  Total item      : {total}"
        for tipe, jumlah in self.hitung.items():
            ringkasan += f"\n    - {tipe}: {jumlah} item"
        ringkasan += "\n" + "=" * 50

        spider.logger.info(ringkasan)
