import sys
import sqlite3
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QMouseEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, \
    QMessageBox, QComboBox, QProgressDialog
from datetime import datetime
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis
from openpyxl import Workbook
from aswwds import Job, Watcher


class CustomChartView(QChartView):

    def __init__(self, chart, parent=None):
        super().__init__(chart, parent)
        self.setMouseTracking(True)
        self.tooltipLabel = QLabel(self)
        self.tooltipLabel.setStyleSheet("background-color: white; border: 1px solid black; padding: 2px;")
        self.tooltipLabel.hide()

    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        point = event.pos()
        chartItem = self.chart().itemAt(self.mapToScene(point))
        if chartItem:
            for series in self.chart().series():
                if isinstance(series, QBarSeries):
                    for barSet in series.barSets():
                        index = series.barSets().index(barSet)
                        categoryIndex = series.categoryAxis().categories().index(chartItem.series().categories()[index])
                        if chartItem.series() == series and chartItem.barset() == barSet:
                            value = barSet.at(categoryIndex)
                            category = series.categoryAxis().categories()[categoryIndex]
                            self.tooltipLabel.setText(f"{category}: {value} adet")
                            self.tooltipLabel.move(event.pos())
                            self.tooltipLabel.show()
                            return
        self.tooltipLabel.hide()



class StokTakipUygulamasi(QWidget):
    def __init__(self):
        super().__init__()
        #self.init_db()
        self.db_ops = Job()
        self.db_ops.start()
        self.init_ui()

    def init_ui(self):
        self.v_box = QVBoxLayout()
        self.setWindowTitle('Stok Takip Uygulaması')

        # Ürün ekleme bölümü
        self.urun_adi_giris_ekle = QLineEdit()
        self.urun_adi_giris_ekle.setPlaceholderText('Ürün adını girin')
        self.miktar_giris_ekle = QLineEdit()
        self.miktar_giris_ekle.setPlaceholderText('Miktarı girin')
        self.alis_tarihi_giris_ekle = QLineEdit()
        self.alis_tarihi_giris_ekle.setPlaceholderText('GG-AA-YYYY')
        self.alis_tarihi_giris_ekle.textChanged.connect(self.format_tarih)
        self.alis_fiyati_giris_ekle = QLineEdit()
        self.alis_fiyati_giris_ekle.setPlaceholderText('Alış fiyatını girin')
        self.kimden_alindi_giris = QLineEdit()
        self.kimden_alindi_giris.setPlaceholderText('Kimden alındığını girin')
        ekleme_butonu = QPushButton('Ürün Ekle', self)
        ekleme_butonu.clicked.connect(self.urun_ekle)

        h_box_ekle = QHBoxLayout()
        h_box_ekle.addWidget(QLabel('Ürün Adı:'))
        h_box_ekle.addWidget(self.urun_adi_giris_ekle)
        h_box_ekle.addWidget(QLabel('Miktar:'))
        h_box_ekle.addWidget(self.miktar_giris_ekle)
        h_box_ekle.addWidget(QLabel('Alış Tarihi:'))
        h_box_ekle.addWidget(self.alis_tarihi_giris_ekle)
        h_box_ekle.addWidget(QLabel('Alış Fiyatı:'))
        h_box_ekle.addWidget(self.alis_fiyati_giris_ekle)
        h_box_ekle.addWidget(QLabel('Kimden Alındı:'))
        h_box_ekle.addWidget(self.kimden_alindi_giris)
        h_box_ekle.addWidget(ekleme_butonu)

        # Ürün silme bölümü için QComboBox kurulumu
        self.urun_adi_combo = QComboBox()
        self.miktar_giris_sil = QLineEdit()
        self.miktar_giris_sil.setPlaceholderText('Miktarı girin')
        self.satis_tarihi_giris_sil = QLineEdit()
        self.satis_tarihi_giris_sil.setPlaceholderText('GG-AA-YYYY')
        self.satis_tarihi_giris_sil.textChanged.connect(self.format_tarih)
        self.satis_fiyati_giris_sil = QLineEdit()
        self.satis_fiyati_giris_sil.setPlaceholderText('Satış fiyatını girin')
        self.kime_satildi_giris = QLineEdit()
        self.kime_satildi_giris.setPlaceholderText('Kime satıldığını girin')
        silme_butonu = QPushButton('Ürün Sat', self)
        silme_butonu.clicked.connect(self.urun_sil)

        h_box_sil = QHBoxLayout()
        h_box_sil.addWidget(QLabel('Ürün Adı:'))
        h_box_sil.addWidget(self.urun_adi_combo)
        h_box_sil.addWidget(QLabel('Miktar:'))
        h_box_sil.addWidget(self.miktar_giris_sil)
        h_box_sil.addWidget(QLabel('Satış Tarihi:'))
        h_box_sil.addWidget(self.satis_tarihi_giris_sil)
        h_box_sil.addWidget(QLabel('Satış Fiyatı:'))
        h_box_sil.addWidget(self.satis_fiyati_giris_sil)
        h_box_sil.addWidget(QLabel('Kime Satıldı:'))
        h_box_sil.addWidget(self.kime_satildi_giris)
        h_box_sil.addWidget(silme_butonu)

        # Arama çubuğu
        self.arama_cubugu = QLineEdit()
        self.arama_cubugu.setPlaceholderText('Stoklarda ara...')
        self.arama_cubugu.textChanged.connect(self.stoklari_ara)

        self.islem_gecmisi_arama_cubugu = QLineEdit()
        self.islem_gecmisi_arama_cubugu.setPlaceholderText('İşlem geçmişinde ara...')
        self.islem_gecmisi_arama_cubugu.textChanged.connect(self.islem_gecmisini_ara)

        # Stok listesi ve işlem bilgisi bölümü
        self.stok_listesi = QTextEdit()
        self.stok_listesi.setReadOnly(True)
        self.islem_bilgisi_etiketi = QLabel('')

        self.v_box.addLayout(h_box_ekle)
        self.v_box.addLayout(h_box_sil)
        self.v_box.addWidget(QLabel('Arama:'))
        self.v_box.addWidget(self.arama_cubugu)
        self.v_box.addWidget(QLabel('Stok Listesi:'))
        self.v_box.addWidget(self.stok_listesi)
        self.v_box.addWidget(self.islem_bilgisi_etiketi)

        self.v_box.addWidget(QLabel('İşlem Geçmişi Arama:'))
        self.v_box.addWidget(self.islem_gecmisi_arama_cubugu)

        self.grafikleri_guncelle()

        self.setLayout(self.v_box)
        self.stoklari_goster()

        excel_disa_aktar_butonu = QPushButton('Verileri Excel Olarak Dışa Aktar', self)
        excel_disa_aktar_butonu.clicked.connect(self.verileri_excel_disa_aktar)
        self.v_box.addWidget(excel_disa_aktar_butonu)

        self.islem_gecmisi = QTextEdit()
        self.islem_gecmisi.setReadOnly(True)
        self.v_box.addWidget(QLabel('İşlem Geçmişi:'))
        self.v_box.addWidget(self.islem_gecmisi)

        self.islem_gecmisini_goster()

        self.urunleri_yukle()

    def satislari_goster(self):
        self.satis_listesi.clear()
        self.db_ops.c.execute('SELECT urun_adi, SUM(miktar) FROM islem_gecmisi WHERE islem_tipi="Satış" GROUP BY urun_adi')
        for urun_adi, toplam_miktar in self.db_ops.c.fetchall():
            self.satis_listesi.append(f"{urun_adi}: {toplam_miktar} adet\n")

    def format_tarih(self, text):
        sender = self.sender()
        cursor_position = sender.cursorPosition()

        # GG-AA-YYYY formatına göre ayarla
        if len(text) == 2 and cursor_position == 2:
            sender.setText(text + '-')
            sender.setCursorPosition(cursor_position + 1)
        elif len(text) == 5 and cursor_position == 5:
            sender.setText(text + '-')
            sender.setCursorPosition(cursor_position + 1)
        elif len(text) > 10:
            # Yıl kısmı en fazla 4 karakter olmalı
            sender.setText(text[:10])
            sender.setCursorPosition(10)

    def islem_gecmisini_ara(self):
        arama_terimi = self.islem_gecmisi_arama_cubugu.text().lower()
        self.islem_gecmisi.clear()

        self.db_ops.c.execute('SELECT * FROM islem_gecmisi ORDER BY id DESC')
        for islem in self.db_ops.c.fetchall():
            if any(arama_terimi in str(deger).lower() for deger in islem):
                self.islem_gecmisi.append(
                    f"{islem[1]}: Ürün Adı: {islem[2]}, Miktar: {islem[3]}, Tarih: {islem[4]}, "
                    f"Fiyat: {islem[5]:.2f} TL, Kişi: {islem[6]}\n")

    def urun_ekle(self):
        urun_adi = self.urun_adi_giris_ekle.text().strip()
        miktar = self.miktar_giris_ekle.text().strip()
        alis_tarihi = self.alis_tarihi_giris_ekle.text().strip()
        alis_fiyati = self.alis_fiyati_giris_ekle.text().strip()
        kimden_alindi = self.kimden_alindi_giris.text().strip()

        if not urun_adi or not miktar.isdigit() or not alis_tarihi or not alis_fiyati.replace('.', '', 1).isdigit():
            QMessageBox.warning(self, 'Hata', 'Lütfen tüm alanları doğru şekilde doldurun.')
            return

        miktar = int(miktar)
        alis_fiyati = float(alis_fiyati)

        try:
            datetime.strptime(alis_tarihi, "%d-%m-%Y")
        except ValueError:
            QMessageBox.warning(self, 'Hata', 'Geçersiz tarih formatı, lütfen GG-AA-YYYY formatını kullanın.')
            return

        # Veritabanında aynı ürün adıyla kayıtlı ürün var mı kontrol et
        self.db_ops.c.execute('SELECT miktar FROM stoklar WHERE urun_adi = ?', (urun_adi,))
        result = self.db_ops.c.fetchone()

        if result:
            # Ürün varsa, mevcut miktarı güncelle
            toplam_miktar = result[0] + miktar
            self.db_ops.c.execute(
                'UPDATE stoklar SET miktar = ?, alis_tarihi = ?, alis_fiyati = ?, kimden_alindi = ? WHERE urun_adi = ?',
                (toplam_miktar, alis_tarihi, alis_fiyati, kimden_alindi, urun_adi))
        else:
            # Ürün yoksa yeni bir kayıt ekle
            self.db_ops.c.execute(
                'INSERT INTO stoklar (urun_adi, miktar, alis_tarihi, alis_fiyati, kimden_alindi) VALUES (?, ?, ?, ?, ?)',
                (urun_adi, miktar, alis_tarihi, alis_fiyati, kimden_alindi))

        self.db_ops.c.execute(
            'INSERT INTO islem_gecmisi (islem_tipi, urun_adi, miktar, tarih, fiyat, kisi) VALUES (?, ?, ?, ?, ?, ?)',
            ('Alış', urun_adi, miktar, alis_tarihi, alis_fiyati, kimden_alindi)
        )

        self.db_ops.conn.commit()

        self.urun_adi_giris_ekle.clear()
        self.miktar_giris_ekle.clear()
        self.alis_tarihi_giris_ekle.clear()
        self.alis_fiyati_giris_ekle.clear()
        self.kimden_alindi_giris.clear()
        QMessageBox.information(self, 'Başarılı', 'Ürün başarıyla eklendi.')

        self.stoklari_goster()
        self.islem_gecmisini_goster()
        self.urunleri_yukle()
        self.satislari_goster()
        self.grafikleri_guncelle()

    def urun_sil(self):
        urun_adi = self.urun_adi_combo.currentText()
        miktar = self.miktar_giris_sil.text().strip()
        satis_tarihi = self.satis_tarihi_giris_sil.text().strip()
        satis_fiyati = self.satis_fiyati_giris_sil.text().strip()
        kime_satildi = self.kime_satildi_giris.text().strip()

        if urun_adi == 'Ürün Seç' or not miktar.isdigit() or not satis_tarihi or not satis_fiyati.replace('.', '',
                                                                                                          1).isdigit():
            QMessageBox.warning(self, 'Hata', 'Lütfen tüm alanları doğru şekilde doldurun.')
            return

        miktar = int(miktar)
        satis_fiyati = float(satis_fiyati)

        try:
            datetime.strptime(satis_tarihi, "%d-%m-%Y")
        except ValueError:
            QMessageBox.warning(self, 'Hata', 'Geçersiz tarih formatı, lütfen GG-AA-YYYY formatını kullanın.')
            return

        self.db_ops.c.execute('SELECT miktar FROM stoklar WHERE urun_adi = ?', (urun_adi,))
        result = self.db_ops.c.fetchone()

        if result and result[0] >= miktar:
            yeni_miktar = result[0] - miktar
            self.db_ops.c.execute(
                'UPDATE stoklar SET miktar = ?, satis_tarihi = ?, satis_fiyati = ?, kime_satildi = ? WHERE urun_adi = ?',
                (yeni_miktar, satis_tarihi, satis_fiyati, kime_satildi, urun_adi)
            )
            self.db_ops.c.execute(
                'INSERT INTO islem_gecmisi (islem_tipi, urun_adi, miktar, tarih, fiyat, kisi) VALUES (?, ?, ?, ?, ?, ?)',
                ('Satış', urun_adi, miktar, satis_tarihi, satis_fiyati, kime_satildi)
            )
            self.db_ops.conn.commit()
            QMessageBox.information(self, 'Başarılı', f'{miktar} adet {urun_adi} başarıyla satıldı.')
        else:
            QMessageBox.warning(self, 'Hata', f'Stokta yeterli {urun_adi} bulunmamakta veya ürün adı yanlış.')

        self.urun_adi_combo.setCurrentIndex(0)
        self.miktar_giris_sil.clear()
        self.satis_tarihi_giris_sil.clear()
        self.satis_fiyati_giris_sil.clear()
        self.kime_satildi_giris.clear()

        self.stoklari_goster()
        self.islem_gecmisini_goster()
        self.urunleri_yukle()
        self.satislari_goster()
        self.grafikleri_guncelle()

    def urunleri_yukle(self):
        self.db_ops.c.execute('SELECT DISTINCT urun_adi FROM stoklar WHERE miktar >= 1 ORDER BY urun_adi ASC')
        urunler = self.db_ops.c.fetchall()
        self.urun_adi_combo.clear()
        self.urun_adi_combo.addItem('Ürün Seç')
        self.urun_adi_combo.model().item(0).setEnabled(False)

        for urun in urunler:
            self.urun_adi_combo.addItem(urun[0])

        self.urun_adi_combo.setCurrentIndex(0)

    def stoklari_goster(self):
        self.stok_listesi.clear()
        self.db_ops.c.execute('SELECT urun_adi, SUM(miktar) FROM stoklar GROUP BY urun_adi')
        for urun_adi, toplam_miktar in self.db_ops.c.fetchall():
            self.stok_listesi.append(f"{urun_adi}: {toplam_miktar} adet\n")

    def stok_hareketlerini_goster(self):
        alis_seti = QBarSet("Alış")
        satis_seti = QBarSet("Satış")
        mevcut_stok_seti = QBarSet("Mevcut Stok")

        # Mevcut stok miktarlarını tutacak sözlük
        mevcut_stoklar = {}

        self.db_ops.c.execute('SELECT urun_adi, SUM(miktar) FROM stoklar GROUP BY urun_adi')
        for urun_adi, miktar in self.db_ops.c.fetchall():
            mevcut_stoklar[urun_adi] = miktar

        # Satılan miktarları tutacak sözlük
        satis_miktarlari = {}

        # Tüm satış işlemlerini al (urun_adi ve sattığınız toplam miktar)
        self.db_ops.c.execute('SELECT urun_adi, SUM(miktar) FROM islem_gecmisi WHERE islem_tipi="Satış" GROUP BY urun_adi')
        for urun_adi, miktar in self.db_ops.c.fetchall():
            satis_miktarlari[urun_adi] = miktar

        kategoriler = sorted(set(mevcut_stoklar.keys()).union(satis_miktarlari.keys()))

        for kategori in kategoriler:
            alis_seti.append(mevcut_stoklar.get(kategori, 0))  # Mevcut alış miktarı (stokta kalan)
            satis_seti.append(satis_miktarlari.get(kategori, 0))  # Satış miktarı
            mevcut_stok_seti.append(mevcut_stoklar.get(kategori, 0))  # Mevcut stok miktarı (satış sonrası kalan)

        series = QBarSeries()
        series.append(mevcut_stok_seti)
        series.append(satis_seti)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Stok Hareketleri")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axisX = QBarCategoryAxis()
        axisX.append(kategoriler)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QValueAxis()
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        return chart_view

    def grafikleri_guncelle(self):
        # Mevcut chart widget'ını kaldırın
        if hasattr(self, 'chart_widget'):
            self.v_box.removeWidget(self.chart_widget)
            self.chart_widget.deleteLater()

        # Yeni grafik oluşturun ve widget'a ekleyin
        chart_view = self.stok_hareketlerini_goster()
        self.chart_widget = chart_view
        self.v_box.addWidget(self.chart_widget)

    def islem_gecmisini_goster(self):
        self.islem_gecmisi.clear()
        self.db_ops.c.execute('SELECT * FROM islem_gecmisi ORDER BY id DESC')
        for islem in self.db_ops.c.fetchall():
            self.islem_gecmisi.append(
                f"{islem[1]}: Ürün Adı: {islem[2]}, Miktar: {islem[3]}, Tarih: {islem[4]}, "
                f"Fiyat: {islem[5]:.2f} TL, Kişi: {islem[6]}\n")

    def stoklari_ara(self):
        arama_terimi = self.arama_cubugu.text().lower()
        self.stok_listesi.clear()

        self.db_ops.c.execute('SELECT urun_adi, SUM(miktar) FROM stoklar WHERE lower(urun_adi) LIKE ? GROUP BY urun_adi',
                       ('%' + arama_terimi + '%',))
        for urun_adi, toplam_miktar in self.db_ops.c.fetchall():
            self.stok_listesi.append(f"{urun_adi}: {toplam_miktar} adet\n")

    def verileri_excel_disa_aktar(self):
        progress_dialog = QProgressDialog("Veriler dışa aktarılıyor...", "İptal", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()

        wb = Workbook()

        # Stok listesi sayfası
        ws_stoklar = wb.active
        ws_stoklar.title = "Stoklar"
        ws_stoklar.append(['Ürün Adı', 'Miktar'])
        self.db_ops.c.execute('SELECT urun_adi, SUM(miktar) FROM stoklar GROUP BY urun_adi')
        for row in self.db_ops.c.fetchall():
            ws_stoklar.append(row)

        # İşlem geçmişi sayfası
        ws_islem_gecmisi = wb.create_sheet(title="İşlem Geçmişi")
        ws_islem_gecmisi.append(['ID', 'İşlem Tipi', 'Ürün Adı', 'Miktar', 'Tarih', 'Fiyat', 'Kişi'])
        self.db_ops.c.execute('SELECT * FROM islem_gecmisi')
        for row in self.db_ops.c.fetchall():
            ws_islem_gecmisi.append(row)

        # Dosyayı kaydet
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'C:/Users/kasim/Desktop/veriler_{timestamp}.xlsx'
        wb.save(filename)
        progress_dialog.setValue(100)
        QMessageBox.information(self, 'Başarılı', f'Veriler başarıyla {filename} dosyasına dışa aktarıldı.')

    def closeEvent(self, event):
        self.conn.close()

def main():
    app = QApplication(sys.argv)
    ex = StokTakipUygulamasi()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

