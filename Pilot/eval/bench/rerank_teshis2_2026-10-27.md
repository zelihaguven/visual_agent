# Reranker teşhisi: hit@1'i neden bozuyor?

Aşama 4 rerank sonuçları üzerinden (yeni çağrı yok). 'Doğru parça': soru setindeki beklenen doküman+sayfa.

## qwen3-8b_full

Reranker'a giden metin (soru + parça, bge-v2-m3 tokenizer): 1560 çift, medyan 83 token, en uzun 661; **512'yi aşan (kesilen): 7** (%0). Parça metninde doküman/bölüm başlığı yok (`text`); embedding başlıklı metinle (`embed_text`) yapılıyor.

### bge-reranker-v2-m3 int8 · filtreli: hit@1 kaybı 6, kazancı 4 (kayıpların 6'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q04: doğru parça 1. → 2. · öne alınan `brother-s7300a-00088` (aynı doküman, s.[29], bölüm 'CAUTION'): Turn off the power switch before threading the upper thread. The machine may operate if the treadle is depress
- questions:Q15: doğru parça 1. → 7. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q24: doğru parça 1. → 5. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00078` (aynı doküman, s.[9], bölüm '3.5.5.2 Gimp'): 3.5.5.2 Gimp. The cotton gimp for reinforcing buttonholes shall conform to A-A-50198, soft or glazed finish, T
- questions_ek:Q27: doğru parça 1. → 20. · öne alınan `gl-pd-14-04a-00192` (aynı doküman, s.[24], bölüm '3.11.1.1 Repair of stitch.'): Gauge: raw 1/4 to 5/16-inches from turned edge
- sekil_sorular:N2: doğru parça 1. → 2. · öne alınan `granovsky-1986-00193` (aynı doküman, s.[67], bölüm ''): After they have been dismantled from themachine, cleaned, washed, degreased and dried, the parts are inspected
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q13 (2. → 1.), sekil_sorular:G6 (9. → 1.), sekil_sorular:G7 (6. → 1.)

### bge-reranker-v2-m3 int8 · filtresiz: hit@1 kaybı 10, kazancı 5 (kayıpların 3'i aynı dokümanın başka parçasını öne aldı, 7'i başka dokümanı)

- questions:Q01: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00141` (BAŞKA doküman, s.[19], bölüm '3.11.1 Seams and stitching'): 3.11.1 Seams and stitching. All seams shall be consistent and exhibit a uniform appearance and confOlm to the 
- questions:Q02: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00178` (BAŞKA doküman, s.[22, 23], bölüm '3.11.1 Seams and stitching'): 3.11.1 Seams and stitching. All seams shall be consistent and exhibit a uniform appearance and conform to the 
- questions:Q03: doğru parça 1. → 4. · öne alınan `gl-pd-07-14a-00092` (BAŞKA doküman, s.[11], bölüm '3.7.7 Pockets and flaps'): Buttonholes. The buttonholes shall be eyelet-end tapered bar type worked over gimp for the fly, back hip welt 
- questions:Q15: doğru parça 1. → 7. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q22: doğru parça 1. → 2. · öne alınan `brother-s7300b-00463` (BAŞKA doküman, s.[106], bölüm 'Feed mechanism-related errors'): Code: E210 | Cause: Feed motor origin is not detected when power is turned on. | Remedy: ・Turn off the power a
- questions_ek:Q24: doğru parça 1. → 5. · öne alınan `brother-s7300b-00513` (BAŞKA doküman, s.[112], bölüm '14. TROUBLESHOOTING'): Problem: 10 | Problem: Upper and lower threads are breaking. 0471M | Possible cause: ・ Is the needle tip bent?
- questions_ek:Q25: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00089` (BAŞKA doküman, s.[9, 10], bölüm '3.5.6 Thread (Types II and III only, all'): TABLE II. Thread requirements, Types II and III only. 1/ Needle & Bobbin/Looper shall use same Tex size thread
- questions_ek:Q27: doğru parça 1. → 13. · öne alınan `strickland-1956-00136` (BAŞKA doküman, s.[81], bölüm ''): 1. Run three or four fine, permanent gathering threads through the single thickness of the placket turnback ju
- sekil_sorular:G3: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00221` (aynı doküman, s.[26], bölüm '3.11.3 Bar-tacks and back-tacks'): Bar-tack or back-tack placement: slide fastener) Upper sleeve pockets a. Loop tape 2/ | # of Bar- tacks per ga
- sekil_sorular:N2: doğru parça 1. → 2. · öne alınan `granovsky-1986-00193` (aynı doküman, s.[67], bölüm ''): After they have been dismantled from themachine, cleaned, washed, degreased and dried, the parts are inspected
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q11 (2. → 1.), questions:Q13 (2. → 1.), sekil_sorular:G6 (9. → 1.), sekil_sorular:G7 (6. → 1.)

### jina-reranker-v2-base-multilingual · filtreli: hit@1 kaybı 6, kazancı 3 (kayıpların 6'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q05: doğru parça 1. → 2. · öne alınan `brother-s7300b-00507` (aynı doküman, s.[110], bölüm '14. TROUBLESHOOTING'): Problem: 5 | Problem: Skipped stitches at sewing start Thread unraveling at sewing start. 0749M | Possible cau
- questions:Q15: doğru parça 1. → 2. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q24: doğru parça 1. → 3. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 4. · öne alınan `gl-pd-07-14a-00078` (aynı doküman, s.[9], bölüm '3.5.5.2 Gimp'): 3.5.5.2 Gimp. The cotton gimp for reinforcing buttonholes shall conform to A-A-50198, soft or glazed finish, T
- questions_ek:Q27: doğru parça 1. → 8. · öne alınan `gl-pd-14-04a-00109` (aynı doküman, s.[12], bölüm '3.7.7.2 Chest pocket flaps'): 3.7.7.2 Chest pocket flaps. The chest pocket flaps shall finish 1-1/2 (± 1/8) inches in width and be of suffic
- sekil_sorular:N3: doğru parça 1. → 2. · öne alınan `granovsky-1986-00820` (aynı doküman, s.[50], bölüm ''): Otomatik şekil açıklaması (model üretimi, kaynak metni değil): The figure shows a hierarchical structure of di
- düzelttikleri: questions:Q03 (3. → 1.), questions:Q06 (3. → 1.), sekil_sorular:G6 (9. → 1.)

### jina-reranker-v2-base-multilingual · filtresiz: hit@1 kaybı 11, kazancı 3 (kayıpların 4'i aynı dokümanın başka parçasını öne aldı, 7'i başka dokümanı)

- questions:Q02: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00178` (BAŞKA doküman, s.[22, 23], bölüm '3.11.1 Seams and stitching'): 3.11.1 Seams and stitching. All seams shall be consistent and exhibit a uniform appearance and conform to the 
- questions:Q04: doğru parça 1. → 2. · öne alınan `brother-s7300b-00502` (BAŞKA doküman, s.[109], bölüm '14. TROUBLESHOOTING'): Problem: 1 | Problem: Upper thread is not tight. 0573M | Possible cause: ・ Is the upper thread tension too wea
- questions:Q05: doğru parça 1. → 3. · öne alınan `brother-s7300b-00507` (aynı doküman, s.[110], bölüm '14. TROUBLESHOOTING'): Problem: 5 | Problem: Skipped stitches at sewing start Thread unraveling at sewing start. 0749M | Possible cau
- questions:Q14: doğru parça 1. → 2. · öne alınan `brother-s7300a-00409` (aynı doküman, s.[98], bölüm 'Switch-related errors'): Code: E050 | Cause: Machine head is detected as being tilted back when start sewing. | Remedy: ・Turn off the p
- questions:Q15: doğru parça 1. → 2. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions:Q16: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00092` (BAŞKA doküman, s.[11], bölüm '3.7.7 Pockets and flaps'): Buttonholes. The buttonholes shall be eyelet-end tapered bar type worked over gimp for the fly, back hip welt 
- questions_ek:Q22: doğru parça 1. → 3. · öne alınan `brother-s7300b-00463` (BAŞKA doküman, s.[106], bölüm 'Feed mechanism-related errors'): Code: E210 | Cause: Feed motor origin is not detected when power is turned on. | Remedy: ・Turn off the power a
- questions_ek:Q24: doğru parça 1. → 4. · öne alınan `brother-s7300b-00513` (BAŞKA doküman, s.[112], bölüm '14. TROUBLESHOOTING'): Problem: 10 | Problem: Upper and lower threads are breaking. 0471M | Possible cause: ・ Is the needle tip bent?
- questions_ek:Q25: doğru parça 1. → 4. · öne alınan `gl-pd-14-04a-00089` (BAŞKA doküman, s.[9, 10], bölüm '3.5.6 Thread (Types II and III only, all'): TABLE II. Thread requirements, Types II and III only. 1/ Needle & Bobbin/Looper shall use same Tex size thread
- questions_ek:Q27: doğru parça 1. → 6. · öne alınan `strickland-1956-00125` (BAŞKA doküman, s.[77], bölüm ''): Turn seams along belt length to wrong side, baste and steam. Fold belt lengthwise through center, allowing out
- sekil_sorular:N3: doğru parça 1. → 2. · öne alınan `granovsky-1986-00820` (aynı doküman, s.[50], bölüm ''): Otomatik şekil açıklaması (model üretimi, kaynak metni değil): The figure shows a hierarchical structure of di
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q11 (2. → 1.), sekil_sorular:G6 (9. → 1.)

### qwen3-reranker-8b · filtreli: hit@1 kaybı 3, kazancı 2 (kayıpların 3'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q15: doğru parça 1. → 6. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 3. · öne alınan `gl-pd-07-14a-00076` (aynı doküman, s.[9], bölüm '3.5.5.1 Thread (Type II trouser)'): Component area: Button attachment | Tlu·ead· specification: A-A-50195 (Soft or Bonded) A-A-55195, Type I A-A-5
- sekil_sorular:G2: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00090` (aynı doküman, s.[10], bölüm '3.6 Design'): 3.6 Design. The coat design for Style A-Unisex and Style B-Female has a single-breasted front with a slide fas
- düzelttikleri: questions:Q12 (4. → 1.), questions:Q13 (2. → 1.)

### qwen3-reranker-8b · filtresiz: hit@1 kaybı 5, kazancı 2 (kayıpların 2'i aynı dokümanın başka parçasını öne aldı, 3'i başka dokümanı)

- questions:Q15: doğru parça 1. → 6. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q19: doğru parça 1. → 2. · öne alınan `brother-s7300b-00438` (BAŞKA doküman, s.[105], bölüm 'Switch-related errors'): Code: E051 | Cause: Machine head is detected as being tilted back during sewing. | Remedy: Turn off the power 
- questions_ek:Q25: doğru parça 1. → 3. · öne alınan `gl-pd-14-04a-00089` (BAŞKA doküman, s.[9, 10], bölüm '3.5.6 Thread (Types II and III only, all'): TABLE II. Thread requirements, Types II and III only. 1/ Needle & Bobbin/Looper shall use same Tex size thread
- sekil_sorular:G2: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00090` (aynı doküman, s.[10], bölüm '3.6 Design'): 3.6 Design. The coat design for Style A-Unisex and Style B-Female has a single-breasted front with a slide fas
- sekil_sorular:G8: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00564` (BAŞKA doküman, s.[56], bölüm '6.8 Subject term (key word) listing.'): Otomatik şekil açıklaması (model üretimi, kaynak metni değil): The figure shows a technical drawing of a garme
- düzelttikleri: questions:Q11 (2. → 1.), questions:Q12 (8. → 1.)

## bge-m3-local-bm25_full

Reranker'a giden metin (soru + parça, bge-v2-m3 tokenizer): 1560 çift, medyan 117 token, en uzun 665; **512'yi aşan (kesilen): 12** (%1). Parça metninde doküman/bölüm başlığı yok (`text`); embedding başlıklı metinle (`embed_text`) yapılıyor.

### bge-reranker-v2-m3 int8 · filtreli: hit@1 kaybı 4, kazancı 4 (kayıpların 4'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q04: doğru parça 1. → 2. · öne alınan `brother-s7300a-00088` (aynı doküman, s.[29], bölüm 'CAUTION'): Turn off the power switch before threading the upper thread. The machine may operate if the treadle is depress
- questions:Q15: doğru parça 1. → 4. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q24: doğru parça 1. → 6. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00078` (aynı doküman, s.[9], bölüm '3.5.5.2 Gimp'): 3.5.5.2 Gimp. The cotton gimp for reinforcing buttonholes shall conform to A-A-50198, soft or glazed finish, T
- düzelttikleri: questions:Q06 (3. → 1.), sekil_sorular:G1 (3. → 1.), sekil_sorular:G2 (2. → 1.), sekil_sorular:G7 (3. → 1.)

### bge-reranker-v2-m3 int8 · filtresiz: hit@1 kaybı 6, kazancı 4 (kayıpların 3'i aynı dokümanın başka parçasını öne aldı, 3'i başka dokümanı)

- questions:Q04: doğru parça 1. → 4. · öne alınan `brother-s7300a-00088` (aynı doküman, s.[29], bölüm 'CAUTION'): Turn off the power switch before threading the upper thread. The machine may operate if the treadle is depress
- questions:Q12: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00178` (BAŞKA doküman, s.[22, 23], bölüm '3.11.1 Seams and stitching'): 3.11.1 Seams and stitching. All seams shall be consistent and exhibit a uniform appearance and conform to the 
- questions:Q13: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00142` (BAŞKA doküman, s.[19], bölüm '3.11.1 Seams and stitching'): Buttons shall be attached with 16 stitches per button. The sewn eyelets for the bellows pockets shall have a m
- questions:Q15: doğru parça 1. → 4. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q22: doğru parça 1. → 2. · öne alınan `brother-s7300b-00463` (BAŞKA doküman, s.[106], bölüm 'Feed mechanism-related errors'): Code: E210 | Cause: Feed motor origin is not detected when power is turned on. | Remedy: ・Turn off the power a
- questions_ek:Q24: doğru parça 1. → 3. · öne alınan `brother-s7300a-00377` (aynı doküman, s.[82], bölüm '3. Checking'): Replace the needle if it is bent or if the tip is broken. Check that the upper threads have been threaded corr
- düzelttikleri: questions:Q06 (3. → 1.), sekil_sorular:G1 (3. → 1.), sekil_sorular:G2 (2. → 1.), sekil_sorular:G7 (3. → 1.)

### jina-reranker-v2-base-multilingual · filtreli: hit@1 kaybı 6, kazancı 4 (kayıpların 6'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q05: doğru parça 1. → 2. · öne alınan `brother-s7300b-00507` (aynı doküman, s.[110], bölüm '14. TROUBLESHOOTING'): Problem: 5 | Problem: Skipped stitches at sewing start Thread unraveling at sewing start. 0749M | Possible cau
- questions:Q12: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00165` (aynı doküman, s.[21], bölüm 'OLlPD 07-14A'): Seam Placement: Overedge back edges of left fly lining and buttonhole fly | Seam type: EFd-l | Gage: 3/16 to 1
- questions:Q13: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00098` (aynı doküman, s.[11], bölüm '3.7.4.1 Upper sleeve pocket'): 3.7.4.1 Upper sleeve pocket. The sleeve pocket shall have a bellows at front, back and bottom with a slide fas
- questions:Q15: doğru parça 1. → 2. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q24: doğru parça 1. → 2. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 4. · öne alınan `gl-pd-07-14a-00078` (aynı doküman, s.[9], bölüm '3.5.5.2 Gimp'): 3.5.5.2 Gimp. The cotton gimp for reinforcing buttonholes shall conform to A-A-50198, soft or glazed finish, T
- düzelttikleri: questions:Q03 (3. → 1.), questions:Q06 (3. → 1.), sekil_sorular:G2 (2. → 1.), sekil_sorular:N2 (2. → 1.)

### jina-reranker-v2-base-multilingual · filtresiz: hit@1 kaybı 7, kazancı 4 (kayıpların 2'i aynı dokümanın başka parçasını öne aldı, 5'i başka dokümanı)

- questions:Q04: doğru parça 1. → 2. · öne alınan `brother-s7300b-00502` (BAŞKA doküman, s.[109], bölüm '14. TROUBLESHOOTING'): Problem: 1 | Problem: Upper thread is not tight. 0573M | Possible cause: ・ Is the upper thread tension too wea
- questions:Q05: doğru parça 1. → 3. · öne alınan `brother-s7300b-00507` (aynı doküman, s.[110], bölüm '14. TROUBLESHOOTING'): Problem: 5 | Problem: Skipped stitches at sewing start Thread unraveling at sewing start. 0749M | Possible cau
- questions:Q12: doğru parça 1. → 3. · öne alınan `gl-pd-14-04a-00178` (BAŞKA doküman, s.[22, 23], bölüm '3.11.1 Seams and stitching'): 3.11.1 Seams and stitching. All seams shall be consistent and exhibit a uniform appearance and conform to the 
- questions:Q13: doğru parça 1. → 3. · öne alınan `gl-pd-07-14a-00093` (BAŞKA doküman, s.[12], bölüm '3.7.10 Eyelets'): 3.7.10 Eyelets. The sewn-in eyelets for the bellows pockets shall have a minimum of 16 stitches each with a 3/
- questions:Q15: doğru parça 1. → 2. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q22: doğru parça 1. → 2. · öne alınan `brother-s7300b-00463` (BAŞKA doküman, s.[106], bölüm 'Feed mechanism-related errors'): Code: E210 | Cause: Feed motor origin is not detected when power is turned on. | Remedy: ・Turn off the power a
- questions_ek:Q24: doğru parça 1. → 2. · öne alınan `brother-s7300b-00527` (BAŞKA doküman, s.[114], bölüm '14. TROUBLESHOOTING'): 23 | Broken needle 0469M | Possible cause: ・ Is the material being pushed or pulled with excessive force durin
- düzelttikleri: questions:Q03 (11. → 1.), questions:Q06 (3. → 1.), sekil_sorular:G2 (2. → 1.), sekil_sorular:N2 (2. → 1.)

### qwen3-reranker-8b · filtreli: hit@1 kaybı 2, kazancı 2 (kayıpların 2'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q15: doğru parça 1. → 5. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 3. · öne alınan `gl-pd-07-14a-00078` (aynı doküman, s.[9], bölüm '3.5.5.2 Gimp'): 3.5.5.2 Gimp. The cotton gimp for reinforcing buttonholes shall conform to A-A-50198, soft or glazed finish, T
- düzelttikleri: sekil_sorular:G1 (3. → 1.), sekil_sorular:N2 (2. → 1.)

### qwen3-reranker-8b · filtresiz: hit@1 kaybı 1, kazancı 2 (kayıpların 1'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q15: doğru parça 1. → 5. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- düzelttikleri: sekil_sorular:G1 (3. → 1.), sekil_sorular:N2 (2. → 1.)

## te3-large_full

Reranker'a giden metin (soru + parça, bge-v2-m3 tokenizer): 1560 çift, medyan 98 token, en uzun 601; **512'yi aşan (kesilen): 5** (%0). Parça metninde doküman/bölüm başlığı yok (`text`); embedding başlıklı metinle (`embed_text`) yapılıyor.

### bge-reranker-v2-m3 int8 · filtreli: hit@1 kaybı 6, kazancı 4 (kayıpların 6'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q04: doğru parça 1. → 2. · öne alınan `brother-s7300a-00088` (aynı doküman, s.[29], bölüm 'CAUTION'): Turn off the power switch before threading the upper thread. The machine may operate if the treadle is depress
- questions:Q15: doğru parça 1. → 4. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q24: doğru parça 1. → 8. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00078` (aynı doküman, s.[9], bölüm '3.5.5.2 Gimp'): 3.5.5.2 Gimp. The cotton gimp for reinforcing buttonholes shall conform to A-A-50198, soft or glazed finish, T
- sekil_sorular:G3: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00216` (aynı doküman, s.[26], bölüm '3.11.3 Bar-tacks and back-tacks'): Bar-tack or back-tack placement: Pencil pocket a. Top (left, center, right) | Size of tack (inches): 5/8 | Sti
- sekil_sorular:N2: doğru parça 1. → 2. · öne alınan `granovsky-1986-00842` (aynı doküman, s.[79], bölüm ''): Otomatik şekil açıklaması (model üretimi, kaynak metni değil): The figure shows various stages of a textile ma
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q12 (5. → 1.), questions:Q13 (2. → 1.), sekil_sorular:G7 (6. → 1.)

### bge-reranker-v2-m3 int8 · filtresiz: hit@1 kaybı 8, kazancı 4 (kayıpların 3'i aynı dokümanın başka parçasını öne aldı, 5'i başka dokümanı)

- questions:Q01: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00141` (BAŞKA doküman, s.[19], bölüm '3.11.1 Seams and stitching'): 3.11.1 Seams and stitching. All seams shall be consistent and exhibit a uniform appearance and confOlm to the 
- questions:Q04: doğru parça 1. → 2. · öne alınan `brother-s7300b-00502` (BAŞKA doküman, s.[109], bölüm '14. TROUBLESHOOTING'): Problem: 1 | Problem: Upper thread is not tight. 0573M | Possible cause: ・ Is the upper thread tension too wea
- questions:Q15: doğru parça 1. → 4. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions:Q16: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00092` (BAŞKA doküman, s.[11], bölüm '3.7.7 Pockets and flaps'): Buttonholes. The buttonholes shall be eyelet-end tapered bar type worked over gimp for the fly, back hip welt 
- questions_ek:Q22: doğru parça 1. → 2. · öne alınan `brother-s7300b-00463` (BAŞKA doküman, s.[106], bölüm 'Feed mechanism-related errors'): Code: E210 | Cause: Feed motor origin is not detected when power is turned on. | Remedy: ・Turn off the power a
- questions_ek:Q24: doğru parça 1. → 3. · öne alınan `brother-s7300a-00478` (aynı doküman, s.[104], bölüm '14. TROUBLESHOOTING'): Problem: 10 | Problem: Upper and lower threads are breaking. 0471M | Possible cause: ・ Is the needle tip bent?
- questions_ek:Q25: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00089` (BAŞKA doküman, s.[9, 10], bölüm '3.5.6 Thread (Types II and III only, all'): TABLE II. Thread requirements, Types II and III only. 1/ Needle & Bobbin/Looper shall use same Tex size thread
- sekil_sorular:N2: doğru parça 1. → 2. · öne alınan `granovsky-1986-00842` (aynı doküman, s.[79], bölüm ''): Otomatik şekil açıklaması (model üretimi, kaynak metni değil): The figure shows various stages of a textile ma
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q11 (11. → 1.), sekil_sorular:G1 (5. → 1.), sekil_sorular:G7 (6. → 1.)

### jina-reranker-v2-base-multilingual · filtreli: hit@1 kaybı 6, kazancı 2 (kayıpların 6'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q05: doğru parça 1. → 2. · öne alınan `brother-s7300b-00507` (aynı doküman, s.[110], bölüm '14. TROUBLESHOOTING'): Problem: 5 | Problem: Skipped stitches at sewing start Thread unraveling at sewing start. 0749M | Possible cau
- questions:Q15: doğru parça 1. → 4. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q24: doğru parça 1. → 3. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 4. · öne alınan `gl-pd-07-14a-00078` (aynı doküman, s.[9], bölüm '3.5.5.2 Gimp'): 3.5.5.2 Gimp. The cotton gimp for reinforcing buttonholes shall conform to A-A-50198, soft or glazed finish, T
- sekil_sorular:G1: doğru parça 1. → 4. · öne alınan `gl-pd-14-04a-00100` (aynı doküman, s.[11], bölüm '3.7.4.3 Eyelets'): 3.7.4.3 Eyelets. The sewn-in eyelets for the sleeve pocket bellows shall have a 1/4-inch (± 1/16) diameter fin
- sekil_sorular:N3: doğru parça 1. → 2. · öne alınan `granovsky-1986-00820` (aynı doküman, s.[50], bölüm ''): Otomatik şekil açıklaması (model üretimi, kaynak metni değil): The figure shows a hierarchical structure of di
- düzelttikleri: questions:Q03 (3. → 1.), questions:Q06 (3. → 1.)

### jina-reranker-v2-base-multilingual · filtresiz: hit@1 kaybı 9, kazancı 3 (kayıpların 3'i aynı dokümanın başka parçasını öne aldı, 6'i başka dokümanı)

- questions:Q04: doğru parça 1. → 2. · öne alınan `brother-s7300b-00502` (BAŞKA doküman, s.[109], bölüm '14. TROUBLESHOOTING'): Problem: 1 | Problem: Upper thread is not tight. 0573M | Possible cause: ・ Is the upper thread tension too wea
- questions:Q05: doğru parça 1. → 3. · öne alınan `brother-s7300b-00507` (aynı doküman, s.[110], bölüm '14. TROUBLESHOOTING'): Problem: 5 | Problem: Skipped stitches at sewing start Thread unraveling at sewing start. 0749M | Possible cau
- questions:Q15: doğru parça 1. → 4. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions:Q16: doğru parça 1. → 2. · öne alınan `gl-pd-07-14a-00092` (BAŞKA doküman, s.[11], bölüm '3.7.7 Pockets and flaps'): Buttonholes. The buttonholes shall be eyelet-end tapered bar type worked over gimp for the fly, back hip welt 
- questions_ek:Q22: doğru parça 1. → 2. · öne alınan `brother-s7300b-00463` (BAŞKA doküman, s.[106], bölüm 'Feed mechanism-related errors'): Code: E210 | Cause: Feed motor origin is not detected when power is turned on. | Remedy: ・Turn off the power a
- questions_ek:Q24: doğru parça 1. → 4. · öne alınan `brother-s7300b-00513` (BAŞKA doküman, s.[112], bölüm '14. TROUBLESHOOTING'): Problem: 10 | Problem: Upper and lower threads are breaking. 0471M | Possible cause: ・ Is the needle tip bent?
- questions_ek:Q25: doğru parça 1. → 4. · öne alınan `gl-pd-14-04a-00089` (BAŞKA doküman, s.[9, 10], bölüm '3.5.6 Thread (Types II and III only, all'): TABLE II. Thread requirements, Types II and III only. 1/ Needle & Bobbin/Looper shall use same Tex size thread
- sekil_sorular:G8: doğru parça 1. → 2. · öne alınan `strickland-1956-00287` (BAŞKA doküman, s.[151], bölüm ''): 1. Crotch measurement may be taken in either of two ways. Pin a tape tightly around the waist from which the m
- sekil_sorular:N3: doğru parça 1. → 2. · öne alınan `granovsky-1986-00820` (aynı doküman, s.[50], bölüm ''): Otomatik şekil açıklaması (model üretimi, kaynak metni değil): The figure shows a hierarchical structure of di
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q11 (11. → 1.), sekil_sorular:G1 (5. → 1.)

### qwen3-reranker-8b · filtreli: hit@1 kaybı 3, kazancı 4 (kayıpların 3'i aynı dokümanın başka parçasını öne aldı, 0'i başka dokümanı)

- questions:Q15: doğru parça 1. → 2. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 3. · öne alınan `gl-pd-07-14a-00076` (aynı doküman, s.[9], bölüm '3.5.5.1 Thread (Type II trouser)'): Component area: Button attachment | Tlu·ead· specification: A-A-50195 (Soft or Bonded) A-A-55195, Type I A-A-5
- sekil_sorular:G2: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00090` (aynı doküman, s.[10], bölüm '3.6 Design'): 3.6 Design. The coat design for Style A-Unisex and Style B-Female has a single-breasted front with a slide fas
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q12 (5. → 1.), questions:Q13 (2. → 1.), questions_ek:Q27 (3. → 1.)

### qwen3-reranker-8b · filtresiz: hit@1 kaybı 4, kazancı 3 (kayıpların 2'i aynı dokümanın başka parçasını öne aldı, 2'i başka dokümanı)

- questions:Q15: doğru parça 1. → 2. · öne alınan `brother-s7300a-00318` (aynı doküman, s.[68], bölüm '6-10-1. Hand switch function setting'): At the hand switch setting screen, select "Correction 2nd pitch ratio". Use the + or + key to set the ratio (1
- questions_ek:Q25: doğru parça 1. → 3. · öne alınan `gl-pd-14-04a-00089` (BAŞKA doküman, s.[9, 10], bölüm '3.5.6 Thread (Types II and III only, all'): TABLE II. Thread requirements, Types II and III only. 1/ Needle & Bobbin/Looper shall use same Tex size thread
- sekil_sorular:G2: doğru parça 1. → 2. · öne alınan `gl-pd-14-04a-00090` (aynı doküman, s.[10], bölüm '3.6 Design'): 3.6 Design. The coat design for Style A-Unisex and Style B-Female has a single-breasted front with a slide fas
- sekil_sorular:G8: doğru parça 1. → 2. · öne alınan `strickland-1956-00290` (BAŞKA doküman, s.[152, 153], bölüm ''): Waist and crotch seams. Turn up hem at bottom of leg. Pin pattern pieces together along side seams to the posi
- düzelttikleri: questions:Q06 (3. → 1.), questions:Q11 (11. → 1.), sekil_sorular:G1 (5. → 1.)

