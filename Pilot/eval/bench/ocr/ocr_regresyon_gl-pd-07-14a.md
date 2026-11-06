# OCR regresyon kontrolü: gl-pd-07-14a

2026-11-06 16:49. pilot/ocr.py (sayfa sınıfı → bayrak, sayfa başına dil, eski/yeni seçimi, süzgeç). Değerler verify'ın kanonik sayı biçiminde, sayfa başına çoklu küme. "Kaybolan" = eski katmanda olup son katmanda olmayan; doğru olup olmadığı sayfa görüntüsünden elle değerlendirilir.

| Ölçü | Değer |
|---|---|
| belge | gl-pd-07-14a |
| sayfa | 48 |
| sure_sn | 0.0 |
| secim | {'yeni': 44, 'eski': 4} |
| eski_sayi | 2253 |
| son_sayi | 2382 |
| kaybolan_deger | 153 |
| kayipli_sayfa | 39 |
| eklenen_deger | 282 |
| degisim_sinifi | {'inceleme': 146, 'duzeltme': 127, 'tasindi': 25} |
| ocr_sure_sn | 77.6 |

| Sayfa | sınıf | dil | skor eski → yeni | seçim | eski / son sayı | kaybolan | eklenen |
|---|---|---|---|---|---|---|---|
| 1 | taranmis | eng | 0.99 → 0.99 | yeni | 22 / 24 | 1×1, 50150×1, 65125×1 | 2007, 25, 50, 50, 65 |
| 2 | taranmis | eng | 1.00 → 1.00 | yeni | 18 / 17 | 2×1 | – |
| 3 | taranmis | eng | 0.99 → 1.00 | yeni | 37 / 37 | 3×1 | 14 |
| 4 | taranmis | eng | 0.99 → 0.97 | eski | 23 / 23 | – | – |
| 5 | taranmis | eng | 1.00 → 1.00 | yeni | 44 / 44 | 1060.2001×1, 1×1, 0×1, 5×1 | 10, 1060, 14, 2001 |
| 6 | taranmis | eng | 0.99 → 1.00 | yeni | 70 / 67 | 0×2, 50×1, 1×3, 6×1 | 14, 2, 25, 501 |
| 7 | taranmis | eng | 1.00 → 1.00 | yeni | 79 / 91 | 118×2, 1132×2, 7×1 | 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 11 |
| 8 | taranmis | eng | 1.00 → 0.99 | yeni | 63 / 58 | 5×1, 50×1, 99×1, 195×1, 8×1 | – |
| 9 | taranmis | eng | 0.99 → 0.99 | yeni | 59 / 56 | 40×1, 195×1, 9×1 | – |
| 10 | taranmis | eng | 1.00 → 1.00 | yeni | 58 / 66 | 118×4, 11×3, 112×4, 1116×1 | 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 16 |
| 11 | taranmis | eng | 1.00 → 1.00 | yeni | 65 / 77 | 114×2, 112×7, 0.1×1, 118×1, 11×1 | 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 |
| 12 | taranmis | eng | 0.97 → 1.00 | yeni | 129 / 137 | 112×6 | 1, 1, 1, 1, 1, 1, 1, 14, 2, 2, 2, 2 |
| 13 | taranmis | eng | 0.92 → 1.00 | yeni | 209 / 219 | 112×10 | 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2 |
| 14 | taranmis | eng | 0.99 → 0.99 | yeni | 15 / 12 | 11×2, 0×2 | 1 |
| 15 | taranmis | eng | 0.99 → 0.98 | yeni | 13 / 14 | – | 4 |
| 16 | taranmis | eng | 0.98 → 0.98 | yeni | 14 / 14 | 11×2, 00×1 | 1, 1, 100 |
| 17 | taranmis | eng | 1.00 → 0.99 | yeni | 14 / 13 | 1×1, 00×1, 170×1 | 100, 17 |
| 18 | taranmis | eng | 0.99 → 1.00 | yeni | 34 / 39 | 112×2, 114×1 | 1, 1, 1, 1, 1, 2, 2, 4 |
| 19 | taranmis | eng | 0.96 → 0.98 | yeni | 46 / 47 | 5×1, 112×1 | 1, 1, 2 |
| 20 | taranmis | eng | 0.99 → 0.97 | eski | 57 / 57 | – | – |
| 21 | taranmis | eng | 0.99 → 0.98 | yeni | 60 / 69 | 118×5, 1116×1, 502.503×2, 114×1 | 1, 1, 1, 1, 1, 1, 1, 16, 4, 502, 502, 503 |
| 22 | taranmis | eng | 1.00 → 1.00 | yeni | 75 / 76 | 114×3, 112×1, 48×1 | 1, 1, 1, 4, 4, 4 |
| 23 | taranmis | eng | 0.99 → 0.97 | yeni | 336 / 344 | 112×5, 11×1, 43×1 | 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2 |
| 24 | taranmis | eng | 0.98 → 0.99 | yeni | 17 / 18 | 1.4×1 | 14, 4 |
| 25 | taranmis | eng | 0.99 → 0.99 | yeni | 44 / 54 | 112×4, 114×5 | 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2 |
| 26 | taranmis | eng | 0.99 → 0.99 | yeni | 34 / 37 | 114×2 | 1, 1, 1, 4, 4 |
| 27 | taranmis | eng | 0.98 → 0.97 | yeni | 69 / 73 | 11×1, 22×1 | 1, 14, 2, 2, 2, 3776 |
| 28 | taranmis | eng | 0.97 → 0.97 | yeni | 60 / 69 | 11×1, 135.3×1, 5.1×1, 19.2×1, 25.3×1, 35.4×1, 45.49×1 | 1, 10, 135, 19, 20, 25, 3, 30, 35, 3773, 40, 4108 |
| 29 | taranmis | eng | 0.92 → 0.94 | yeni | 31 / 33 | 3×1, 4.1×1, 5×1, 530×1 | 0.000001, 0.0001, 1, 1, 100, 5.1 |
| 30 | taranmis | eng | 0.98 → 0.98 | yeni | 23 / 29 | 99.999×1 | 1, 1, 1.1, 10, 299.999, 4, 4 |
| 31 | taranmis | eng | 0.97 → 0.98 | yeni | 24 / 36 | 2×1, 135.3×1, 75.1×1 | 1, 1, 1, 1, 1, 10, 100, 135, 150, 200, 3, 5 |
| 32 | taranmis | eng | 0.99 → 1.00 | yeni | 30 / 38 | 3.2×1, 0.4×1 | 0, 1, 1.3, 10, 10, 100, 14, 2, 4, 95 |
| 33 | taranmis | eng | 0.97 → 0.98 | yeni | 18 / 18 | 1×1 | 95 |
| 34 | taranmis | eng | 0.95 → 0.96 | yeni | 38 / 38 | 0×1 | 10 |
| 35 | taranmis | eng | 0.97 → 0.97 | yeni | 25 / 31 | 2×1 | 0.001, 000, 1, 1, 1, 1, 1.1 |
| 36 | taranmis | eng | 0.98 → 0.99 | yeni | 61 / 67 | 921×1, 21×3 | 1, 1, 1, 1, 1, 2, 2, 2, 2, 9 |
| 37 | taranmis | eng | 0.99 → 1.00 | yeni | 53 / 56 | 14×1, 112×1 | 1, 144, 2, 200, 3 |
| 38 | taranmis | eng | 1.00 → 1.00 | yeni | 32 / 34 | – | 15, 15 |
| 39 | taranmis | eng | 0.98 → 0.98 | yeni | 23 / 23 | – | – |
| 40 | taranmis | eng | 0.97 → 0.97 | yeni | 36 / 36 | 14×1 | 144 |
| 41 | taranmis | eng | 1.00 → 1.00 | yeni | 41 / 41 | 41×1 | 4 |
| 42 | taranmis | eng | 0.98 → 0.98 | yeni | 13 / 13 | – | – |
| 43 | taranmis | eng | 0.91 → 1.00 | yeni | 5 / 4 | 1×1 | – |
| 44 | taranmis | eng | 0.90 → 0.73 | eski | 4 / 4 | – | – |
| 45 | taranmis | eng | 0.97 → 1.00 | yeni | 5 / 5 | 14×1 | 144 |
| 46 | taranmis | eng | 0.82 → 0.87 | yeni | 8 / 4 | 1×3, 11×1 | – |
| 47 | taranmis | eng | 0.93 → 0.97 | yeni | 4 / 5 | – | 4 |
| 48 | taranmis | eng | 0.96 → 0.92 | eski | 15 / 15 | – | – |

## Sayı içeren değişimler: inceleme gerekenler (kelime hizalaması; düzeltme, biçim, taşınan hariç)

| Sayfa | eski katman | yeni katman |
|---|---|---|
| 1 | `Apri12007` | `April 2007 PURCHASE DESCRIPTION` |
| 1 | `1.` | `I,` |
| 1 | `Class 1` | `Classl` |
| 2 | `2` | `` |
| 3 | `` | `2-1-2519-1` |
| 3 | `` | `2-1-2519-2` |
| 3 | `` | `2-1-2519-3` |
| 5 | `65/25/1 0` | `65/25/10` |
| 5 | `5` | `` |
| 6 | `MIL-DTL-444 1 1` | `MIL-DTL-44411` |
| 6 | `MIL-DTL-444 1 1` | `MIL-DTL-44411` |
| 6 | `` | `>/= 90%` |
| 6 | `` | `>/= 90%` |
| 6 | `6 % Bite Protection >/=90% >/=90% >/=70` | `>/= 70` |
| 7 | `caniers, I-end` | `carriers, 1-end` |
| 7 | `7` | `` |
| 8 | `A-A-50l99,` | `A-A-50199,` |
| 8 | `stitch(5` | `stitch(S` |
| 8 | `A-A-55 195,` | `A-A-55195,` |
| 8 | `8` | `` |
| 9 | `40` | `AQ` |
| 9 | `A-A-55 195,` | `A-A-55195,` |
| 9 | `9` | `` |
| 10 | `pattel11s` | `patterns` |
| 10 | `pattel11.` | `pattern.` |
| 10 | `pattel11` | `pattern` |
| 11 | `114 inch.` | `1/4 inch,` |
| 11 | `- 112` | `— 1/2` |
| 11 | `(3.5 .1.1)` | `(3.5.1.1)` |
| 11 | `11` | `Il` |
| 12 | `` | `Waist: Up to 27 in. NSN No. NATO Size: 6067/5869 X-Small — Short` |
| 12 | `` | `Waist: Up to 27 in. NSN No. NATO Size: 6775/5869 X-Small — Regular` |
| 12 | `` | `NSN No. NATO Size: 7583/5869 X-Small — Long` |
| 12 | `` | `in. Inseam: 32-1/2 to 35-1/2 in. X-Small — X-Long Inseam: 35-1/2 to 38-1/2` |
| 12 | `NSNNo. NSNNo. NSNNo. NATO Size: 6067/5869 NATO Size: 6775/5869 NATO Size: 7583/5869 X-Small- Long X-Small- X-Long X-Smal` | `X-Small —` |
| 12 | `27` | `26-1/2` |
| 12 | `Up` | `27` |
| 12 | `` | `31 in. Inseam: 26-1/2 to 29-1/2 in. Waist:` |
| 12 | `` | `to 31` |
| 12 | `Up` | `29-1/2` |
| 12 | `26-1/2 in. Inseam: 26-1/2 to 29-1/2 in. Inseam: 29-112 to 32-112` | `32-1/2` |
| 12 | `Waist: 27` | `Inseam: 32-1/2` |
| 12 | `31` | `35-1/2` |
| 12 | `NSNNo. NSNNo. NSNNo.` | `NSN No. NATO Size: 8390/6979 Inseam: 35-1/2 to 38-1/2 in. Waist: 27 to 31 in. NSN No. NATO Size: 9098/6979 NSN No. NSN N` |
| 12 | `Inseam: 32-112 to 35-112 in. Inseam: 35-1/2 to 38-112 in.` | `` |
| 12 | `Waist: 27 to 31 in. Waist: 27 to 31 in. NSNNo. NSNNo. NSNNo. NATO Size: 8390/6979 NATO Size: 9098/6979` | `NSN No.` |
| 13 | `` | `Waist: 31 to 35 in. NSN No. NATO Size: 6067/7989 Medium — Short` |
| 13 | `` | `Waist: 31 to 35 in. NSN No. NATO Size: 6775/7989 Medium — Regular` |
| 13 | `Waist: 31` | `NSN No. NATO Size: 7583/7989 Medium — Long Inseam: 32-1/2` |
| 13 | `35` | `35-1/2` |
| 13 | `Size: 6067/7989 NATO Size: 6775/7989 NATO Size: 7583/7989 Medium ~ Long` | `Size:8390/7989` |
| 13 | `` | `Inseam: 35-1/2 to 38-1/2 in, Waist: 31 to 35 in. NSN No. NATO Size: 9098/7989` |
| 13 | `Inseam: 32-112 to 35-1/2 in. Inseam: 35-112 to 38-1/2 in.` | `` |
| 13 | `Waist: 31 to 35 in. Waist: 31 to 35 in. NSNNo. NSNNo. NSNNo. NATO Size:8390/7989 NATO Size: 9098/7989` | `NSN No.` |
| 13 | `` | `Waist: 35 to 39 in. Large — Short` |
| 13 | `` | `Waist: 35 to 39 in. Large - Regular` |
| 13 | `Waist: 35 to 39 in. Waist: 35 to 39 in. NSNNo. NSNNo. NSNNo.` | `NSN No. NSN No. NSN No.` |
| 13 | `` | `Waist: 35 to 39 in. NSN No. NATO Size: 8390/8999` |
| 13 | `` | `Waist: 35 to 39 in. NSN No. NATO Size: 9098/8999` |
| 13 | `Waist: 35 to 39 in. Waist: 35 to 39 in. NSNNo. NSNNo. NSNNo. NATO Size: 8390/8999 NATO Size: 9098/8999` | `NSN No.` |
| 13 | `` | `Waist: 39 to 43 in. NSN No. NATO Size: 6067/9909 X-Large - Short` |
| 13 | `` | `Waist: 39 to 43 in. NSN No, NATO Size: 6775/9909 X-Large - Regular` |
| 13 | `Waist: 39` | `NSN No. NATO Size: 7583/9909 X-Large - Long Inseam: 32-1/2` |
| 13 | `43` | `35-1/2` |
| 13 | `6067/9909 NATO Size: 6775/9909 NATO Size: 7583/9909 X-Large - Long` | `8390/9909` |
| 13 | `X-Large - XX-Long Inseam: 32-1/2 to 35-112 in.` | `` |
| 13 | `` | `Waist: 39 to 43 in. NSN No. NATO Size: 9098/9909 X-Large - XX-Long` |
| 13 | `Waist: 39 to 43 in. Waist: 39 to 43 in. NSNNo. NSNNo. NSNNo. NATO Size: 8390/9909 NATO Size: 9098/9909` | `NSN No.` |
| 13 | `` | `Inseam: Up to 26-1/2 in. Waist: 43 to 47 in. NSN No. NATO Size: 6067/0919` |
| 13 | `` | `Inseam: 26-1/2 to 29-1/2 in. Waist: 43 to 47 in. NSN No. NATO Size: 6775/0919` |
| 13 | `Inseam: Up to 26-112 in. Inseam: 26-112 to 29-112 in.` | `` |
| 13 | `Waist: 43` | `NSN No. NATO Size: 7583/0919 XX-Large - Long Inseam: 32-1/2` |
| 13 | `47` | `35-1/2` |
| 13 | `6067/0919` | `8390/0919 XX-Large - X- Long Inseam: 35-1/2 to 38-1/2 in. Waist: 43 to 47 in, NSN No.` |
| 13 | `6775/0919 NATO Size: 7583/0919 XX-Large - Long XX-Large - X-Long` | `9098/0919` |
| 13 | `Inseam: 32-112 to 35-1/2 in. Inseam: 35-112 to 38-1/2 in.` | `` |
| 13 | `Waist: 43 to 47 in. Waist: 43 to 47 in. NSNNo. NSNNo. NSNNo. NATO Size: 8390/0919 NATO Size: 9098/0919` | `NSN No. 13` |
| 14 | `11` | `I/` |
| 14 | `140 0 -160 0` | `140° — 160°` |
| 15 | `` | `4 Tomy authorized by the` |
| 16 | `11` | `1/ -Do Not Dry Clean` |
| 16 | `TOTAL. ...................................... I00.00%` | `TOTAL, .....ccccccccesceccescveceeeeseeeesens 100.00%` |
| 17 | `..................................... 1 00.00%` | `...cccccccssececeesecveveeeceveuseess 100.00%` |
| 18 | `I - - FRONTRT` | `1 FRONT RT` |
| 19 | `I - - -` | `1` |
| 19 | `(5-thread)` | `(S-thread)` |
| 21 | `- 114` | `— 1/4` |
| 22 | `48` | `AS` |
| 23 | `112` | `| 1/2` |
| 23 | `11 X-Shott` | `3/ X-Short` |
| 23 | `43-3/8` | `43.3/8` |
| 23 | `± 112 :!I` | `+ 1/2 4/` |
| 23 | `oftrousers. 'J/` | `of trousers. 3/` |
| 25 | `` | `101 102 201` |
| 25 | `oftrouser 103` | `of trouser` |
| 25 | `` | `103 203` |
| 25 | `114"` | `1/4”` |
| 25 | `112",` | `1/2”,` |
| 25 | `` | `104 105 204 205 206` |
| 25 | `` | `208 106 209 210` |
| 25 | `` | `107 108 109 110 lil` |
| 28 | `... 11` | `1/` |
| 29 | `A.3` | `A3` |
| 29 | `10-1 OOmL` | `b. C. 10-100mL` |
| 29 | `A.4.1` | `AA4.]` |
| 29 | `A.5.!` | `A.5.1 mo Rage: A.5.2 a. b. c d. e.` |
| 29 | `A.5.2 Soxhlet. a.` | `Soxhlet,` |
| 29 | `(G I 530N)` | `(G1530N)` |
| 29 | `80psi b.` | `80ps1` |
| 29 | `I/lL e.` | `1pL` |
| 30 | `B.I Pennethrin` | `B.1 Permethrin` |
| 30 | `~99.999% BA` | `299.999% B.4` |
| 30 | `BA)` | `B.4)` |
| 31 | `A9)` | `A.9)` |
| 31 | `A8)` | `A.8)` |
| 31 | `45.6037cm2)` | `45.6037cm”)` |
| 31 | `200ng/IlL, [lng/ilL` | `200ng/uL, [1ng/pL` |
| 31 | `of200ng/llL.` | `of 200ng/nL.` |
| 31 | `AS) F.l` | `A.5) F.1` |
| 32 | `` | `22mL` |
| 32 | `` | `0 min` |
| 32 | `o` | `5` |
| 32 | `5 min@ lOOoC` | `@ 100°C` |
| 32 | `F .4). F.2` | `F,4). F,2` |
| 33 | `G.l Ouality` | `G.1 Quality` |
| 33 | `1` | `|` |
| 33 | `1` | `|` |
| 34 | `` | `250 °C` |
| 34 | `` | `275°C` |
| 34 | `` | `280°C` |
| 34 | `GCRunTime` | `1.3 mL/min GC Run Time 10 min` |
| 34 | `` | `3:1` |
| 34 | `` | `G.4.3 Evaluation Procedures.` |
| 35 | `H.I Pennethrin` | `H.1 Permethrin` |
| 35 | `(W!W%): H.I.I Concentration.` | `(W/W%): H.1.1 Concentration,` |
| 35 | `(1I45.6037cm2)` | `(1/45.6037cm?)` |
| 35 | `1.` | `I,` |
| 36 | `l! 3 x` | `1/ 3.x` |
| 36 | `21 I x I x I 21 l!` | `2/ Ix 1x = ‘1 2/ 1/` |
| 37 | `GLIPD 07-14A` | `GL/PD 07-144` |
| 40 | `GLIPD 07-14A Department's` | `GL/PD 07-144 Department’s` |
| 43 | `-----; .... ,,---...1 GUPD` | `GL/PD` |
| 45 | `Buttons • I I I I I I I I` | `GL/PD 07-144` |
| 45 | `GLlPD 07-14A ~Iastic` | `Elastic` |
| 46 | `I , I , I I , , I I I' I I ..... f. "~J-;'" '.;~:...~~~~ ',,: ~~ .*" ... f .• ~ . ...~' • ~'.".",,, . ... ;'tot~ • it L,` | `————oo——` |
| 47 | `~ __` | `NN —— fe av aemre sewn mms amaoeand a roo » > 4` |

## Düzeltme sınıfına girenlerden örnekler

- s.1: `50150` → `50/50`
- s.1: `65125/10 RayonlPara-AramidlNylon` → `65/25/10 Rayon/Para-Aramid/Nylon`
- s.3: `GLlPD 07-l4A` → `GL/PD 07-14A`
- s.5: `GLIPD 07-l4A` → `GL/PD 07-14A`
- s.5: `1057- 1060,2001` → `1057 - 1060, 2001`
- s.6: `GLlPD 07-l4A` → `GL/PD 07-14A`
- s.6: `2xlleft` → `2x1 left`
- s.6: `of2.0` → `of 2.0`
- s.6: `of25.0` → `of 25.0`
- s.6: `50 I,` → `501,`
- s.7: `(± 118)` → `(+ 1/8)`
- s.7: `(± I)` → `(+ 1)`
- s.7: `I-inch` → `1-inch`
- s.7: `118 (+ 1132,` → `1/8 (+1/32,`
- s.7: `II` → `11`
- s.7: `(± 1132)` → `(+ 1/32)`
- s.7: `of(± I` → `of (+ 1`
- s.7: `I12-inch` → `1/2-inch`
- s.7: `I` → `1`
- s.7: `I` → `1`
- s.10: `118-` → `1/8 -`
- s.10: `± 118` → `+ 1/8`
- s.10: `(± 118)` → `(+ 1/8)`
- s.10: `112` → `1/2`
- s.10: `(± 112)` → `(+ 1/2)`
