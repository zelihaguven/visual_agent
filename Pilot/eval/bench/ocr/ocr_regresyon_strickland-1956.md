# OCR regresyon kontrolü: strickland-1956

2026-11-06 16:56. pilot/ocr.py (sayfa sınıfı → bayrak, sayfa başına dil, eski/yeni seçimi, süzgeç). Değerler verify'ın kanonik sayı biçiminde, sayfa başına çoklu küme. "Kaybolan" = eski katmanda olup son katmanda olmayan; doğru olup olmadığı sayfa görüntüsünden elle değerlendirilir.

| Ölçü | Değer |
|---|---|
| belge | strickland-1956 |
| sayfa | 164 |
| sure_sn | 0.0 |
| secim | {'yeni': 134, 'goruntu': 21, 'eski': 9} |
| eski_sayi | 1110 |
| son_sayi | 1247 |
| kaybolan_deger | 139 |
| kayipli_sayfa | 51 |
| eklenen_deger | 276 |
| degisim_sinifi | {'inceleme': 412, 'tasindi': 106, 'duzeltme': 24} |
| ocr_sure_sn | 444.0 |

| Sayfa | sınıf | dil | skor eski → yeni | seçim | eski / son sayı | kaybolan | eklenen |
|---|---|---|---|---|---|---|---|
| 1 | yok | eng | 0.00 → 1.00 | yeni | 0 / 0 | – | – |
| 2 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 3 | yok | eng | 1.00 → 1.00 | yeni | 0 / 0 | – | – |
| 4 | taranmis | eng | 1.00 → 1.00 | yeni | 0 / 0 | – | – |
| 5 | taranmis | eng | 0.95 → 0.96 | yeni | 0 / 0 | – | – |
| 6 | taranmis | eng | 1.00 → 1.00 | yeni | 9 / 8 | 515×1, 1151×1 | 736 |
| 7 | taranmis | eng | 0.99 → 0.99 | yeni | 0 / 0 | – | – |
| 8 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 9 | taranmis | eng | 0.99 → 1.00 | yeni | 40 / 0 | 1×1, 3×2, 4×1, 5×1, 6×2, 9×1, 14×2, 16×1, 17×1, 18×1, 20×1, 21×2, 25×2, 26×1, 28×1, 30×1, 31×2, 32×2, 33×1, 35×1, 37×2, 38×3, 39×2, 40×1, 41×2, 50×3 | – |
| 10 | taranmis | eng | 1.00 → 1.00 | yeni | 52 / 52 | 55×1, 59×1 | 95, 99 |
| 11 | taranmis | eng | 1.00 → 1.00 | yeni | 52 / 51 | 12×1, 3×1 | 123 |
| 12 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 13 | yok | eng | 1.00 → 1.00 | yeni | 0 / 0 | – | – |
| 14 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 15 | taranmis | eng | 0.99 → 1.00 | yeni | 1 / 1 | 1×1 | 4 |
| 16 | taranmis | eng | 1.00 → 1.00 | yeni | 3 / 6 | – | 2, 4, 4 |
| 17 | taranmis | eng | 1.00 → 1.00 | yeni | 1 / 1 | – | – |
| 18 | taranmis | eng | 0.99 → 0.99 | yeni | 6 / 7 | – | 6 |
| 19 | taranmis | eng | 1.00 → 1.00 | yeni | 1 / 0 | 5×1 | – |
| 20 | taranmis | eng | 1.00 → 1.00 | yeni | 13 / 15 | – | 2, 2 |
| 21 | yok | eng | 0.00 → 0.82 | goruntu | 0 / 0 | – | – |
| 22 | taranmis | eng | 0.98 → 0.99 | yeni | 2 / 1 | 3×1 | – |
| 23 | taranmis | eng | 1.00 → 1.00 | yeni | 7 / 8 | – | 4 |
| 24 | taranmis | eng | 0.99 → 1.00 | yeni | 29 / 28 | 3×1 | – |
| 25 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 26 | yok | eng | 0.00 → 1.00 | yeni | 0 / 1 | – | 12 |
| 27 | taranmis | eng | 0.98 → 0.99 | yeni | 14 / 15 | – | 14 |
| 28 | taranmis | eng | 1.00 → 1.00 | yeni | 19 / 14 | 2×1, 3×2, 5×2, 6×2, 7×2 | 2.2, 6.6, 7.7, 9.5 |
| 29 | taranmis | eng | 0.98 → 0.98 | yeni | 23 / 20 | 9×2, 11×1, 13×1, 14×1 | 2.9, 911 |
| 30 | taranmis | eng | 0.95 → 0.93 | eski | 35 / 35 | – | – |
| 31 | taranmis | eng | 0.90 → 0.94 | yeni | 27 / 28 | 1×3, 5×1, 8×1, 45×1 | 2, 4, 54, 7, 7, 7, 7 |
| 32 | taranmis | eng | 1.00 → 0.93 | eski | 4 / 4 | – | – |
| 33 | taranmis | eng | 0.99 → 0.99 | yeni | 11 / 13 | – | 2, 4 |
| 34 | taranmis | eng | 0.98 → 0.79 | eski | 11 / 11 | – | – |
| 35 | taranmis | eng | 0.98 → 0.97 | yeni | 16 / 16 | 3×1, 1×1 | 2, 6 |
| 36 | yok | eng | 0.00 → 0.70 | goruntu | 0 / 0 | – | – |
| 37 | yok | eng | 0.00 → 0.78 | goruntu | 0 / 0 | – | – |
| 38 | yok | eng | 0.00 → 0.67 | goruntu | 0 / 0 | – | – |
| 39 | taranmis | eng | 0.99 → 0.99 | yeni | 11 / 12 | – | 1 |
| 40 | taranmis | eng | 0.97 → 0.98 | yeni | 3 / 4 | – | 1 |
| 41 | taranmis | eng | 0.98 → 0.97 | yeni | 3 / 4 | – | 9 |
| 42 | taranmis | eng | 0.98 → 0.99 | yeni | 9 / 15 | – | 2, 28, 4, 4, 4, 6 |
| 43 | taranmis | eng | 0.99 → 0.99 | yeni | 1 / 2 | – | 4 |
| 44 | taranmis | eng | 0.99 → 0.98 | yeni | 4 / 6 | – | 4, 4 |
| 45 | taranmis | eng | 0.99 → 0.99 | yeni | 10 / 11 | 12×1, 1×1 | 4, 4, 7 |
| 46 | taranmis | eng | 0.93 → 0.94 | yeni | 8 / 14 | – | 1, 1, 114, 14, 2, 7 |
| 47 | taranmis | eng | 0.90 → 0.91 | yeni | 6 / 11 | – | 14, 17, 4, 7, 7 |
| 48 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 49 | taranmis | eng | 0.92 → 0.94 | yeni | 8 / 9 | 0×2 | 1, 14, 7 |
| 50 | taranmis | eng | 0.95 → 0.94 | yeni | 4 / 5 | – | 7 |
| 51 | taranmis | eng | 1.00 → 1.00 | yeni | 3 / 4 | – | 1 |
| 52 | taranmis | eng | 0.98 → 0.98 | yeni | 19 / 17 | 1×4, 18×1 | 0, 3, 4 |
| 53 | taranmis | eng | 1.00 → 1.00 | yeni | 2 / 2 | – | – |
| 54 | taranmis | eng | 0.98 → 0.98 | yeni | 3 / 3 | – | – |
| 55 | taranmis | eng | 0.98 → 0.99 | yeni | 16 / 18 | – | 1, 6 |
| 56 | taranmis | eng | 0.97 → 0.96 | yeni | 9 / 4 | 42×1, 3×1, 4×1, 5×1, 6×1 | – |
| 57 | taranmis | eng | 0.98 → 0.98 | yeni | 7 / 7 | – | – |
| 58 | taranmis | eng | 0.98 → 0.99 | yeni | 4 / 8 | – | 2, 21, 21, 3 |
| 59 | taranmis | eng | 0.98 → 0.97 | yeni | 5 / 13 | – | 1, 21, 21, 21, 4, 5, 6, 6 |
| 60 | taranmis | eng | 0.99 → 0.98 | yeni | 10 / 10 | – | – |
| 61 | yok | eng | 0.00 → 0.88 | yeni | 0 / 8 | – | 1, 10, 10, 11, 2, 21, 47, 8 |
| 62 | taranmis | eng | 0.99 → 0.99 | yeni | 12 / 16 | 12.13×1, 14.15×1 | 1, 12, 13, 2, 2, 39 |
| 63 | taranmis | eng | 0.99 → 0.98 | yeni | 9 / 9 | 7×2 | 17, 4 |
| 64 | taranmis | eng | 0.99 → 0.99 | yeni | 11 / 13 | – | 111, 22 |
| 65 | taranmis | eng | 0.98 → 0.99 | yeni | 1 / 1 | – | – |
| 66 | yok | eng | 0.00 → 1.00 | yeni | 0 / 1 | – | 52 |
| 67 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 68 | taranmis | eng | 1.00 → 1.00 | yeni | 1 / 1 | – | – |
| 69 | taranmis | eng | 1.00 → 1.00 | yeni | 5 / 5 | 55×1 | 95 |
| 70 | taranmis | eng | 1.00 → 1.00 | yeni | 5 / 5 | 56×1 | 36 |
| 71 | taranmis | eng | 0.99 → 0.99 | yeni | 14 / 14 | 5×1 | 9 |
| 72 | yok | eng | 0.00 → 0.67 | goruntu | 0 / 0 | – | – |
| 73 | taranmis | eng | 0.99 → 0.99 | yeni | 7 / 9 | – | 111, 6 |
| 74 | taranmis | eng | 1.00 → 1.00 | yeni | 4 / 4 | – | – |
| 75 | taranmis | eng | 1.00 → 1.00 | yeni | 1 / 1 | – | – |
| 76 | taranmis | eng | 0.97 → 0.98 | yeni | 4 / 8 | – | 2, 27, 6, 8 |
| 77 | taranmis | eng | 1.00 → 0.99 | yeni | 7 / 9 | – | 18, 4 |
| 78 | taranmis | eng | 0.99 → 0.97 | eski | 4 / 4 | – | – |
| 79 | taranmis | eng | 1.00 → 1.00 | yeni | 10 / 15 | 1.2×1, 3.4×1, 5.6×1 | 1, 2, 3, 3, 4, 5, 6, 6 |
| 80 | taranmis | eng | 0.97 → 0.96 | yeni | 6 / 8 | – | 3, 4 |
| 81 | taranmis | eng | 0.99 → 0.99 | yeni | 13 / 13 | 67×1, 6×1 | 4, 4 |
| 82 | taranmis | eng | 1.00 → 0.96 | eski | 1 / 1 | – | – |
| 83 | taranmis | eng | 1.00 → 1.00 | yeni | 12 / 13 | – | 33 |
| 84 | taranmis | eng | 1.00 → 1.00 | yeni | 6 / 7 | – | 34 |
| 85 | taranmis | eng | 0.99 → 0.99 | yeni | 2 / 3 | – | 4 |
| 86 | taranmis | eng | 0.99 → 0.99 | yeni | 15 / 26 | – | 0, 0, 0, 0, 0, 0, 0, 0, 0, 36, 6 |
| 87 | taranmis | eng | 0.99 → 1.00 | yeni | 6 / 7 | – | 6 |
| 88 | taranmis | eng | 0.98 → 0.98 | yeni | 4 / 7 | – | 1, 4, 4 |
| 89 | taranmis | eng | 0.99 → 1.00 | yeni | 2 / 5 | – | 1, 1, 1 |
| 90 | taranmis | eng | 0.99 → 0.99 | yeni | 2 / 2 | – | – |
| 91 | taranmis | eng | 0.99 → 0.93 | eski | 4 / 4 | – | – |
| 92 | taranmis | eng | 0.99 → 0.99 | yeni | 9 / 10 | 3×1 | 4, 4 |
| 93 | taranmis | eng | 0.98 → 0.99 | yeni | 3 / 5 | 3×1 | 4, 6, 6 |
| 94 | taranmis | eng | 1.00 → 0.99 | yeni | 4 / 6 | 46×1 | 42, 6, 7 |
| 95 | taranmis | eng | 1.00 → 0.97 | eski | 1 / 1 | – | – |
| 96 | taranmis | eng | 0.99 → 0.99 | yeni | 5 / 5 | – | – |
| 97 | taranmis | eng | 0.99 → 0.97 | yeni | 2 / 3 | – | 45 |
| 98 | taranmis | eng | 0.99 → 0.98 | yeni | 7 / 7 | 84×1 | 8 |
| 99 | taranmis | eng | 0.96 → 0.96 | yeni | 1 / 6 | – | 1, 233, 47, 47, 85 |
| 100 | taranmis | eng | 0.99 → 1.00 | yeni | 10 / 11 | 1×1 | 14, 6 |
| 101 | taranmis | eng | 0.98 → 0.98 | yeni | 4 / 6 | – | 4, 48 |
| 102 | taranmis | eng | 0.99 → 0.99 | yeni | 10 / 14 | 50×1 | 2, 4, 4, 4, 49 |
| 103 | taranmis | eng | 1.00 → 1.00 | yeni | 1 / 2 | 51×1 | 52, 89 |
| 104 | yok | eng | 0.00 → 0.80 | goruntu | 0 / 0 | – | – |
| 105 | taranmis | eng | 1.00 → 1.00 | yeni | 5 / 5 | 53×1 | 33 |
| 106 | taranmis | eng | 0.99 → 0.99 | yeni | 4 / 5 | – | 4 |
| 107 | yok | eng | 0.00 → 0.80 | goruntu | 0 / 0 | – | – |
| 108 | taranmis | eng | 0.99 → 0.99 | yeni | 17 / 19 | 1×1 | 3, 4, 5 |
| 109 | taranmis | eng | 0.98 → 0.99 | yeni | 2 / 5 | – | 4, 58, 6 |
| 110 | taranmis | eng | 1.00 → 1.00 | yeni | 2 / 2 | – | – |
| 111 | taranmis | eng | 0.99 → 1.00 | yeni | 9 / 12 | – | 4, 4, 4 |
| 112 | taranmis | eng | 0.99 → 0.99 | yeni | 4 / 3 | 98×1, 39×1 | 59 |
| 113 | taranmis | eng | 0.99 → 0.99 | yeni | 6 / 6 | 14×1 | 4 |
| 114 | taranmis | eng | 0.99 → 0.98 | yeni | 8 / 9 | 9×1 | 1, 1 |
| 115 | yok | eng | 0.00 → 0.75 | goruntu | 0 / 0 | – | – |
| 116 | taranmis | eng | 0.99 → 0.99 | yeni | 8 / 9 | 2×1 | 1.2, 4 |
| 117 | taranmis | eng | 0.99 → 0.99 | yeni | 8 / 7 | 134.135×1, 1×1, 9×1, 63×1 | 134, 135, 4 |
| 118 | taranmis | eng | 0.98 → 0.99 | yeni | 5 / 6 | – | 4 |
| 119 | taranmis | eng | 0.97 → 0.98 | yeni | 6 / 9 | 8×1 | 22, 4, 6, 6 |
| 120 | taranmis | eng | 0.98 → 0.98 | yeni | 8 / 8 | – | – |
| 121 | taranmis | eng | 0.96 → 0.96 | yeni | 8 / 14 | – | 1, 1, 1, 2, 4, 4 |
| 122 | taranmis | eng | 0.98 → 0.97 | yeni | 8 / 9 | 4×1 | 0, 414 |
| 123 | taranmis | eng | 1.00 → 0.98 | yeni | 4 / 7 | – | 1, 21, 67 |
| 124 | taranmis | eng | 0.98 → 0.99 | yeni | 2 / 2 | – | – |
| 125 | taranmis | eng | 0.99 → 0.99 | yeni | 5 / 7 | – | 4, 9 |
| 126 | taranmis | eng | 0.97 → 0.99 | yeni | 5 / 4 | 3×1 | – |
| 127 | taranmis | eng | 1.00 → 1.00 | yeni | 6 / 7 | – | 70 |
| 128 | taranmis | eng | 0.99 → 0.98 | yeni | 11 / 13 | – | 2, 4 |
| 129 | taranmis | eng | 0.98 → 0.99 | yeni | 4 / 4 | 71×1 | 1 |
| 130 | taranmis | eng | 1.00 → 1.00 | yeni | 1 / 1 | – | – |
| 131 | taranmis | eng | 0.97 → 0.97 | yeni | 1 / 3 | – | 117, 72 |
| 132 | taranmis | eng | 1.00 → 0.99 | yeni | 5 / 6 | – | 2 |
| 133 | taranmis | eng | 1.00 → 0.98 | eski | 8 / 8 | – | – |
| 134 | taranmis | eng | 0.96 → 0.99 | yeni | 6 / 11 | – | 119, 2, 3, 6, 75 |
| 135 | taranmis | eng | 0.99 → 1.00 | yeni | 3 / 6 | – | 4, 42, 77 |
| 136 | taranmis | eng | 1.00 → 1.00 | yeni | 2 / 4 | – | 1, 2 |
| 137 | taranmis | eng | 0.99 → 0.99 | yeni | 13 / 12 | 1×2, 6×1 | 2, 4 |
| 138 | taranmis | eng | 0.99 → 0.98 | yeni | 9 / 12 | 6×1 | 1, 2, 7, 79 |
| 139 | taranmis | eng | 0.98 → 0.97 | yeni | 3 / 7 | – | 2, 3, 505.05, 525.254 |
| 140 | taranmis | eng | 1.00 → 1.00 | yeni | 6 / 6 | 3×1 | 1 |
| 141 | taranmis | eng | 0.99 → 1.00 | yeni | 9 / 12 | – | 4, 4, 9 |
| 142 | taranmis | eng | 0.99 → 1.00 | yeni | 11 / 10 | 1×1, 6×1 | 12 |
| 143 | taranmis | eng | 0.99 → 1.00 | yeni | 6 / 9 | – | 1, 4, 83 |
| 144 | taranmis | eng | 0.99 → 0.96 | eski | 18 / 18 | – | – |
| 145 | taranmis | eng | 0.98 → 0.99 | yeni | 3 / 9 | – | 1, 131, 133, 4, 85, 87 |
| 146 | taranmis | eng | 0.99 → 1.00 | yeni | 9 / 10 | – | 86 |
| 147 | taranmis | eng | 0.99 → 0.99 | yeni | 3 / 4 | – | 8 |
| 148 | taranmis | eng | 1.00 → 0.99 | yeni | 3 / 5 | 4×1 | 1, 1, 6 |
| 149 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 150 | taranmis | eng | 1.00 → 1.00 | yeni | 10 / 12 | – | 1, 6 |
| 151 | taranmis | eng | 0.99 → 0.99 | yeni | 11 / 10 | 90×1 | – |
| 152 | taranmis | eng | 1.00 → 0.98 | yeni | 12 / 10 | 1×2, 3×1 | 3.4 |
| 153 | taranmis | eng | 1.00 → 0.98 | yeni | 9 / 9 | 3×1, 2×1 | 32, 4 |
| 154 | taranmis | eng | 1.00 → 1.00 | yeni | 14 / 10 | 3×1, 4×1, 9×1, 90×1 | – |
| 155 | taranmis | eng | 0.99 → 0.99 | yeni | 10 / 24 | – | 1, 10, 100, 101, 12, 13, 141, 2, 5, 5, 6, 61 |
| 156 | taranmis | eng | 0.99 → 1.00 | yeni | 17 / 18 | 684×1 | 110, 68 |
| 157 | yok | eng | 1.00 → 1.00 | yeni | 0 / 0 | – | – |
| 158 | taranmis | eng | 0.99 → 0.99 | yeni | 13 / 16 | – | 2, 4, 4 |
| 159 | yok | eng | 0.75 → 0.75 | goruntu | 2 / 2 | – | – |
| 160 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 161 | yok | eng | 0.00 → 0.75 | goruntu | 0 / 0 | – | – |
| 162 | taranmis | eng | 1.00 → 1.00 | yeni | 2 / 2 | – | – |
| 163 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |
| 164 | yok | eng | 0.00 → 0.00 | goruntu | 0 / 0 | – | – |

## Sayı içeren değişimler: inceleme gerekenler (kelime hizalaması; düzeltme, biçim, taşınan hariç)

| Sayfa | eski katman | yeni katman |
|---|---|---|
| 6 | `rr 515` | `TT JP` |
| 6 | `1151,` | `/736` |
| 9 | `1` | `` |
| 9 | `3` | `` |
| 9 | `3` | `` |
| 9 | `4` | `` |
| 9 | `5` | `` |
| 9 | `6` | `` |
| 9 | `6` | `` |
| 9 | `9` | `` |
| 9 | `14` | `` |
| 9 | `14` | `` |
| 9 | `16` | `` |
| 9 | `17` | `` |
| 9 | `18` | `` |
| 9 | `20` | `` |
| 9 | `21` | `` |
| 9 | `21` | `` |
| 9 | `25` | `` |
| 9 | `25` | `` |
| 9 | `26` | `` |
| 9 | `t 28` | `` |
| 9 | `30` | `` |
| 9 | `31` | `` |
| 9 | `31` | `` |
| 9 | `32` | `` |
| 9 | `32` | `` |
| 9 | `33` | `` |
| 9 | `35` | `` |
| 9 | `37` | `` |
| 9 | `37` | `` |
| 9 | `38` | `` |
| 9 | `38` | `` |
| 9 | `38` | `` |
| 9 | `39` | `` |
| 9 | `39` | `` |
| 9 | `40` | `` |
| 9 | `41` | `` |
| 9 | `41` | `` |
| 9 | `50` | `` |
| 9 | `50` | `` |
| 9 | `50 vii` | `ND OO & OO FO — <` |
| 10 | `55` | `` |
| 10 | `59` | `` |
| 10 | `` | `51 54 95 56 56 56 57 57 99 60 62 62 63 63 64 65 66 66 67 69 69 70 70 70 72 74 74 77 78 78 80 82 82 83 84 85 85 86 86 86 ` |
| 11 | `12 3` | `123` |
| 15 | `b.` | `6.` |
| 15 | `Vi` | `%4` |
| 15 | `b.` | `6.` |
| 15 | `1` | `` |
| 16 | `` | `2` |
| 16 | `V4` | `'4` |
| 16 | `Vi` | `'4` |
| 18 | `b.` | `6b.` |
| 19 | `5` | `` |
| 20 | `7 Vi` | `7!2` |
| 20 | `L` | `2.` |
| 22 | `8` | `A Tailoring Manual` |
| 22 | `` | `f, 8. 1.` |
| 22 | `3A` | `%` |
| 23 | `lA` | `4` |
| 23 | `5.` | `35.` |
| 24 | `3A` | `%` |
| 24 | `b.` | `6.` |
| 26 | `` | `12` |
| 27 | `` | `13` |
| 27 | `1 Vi-inch` | `14-inch` |
| 27 | `13` | `k,l.` |
| 27 | `lVi` | `1%` |
| 28 | `` | `14` |
| 28 | `2, T` | `2,2’` |
| 28 | `5, 5'` | `9,5’` |
| 28 | `3A` | `%` |
| 28 | `6, 6'` | `6,6’` |
| 29 | `` | `8 c,d 2,9` |
| 29 | `8` | `a. Front` |
| 29 | `V2` | `2` |
| 29 | `` | `911` |
| 31 | `S| .§ | 8 | N 1 | J` | `` |
| 31 | `` | `Plus 4" for` |
| 31 | `5V*"` | `54%”` |
| 31 | `curve.) Plus W for arm ease Plus shoulder pad height if used b.` | `curve. ) 6.` |
| 31 | `` | `3"` |
| 31 | `3" or more` | `—` |
| 31 | `` | `0` |
| 31 | `T-T-T 0 /.` | `7-7-7 f.` |
| 31 | `` | `b. Figure 4 (b)` |
| 31 | `` | `17` |
| 31 | `45` | `5` |
| 31 | `` | `4` |
| 31 | `g` | `2 E 3 ~ 2` |
| 31 | `J_` | `7` |
| 33 | `` | `19` |
| 33 | `xh` | `'4` |
| 33 | `2.` | `.` |
| 33 | `3.` | `.` |
| 33 | `Vi` | `'2` |
| 35 | `1` | `|` |
| 35 | `(V2` | `('2` |
| 35 | `3A` | `%` |
| 35 | `b.` | `6b.` |
| 40 | `b.` | `6.` |
| 41 | `` | `—_ oo b. = Figure 9` |
| 41 | `` | `_— Figure 9 f.` |
| 41 | `` | `scye 6 inches down, then diagonally to` |
| 42 | `` | `28 A Tatlonng Manual` |
| 42 | `Vi` | `2` |
| 42 | `` | `tern outward ‘4 inch to widen neck edge of` |
| 42 | `` | `back. Draw new upper back along pattern edge. 6b. Measure 1 inch in on neck line from new center back and mark. Draw lin` |
| 42 | `Vi` | `'4` |
| 42 | `Vi` | `4` |
| 43 | `lA` | `'4` |
| 44 | `` | `Y tml OT HCHHTTTTHHTLALL, 4 ] ] ] SS NS` |
| 44 | `V4` | `4` |
| 45 | `Figure 12` | `` |
| 45 | `V*` | `‘4` |
| 45 | `` | `Y Y Y y Z Z 4 7 / ; YY YEE veer` |
| 45 | `1` | `!` |
| 46 | `` | `TYPES OF SET-IN SLEEVES USED IN TAILORED GARMENTS Figure 15. SS` |
| 46 | `a.` | `i " " 1 " 1 " i | 1 i — a` |
| 46 | `F IV2` | `114` |
| 46 | `G 1 lh` | `14` |
| 46 | `J` | `7` |
| 46 | `L Vi` | `2` |
| 47 | `Pattern Alteration 33 Figure 15` | `f` |
| 47 | `Vi` | `'4` |
| 47 | `E Intersection of AB and CD. F Top of back half of sleeve cap. G Top of front half of sleeve. H 1 xh` | `14` |
| 47 | `I Vh` | `1` |
| 47 | `IJ.` | `[7. Nor AO Oy by . ——___ | | e. Figure 15` |
| 47 | `` | `d. M N Intersection of AB and CD. Top of back half of sleeve cap. Top of front half of sleeve. 33 mm` |
| 47 | `IJ.` | `17.` |
| 47 | `J. d.` | `7.` |
| 49 | `J` | `7` |
| 49 | `` | `K Figure 16 g. ~~ 35` |
| 49 | `IH. Figure 16 g. g. AB` | `JH.` |
| 49 | `L VA` | `1%` |
| 49 | `M V/z` | `14` |
| 49 | `/. 0` | `I.` |
| 49 | `0.` | `O.` |
| 50 | `` | `alo Figure 16 h. h. Figure 16 i. z. g.` |
| 50 | `Figure 16 /. 1.` | `` |
| 50 | `/` | `7` |
| 52 | `1 to \Vi` | `ltol%` |
| 52 | `1` | `|` |
| 52 | `1 xh or more` | `l’ormore` |
| 52 | `1` | `|` |
| 52 | `lh` | `“4` |
| 52 | `` | `Figure 17` |
| 52 | `is` | `3s` |
| 52 | `b.` | `6.` |
| 52 | `b.` | `0.` |
| 53 | `` | `39` |
| 53 | `wad¬ 39` | `wad-` |
| 55 | `b.` | `6b.` |
| 56 | `42` | `` |
| 56 | `3 4 5 6` | `J` |
| 56 | `b.` | `6.` |
| 57 | `d.` | `43 4 Problem: Full bust. a. Garment bunches may appear at front` |
| 57 | `4 Problem: Full bust. a. Garment bunches may appear at front` | `b.` |
| 58 | `` | `d. Figure 21 (Problem 2, Continued)` |
| 58 | `b.` | `6.` |
| 58 | `` | `b. Figure 21 (Problem 3)` |
| 59 | `` | `—~ —~ — —!O Jj. - L — Figure 21 (Problem 4) - SS Ww ——hL 1oeLeb i Figure 21 (Problem 5) Figure 21 (Problem 6)` |
| 59 | `shoulders. Use the same alteration as 7 a, b, and c to remove excess back length. 9 Problem: Garment too wide both front` | `.` |
| 59 | `b.` | `shoulders. 6.` |
| 59 | `` | `Use the same alteration as 7 a, 6, and c to remove excess back length. 9 Problem: Garment too wide both front and back.` |
| 60 | `` | `— — “|| _ ee — —_— “_ —" Figure 21 (Problem 8)` |
| 61 | `` | `! \ J iN l Q Nn 47 1] Figure 21 (Problems 10, 11) > ee aN => >>> = % KN XY _ mr he Mee tienes ‘ IN ee ee ——_—. \ IN eZ \` |
| 62 | `14 15` | `an a =-2 a —e ee Lt — ee tL a — LS] — GO a2 .W< -.—39@ - 2c —” Y-3 de ——— — Lob bk —_= —d & —_ 1S.)` |
| 63 | `b.` | `6.` |
| 63 | `7 7` | `17` |
| 63 | `Vi` | `4` |
| 63 | `b.` | `6.` |
| 64 | `` | `50` |
| 64 | `` | `a. b. c. d. Figure 22` |
| 65 | `` | `51` |
| 65 | `t.` | `1.` |
| 66 | `` | `52` |
| 69 | `55` | `95` |
| 70 | `56` | `36` |
| 71 | `5.)` | `9.)` |
| 73 | `b,` | `6,` |
| 73 | `` | `b. Figure 26` |
| 75 | `` | `61` |
| 76 | `b,` | `8,` |
| 76 | `xh` | `2` |
| 76 | `b.` | `6.` |
| 76 | `` | `Figure 27` |
| 76 | `b,` | `6,` |
| 77 | `` | `the Skirt 63` |
| 77 | `` | `YY: SY —18Q ~EhD <OD 4g ~COD -h —VED ~tHd ~eng` |
| 77 | `the Skirt 63` | `Cc.` |
| 79 | `65` | `Lo rf` |
| 79 | `1,2,3,4)` | `1, 2, 3, 4) 3` |
| 79 | `` | `65 | Ee fe) 6` |
| 80 | `` | `_S —— <— rte enn 3 _ S| a. b.` |
| 80 | `` | `4` |
| 80 | `` | `Figure 30` |
| 80 | `` | `pleat fold. in 2 en pleats start below the belt, the pleats` |
| 80 | `as in 2.` | `asm é. must have width stitching across the top edge to` |
| 80 | `d. Figure 30 Pleats may be stitched from outside along` | `on` |
| 81 | `67` | `` |
| 81 | `%6` | `%e` |
| 81 | `V4` | `4` |
| 81 | `b.` | `6.` |
| 81 | `Vi` | `4` |
| 83 | `` | `69` |
| 83 | `` | `Q o— Figure 33` |
| 84 | `` | `Figure 34` |
| 85 | `V4` | `4` |
| 86 | `` | `eeea + ) i) ) | ‘ 0 ] 0 0 Q Q 0 $ 0 t 0 ‘ 0 0 0 Figure 36` |
| 86 | `b,` | `6,` |
| 86 | `2V6` | `2%` |
| 86 | `b,` | `6,` |
| 87 | `b,` | `6,` |
| 88 | `b.` | `6.` |
| 88 | `Vi` | `4` |
| 88 | `Vi` | `‘4` |
| 88 | `tendency to fray. SEAM FINISHES ON RIGHT SIDE OF GARMENT` | `a ~~ _ | rye Ry ee Figure 38` |
| 89 | `` | `75` |
| 92 | `1` | `|` |
| 92 | `V4` | `4` |
| 92 | `V4` | `‘4` |
| 92 | `3/i6` | `%e` |
| 93 | `3/i6` | `“6` |
| 93 | `$Ae` | `%6` |
| 93 | `Vi` | `4` |
| 94 | `` | `ene ae rn qd. L } ny TT S li b. Nn yN 7 a` |
| 94 | `Tailoring` | `A a a Figure 42 A Tailonng` |
| 94 | `comers. 2.` | `corners.` |
| 94 | `3.` | `.` |
| 94 | `b.` | `6.` |
| 94 | `s/46` | `“6` |
| 94 | `2.` | `` |
| 96 | `` | `Figure 44 Cut buttonhole:` |
| 96 | `b.` | `6.` |
| 97 | `b.` | `6.` |
| 97 | `` | `Figure 45` |
| 98 | `84` | `8` |
| 98 | `©@ © ©` | `Qa. ot b. Sh <= Figure 46` |
| 99 | `p` | `Making the Jacket or Coat PREPARING INSIDE CUTS ON GARMENT SURFACE Figure 47. Reinforced corners or turns: Any seam cut ` |
| 99 | `` | `c. x From the seam edge, stitch an arrowhead to the point of seam, pivot the fabric around the needle, take one short st` |
| 99 | `` | `47 85` |
| 100 | `1 %-inch` | `14-inch` |
| 100 | `b.` | `6.` |
| 100 | `b.` | `6.` |
| 101 | `` | `jousyow yo ;yBinys Figure 48` |
| 101 | `b.` | `6.` |
| 101 | `Vi` | `4` |
| 102 | `50` | `49 xf N \ ‘ -— 2,` |
| 102 | `b.` | `6.` |
| 102 | `2 xh` | `2'4` |
| 102 | `Vi` | `'4` |
| 102 | `Vi` | `'4` |
| 102 | `b.` | `6.` |
| 103 | `Figure 51` | `Making the Jacket or Coat 89` |
| 103 | `TAP Figu a` | `TAPING THE GARMENT FRONTS Figure 52. a. Lay garment flat on table with canvas up. 1. Pin tape along back edge of break l` |
| 105 | `b.` | `6.` |
| 105 | `53` | `33` |
| 106 | `V4` | `4` |
| 106 | `b.` | `6.` |
| 108 | `Vi-` | `4-` |
| 108 | `1` | `|` |
| 108 | `b.` | `6.` |
| 108 | `b` | `5` |
| 108 | `Figure 57` | `A` |
| 108 | `b,` | `3),` |
| 108 | `` | `Figure 57` |
| 109 | `b.` | `6b.` |
| 109 | `Si b. Figure S8` | `58` |
| 109 | `Vi-inch` | `'4-inch` |
| 111 | `1V4` | `1%` |
| 111 | `Vi-inch` | `%4-inch` |
| 111 | `Vi-inch` | `'4-inch` |
| 111 | `Vi-inch` | `'4-inch` |
| 111 | `Vi-inch` | `'4-inch` |
| 111 | `` | `-= a. A Figure 59 97` |
| 112 | `98` | `` |
| 112 | `39` | `59` |
| 113 | `FLAP POCKET` | `99 d. Cut one section of pocket bag of wool and one of lining silk.` |
| 113 | `14-inch` | `'4-inch` |
| 113 | `b. 99 d. Cut one section of pocket bag of wool and one of lining silk. 1. Match the stitching line of the wool sec¬ tion` | `Figure 60` |
| 114 | `e. f. 9-` | `i q 1 i t] & lp, a ean conicanomn, oem ~"~ g.` |
| 116 | `` | `102` |
| 116 | `lA` | `4` |
| 116 | `b.` | `6.` |
| 116 | `1, 2.` | `1,2.` |
| 117 | `134,135.) d.` | `134, 135.) .` |
| 117 | `lA` | `4` |
| 117 | `1 e f. 9- Figure 63` | `Ke) a Ee Sen EP aa es ab ab ae See 103` |
| 118 | `lA` | `4` |
| 118 | `b.` | `6.` |
| 119 | `r b. ] C.` | `_ - => & = l= «= me PRO ene ee eee 22am = NN \` |
| 119 | `(b)` | `(6)` |
| 119 | `(b)` | `(6)` |
| 119 | `` | `4` |
| 121 | `` | `Pockets 107` |
| 121 | `c is` | `¢ 1s` |
| 121 | `b.` | `6.` |
| 121 | `po¬` | `po- 2` |
| 121 | `lA` | `4` |
| 121 | `b. Figure 66 e.` | `emnem` |
| 121 | `lA` | `4` |
| 121 | `` | `Figure 66` |
| 122 | `` | `h. Figure 66 (Continued)` |
| 122 | `b` | `0` |
| 122 | `4xh` | `414` |
| 123 | `` | `a. = = — XX P< = 1] ‘ = ~ |x xx 21 b. d. Figure 67` |
| 124 | `3.` | `.` |
| 124 | `4.` | `` |
| 124 | `2.` | `.` |
| 124 | `3.` | `.` |
| 124 | `2.` | `.` |
| 125 | `Vi` | `4` |
| 125 | `` | `ANN 9 |<——— >` |
| 126 | `r_3 l_-J J-` | `` |
| 126 | `g.` | `( ) J: eS, Figure 69 (Continued)` |
| 127 | `1.` | `113 .` |
| 127 | `2.` | `.` |
| 127 | `3.` | `.` |
| 127 | `4.` | `.` |
| 127 | `5.` | `.` |
| 127 | `3.` | `.` |
| 127 | `` | `Figure 70` |
| 128 | `1` | `|` |
| 128 | `lVi` | `1'4` |
| 128 | `1.` | `t.` |
| 128 | `Vi` | `2` |
| 129 | `Collar 115 Figure 71` | `k,l.` |
| 129 | `` | `line d, pad stitch a continuous line the en- tire length of the collar to the top buttonhole, k. Continue pad stitching ` |
| 130 | `` | `2.` |
| 130 | `2.` | `` |
| 130 | `3.` | `.` |
| 130 | `4.` | `.` |
| 130 | `5.` | `.` |
| 130 | `6.` | `.` |
| 131 | `` | `Collarless Garments Figure 72. In all garments without collars an ease thread or stay stitching should be placed around ` |
| 131 | `` | `117` |
| 132 | `V&-inch` | `’2-inch` |
| 134 | `(b-3)` | `(6-3)` |
| 134 | `` | `fin- > & A Tailoring Manual te LX ° 2%, ished hem and slightly longer than the cir- cumference of finished wrist edge. W` |
| 135 | `` | `121 ease the outer fabric section over the hymo, pin, baste, and stitch the three sec- tions together across each end an` |
| 135 | `` | `two cuff edges together '4 inch, the width` |
| 135 | `2.` | `` |
| 135 | `3.` | `` |
| 135 | `` | `| Figure 77.` |
| 135 | `б.` | `6.` |
| 135 | `` | `Figure 77` |
| 136 | `xh` | `2` |
| 137 | `Vi` | `2` |
| 137 | `1` | `|` |
| 137 | `Vi 6-` | `“i6-` |
| 137 | `1 Vi-inch` | `1'4-inch` |
| 138 | `c. HEMMING THE LONG COAT` | `m. i o ve a ——_ —e awe ase a= = — qa. Hi ' ’ ° 1] € i|U ' f ( ae baaenieions pinbeiaie | ink te ee | __2 e@ @@ @ oo & ge` |
| 138 | `80. The hems of the long coat and lining are fin¬ ished separately. a. The long coat is hemmed entirely across the hem a` | `79 Cc.` |
| 138 | `Vi 6` | `Me` |
| 138 | `interlining.)` | `interlining. ) HEMMING THE LONG COAT Figure 80. The hems of the long coat and lining are fin- ished separately. a. The l` |
| 139 | `` | `125 Q. 2 Be L 3` |
| 139 | `3.` | `.` |
| 139 | `4.` | `.` |
| 139 | `b.` | `y H _a~ aw em © am a em ao a ow ae a= ae on 505.05. oo =-_—e oe oe ee ee we we we oe em ow ow = eas = = OOK ate 525.254 ` |
| 140 | `3A` | `%` |
| 140 | `b.` | `6.` |
| 141 | `` | `127` |
| 141 | `c.` | `4 an! 9 Cc.` |
| 141 | `` | `Figure 82` |
| 142 | `` | `1.` |
| 142 | `4.` | `.` |
| 142 | `1 Vi-inch` | `1'4-inch` |
| 142 | `5.` | `.` |
| 142 | `2.` | `.` |
| 142 | `1V4` | `12` |
| 142 | `5.` | `` |
| 142 | `H 6` | `Xe` |
| 142 | `2.` | `.` |
| 142 | `out b. 1.` | `out. .` |
| 143 | `` | `Figure 83` |
| 143 | `(lVi-inch-pleat)` | `(1'4-inch-pleat)` |
| 145 | `` | `Lining the Garment 131 Fasten the two hem edges together at the seams, and between seams if circumference of garment is ` |
| 145 | `` | `hem to the lining so that the stitches do not show from the right side of the lining. In the short jacket the hem at jac` |
| 146 | `` | `132` |
| 146 | `b.` | `6.` |
| 146 | `` | `Figure 86` |
| 147 | `` | `133` |
| 147 | `` | `A 8` |
| 148 | `` | `134` |
| 148 | `by` | `6,` |
| 148 | `(4 cy /).` | `(d ¢, {).` |
| 150 | `\lh` | `1%` |
| 150 | `Vi6` | `‘6` |
| 150 | `garment` | `garment. 136` |
| 151 | `` | `b. Measurement of the figure with minimum allowance for ease. 1. 2. 3. 4. 5. 6. Waistline: snug enough to stay in place.` |
| 152 | `3, 4.` | `3,4.` |
| 152 | `1` | `|` |
| 152 | `V4` | `4` |
| 152 | `-1 ■` | `-|l ! C Cc.` |
| 153 | `Vi` | `'4` |
| 153 | `3V2` | `32` |
| 154 | `3 4 9- Figure 90 (Continued)` | `` |
| 155 | `` | `Slacks POCKETS Slacks may have pockets on both sides in seam and placket, or in the right side seam only, or pockets may` |
| 155 | `` | `> a bed » A wn 141 \ 1/ Ls Pocket enlarged Figure 91 (a) Match the pocket bag to the stitching line of side seams of the` |
| 156 | `` | `joe ee = = = = wm Figure 91 (a) (Continued)` |
| 156 | `684` | `68d,` |
| 156 | `HO.)` | `110.)` |
| 156 | `b.` | `6.` |
| 158 | `1.` | `l.` |
| 158 | `5.` | `` |
| 158 | `b.` | `6.` |
| 158 | `Vi` | `4` |
| 158 | `Vi` | `2` |
| 158 | `V4` | `4` |
| 162 | `` | `148` |

## Düzeltme sınıfına girenlerden örnekler

- s.28: `7, 7'` → `7,7'`
- s.39: `is` → `1s`
- s.40: `is` → `1s`
- s.51: `is` → `1s`
- s.55: `i.` → `1.`
- s.55: `is` → `1s`
- s.62: `12,13,14,15)` → `12, 13, 14, 15)`
- s.64: `Ill,` → `111,`
- s.73: `Ill,` → `111,`
- s.79: `5,6)` → `5, 6)`
- s.88: `is` → `1s`
- s.89: `is` → `1s`
- s.89: `is` → `1s`
- s.89: `is` → `1s`
- s.92: `is` → `1s`
- s.100: `i.` → `1.`
- s.114: `is` → `1s`
- s.116: `is` → `1s`
- s.118: `i.` → `1.`
- s.121: `is` → `1s`
- s.129: `is` → `1s`
- s.136: `is` → `1s`
- s.148: `is` → `1s`
- s.148: `is` → `1s`
