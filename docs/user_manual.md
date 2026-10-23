# Panduan Pengguna: Heart Disease Risk Advisor

Aplikasi ini membantu kamu memahami risiko penyakit jantung dan mencari jawaban pencegahan dalam bahasa Indonesia yang mudah dipahami.

> **Penting:** aplikasi ini hanya untuk **edukasi**. Hasilnya **bukan diagnosis** dan **bukan pengganti saran dokter**. Jangan memulai, mengubah, atau menghentikan pengobatan hanya berdasarkan hasil aplikasi ini.

> **Darurat?** Nyeri dada hebat, sesak napas berat, atau lemah separuh badan: segera ke IGD atau hubungi **119**. Jangan menunggu hasil aplikasi.

## 1. Membuka aplikasi

1. Buka alamat **https://heart-risk-advisor.streamlit.app** di browser HP atau komputer. Tidak perlu daftar atau login.
2. Kalau aplikasi lama tidak dikunjungi (sekitar 12 jam), server "tidur". Pengunjung pertama perlu menunggu sekitar **1 sampai 3 menit** sampai aplikasi siap. Setelah itu pengunjung berikutnya langsung masuk.
3. Pastikan panel kiri menampilkan tulisan **"Server terhubung"**.

## 2. Cek risiko

Isi formulir di panel kiri, lalu tekan tombol **Cek Risiko**.

### Data dasar (wajib)

| Isian | Petunjuk |
|---|---|
| Usia | Dalam tahun |
| Jenis kelamin | Laki-laki atau perempuan |
| Tekanan darah atas (sistolik) | Angka pertama hasil tensi, dalam mmHg |
| Kolesterol total | Dari hasil laboratorium, dalam mg/dl. Kalau hasilmu dalam mmol/l, aplikasi menampilkan petunjuk cara mengubahnya |
| Gula darah puasa di atas 120 mg/dl? | Pilih Tidak, Ya, atau Tidak tahu |
| Keluhan nyeri dada | Pilih yang paling sesuai |
| Nyeri dada saat olahraga atau aktivitas berat? | Tidak atau Ya |

### Data klinis (opsional)

Kalau kamu punya hasil pemeriksaan jantung (EKG, uji treadmill, dan sejenisnya), buka bagian **"Data klinis dari hasil pemeriksaan (opsional)"**, lalu centang **"Pakai data klinis yang saya isi di bawah"**.

Kalau tidak punya, **tidak masalah**. Biarkan kosong, dan aplikasi memakai nilai rata-rata. Konsekuensinya hasil menjadi **kurang akurat**, dan aplikasi akan memberi tahu kamu.

## 3. Membaca hasil

Hasil tampil di halaman utama berupa pengukur (gauge) berwarna dan persentase.

| Warna | Kategori | Artinya |
|---|---|---|
| Hijau (di bawah 30%) | Risiko rendah | Pola datamu mirip kelompok dengan risiko rendah. Tetap jaga gaya hidup sehat dan periksa kesehatan berkala |
| Kuning (30 sampai 60%) | Risiko sedang | Pola datamu mirip kelompok dengan risiko sedang. Sebaiknya konsultasikan dengan dokter dan perhatikan faktor risiko yang masih bisa diubah |
| Merah (di atas 60%) | Risiko tinggi | Pola datamu mirip kelompok dengan risiko tinggi. Segera konsultasikan dengan dokter untuk pemeriksaan lebih lanjut |

Yang perlu kamu pahami:
- Angka itu **perkiraan model**, bukan hasil diagnosis. Model dilatih dari data 303 pasien rumah sakit di Cleveland (data akhir 1980-an), sehingga belum tentu mewakili kondisi masyarakat Indonesia saat ini.
- Batas warna (30% dan 60%) adalah keputusan tim, **bukan standar kedokteran**.
- Hasil rendah **bukan jaminan** bebas penyakit jantung.
- Kalau muncul catatan "hasil kurang akurat karena sebagian data diperkirakan", artinya ada data yang tidak kamu isi.

## 4. Tanya pedoman WHO (chat)

Di bagian **Tanya Pedoman WHO** kamu bisa bertanya tentang pencegahan penyakit jantung dengan dua cara:
- **Mengetik** pertanyaan di kotak chat, lalu kirim. Contoh: "Berapa batas konsumsi garam per hari?"
- **Menekan pertanyaan siap-klik** di atas kotak chat. Pertanyaan ini menyesuaikan hasil cek risikomu. Contohnya, kalau tekanan darahmu 140 atau lebih, muncul pertanyaan tentang cara menurunkan tekanan darah tinggi.

Setiap jawaban:
- diambil dari **pedoman WHO tahun 2007** (bukan dari pengetahuan umum),
- ditulis dalam bahasa Indonesia sederhana,
- disertai **sumber** berupa nomor halaman pedoman. Klik daftar sumber untuk membuka dan menutupnya,
- diakhiri **disclaimer** "Ini bukan nasihat medis".

Jawaban biasanya muncul dalam 1 sampai 3 detik. Gunakan tombol hapus percakapan untuk memulai dari awal.

### Pertanyaan yang cocok
- Apa saja faktor risiko penyakit jantung yang bisa diubah?
- Bagaimana cara mencegah penyakit jantung?
- Berapa banyak aktivitas fisik yang disarankan?
- Bagaimana cara menurunkan tekanan darah tinggi?

### Yang tidak bisa dilakukan aplikasi
- Memberi **diagnosis** atau menentukan apakah kamu "pasti sakit".
- Meresepkan obat atau menentukan dosis. Pertanyaan semacam itu sebaiknya kamu tanyakan langsung ke dokter atau apoteker.
- Menjawab hal di luar pencegahan penyakit jantung. Kalau informasi tidak ada di pedoman, aplikasi menjawab "Maaf, informasi tidak ditemukan."

## 5. Pertanyaan yang sering muncul

**Kenapa hasilnya berbeda dari perkiraanku?**
Model hanya memakai 13 data, dan sebagian diisi dengan nilai rata-rata kalau kamu tidak punya hasil pemeriksaan jantung. Hasil bisa meleset, jadi jangan dijadikan patokan tunggal.

**Kenapa memilih "tidak ada nyeri dada" bisa menghasilkan risiko lebih tinggi?**
Model belajar dari pasien rumah sakit yang tetap dirujuk memeriksakan jantung meski tanpa keluhan. Ini keterbatasan data, bukan berarti tidak ada nyeri dada itu lebih berbahaya.

**Aplikasi tidak mau terbuka atau lama sekali.**
Tunggu sampai 3 menit lalu muat ulang halaman. Server gratis tidur setelah lama tidak dipakai dan butuh waktu untuk bangun.

**Chat tidak menjawab atau muncul pesan error.**
Periksa tulisan "Server terhubung" di panel kiri. Pastikan pertanyaanmu 3 sampai 500 karakter. Kalau masih gagal, coba beberapa saat lagi.

**Apa yang harus kulakukan setelah melihat hasil?**
Hasil sedang atau tinggi: temui dokter untuk pemeriksaan sebenarnya. Hasil rendah: tetap jaga pola makan, aktivitas fisik, dan pemeriksaan berkala. Gejala berat: langsung ke IGD atau hubungi 119.

---

*Sumber pengetahuan: WHO (2007), Prevention of cardiovascular disease: Guidelines for assessment and management of cardiovascular risk. Dataset: UCI Heart Disease (Cleveland).*
