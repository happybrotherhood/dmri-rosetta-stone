# Study Companion / Çalışma Rehberi

Everything needed to explain and defend this paper: what it claims, why each
choice was made, what every figure and table shows, how the argument was
corrected twice along the way, and the questions an expert will ask.

Bu makaleyi anlatmak ve savunmak için gereken her şey: ne iddia ediyor, her
tercih neden yapıldı, her figür ve tablo neyi gösteriyor, argüman yol boyunca
nasıl iki kez düzeltildi, ve bir uzmanın soracağı sorular.

---

## PART 1 — The claim in one page / Tek sayfada iddia

### EN

Diffusion MRI is analysed with three packages: FSL, MRtrix3, DIPY. When their
outputs differ, the field calls this "software-related variability" and moves on.

This paper shows that phrase is wrong in a specific and correctable way.

**Fitting a diffusion tensor is a regression problem.** You have a signal
measured in many directions, and you fit an ellipsoid to it. Because noise is
not equal across measurements, the fit should be *weighted* — some measurements
count more than others. The question is: where do the weights come from?

There are two answers in use:

| Weights from | Who uses it |
|---|---|
| the **measured** signal | FSL `dtifit --wls`, MRtrix3 `dwi2tensor -iter 0` |
| a **predicted** signal, from a first rough fit | DIPY `WLS`, MRtrix3's default |

**Veraart et al. (2013) already established that the second is more accurate.**
Weighting by the measured signal means the weights are contaminated by the very
noise they are meant to suppress.

Our three findings:

1. **Implementation is not the variable.** FSL and MRtrix3, given the same
   estimator, produce *identical* tensors — r = 1.0000, mean absolute error
   0.0000. Two independent codebases, same answer.
2. **The default is the variable.** MRtrix3 and DIPY ship the recommended
   scheme. FSL ships ordinary least squares, and its `--wls` option implements
   the scheme Veraart advises against. The user cannot see this from the command.
3. **It matters at realistic noise.** At SNR 30 the two schemes are equivalent.
   At SNR 10 the measured-signal scheme carries roughly twice the mean
   diffusivity bias. Real data at high b-values lives closer to SNR 10.

**Bottom line:** changing one flag inside FSL moves FA more than replacing FSL
with a different toolkit entirely.

### TR

Difüzyon MRI üç paketle analiz ediliyor: FSL, MRtrix3, DIPY. Çıktıları
farklılaştığında alan buna "yazılım kaynaklı değişkenlik" deyip geçiyor.

Bu makale o ifadenin belirli ve düzeltilebilir bir şekilde yanlış olduğunu
gösteriyor.

**Difüzyon tensörü uydurmak bir regresyon problemi.** Çok sayıda yönde ölçülmüş
bir sinyalin var, ona bir elipsoit uyduruyorsun. Gürültü ölçümler arasında eşit
olmadığı için uydurma *ağırlıklı* olmalı — bazı ölçümler daha çok saymalı. Soru
şu: ağırlıklar nereden geliyor?

Kullanımda iki cevap var:

| Ağırlık kaynağı | Kim kullanıyor |
|---|---|
| **Ölçülen** sinyal | FSL `dtifit --wls`, MRtrix3 `dwi2tensor -iter 0` |
| **Tahmin edilen** sinyal, ilk kaba fitten | DIPY `WLS`, MRtrix3 varsayılanı |

**Veraart ve ark. (2013) ikincisinin daha doğru olduğunu zaten göstermişti.**
Ölçülen sinyalle ağırlıklandırmak, ağırlıkların tam da bastırmaları gereken
gürültüyle kirlenmesi demek.

Üç bulgumuz:

1. **Değişken uygulama değil.** FSL ve MRtrix3, aynı estimator verildiğinde
   *özdeş* tensör üretiyor — r = 1.0000, MAE = 0.0000. İki bağımsız kod tabanı,
   aynı cevap.
2. **Değişken varsayılan.** MRtrix3 ve DIPY tavsiye edileni dağıtıyor. FSL sıradan
   en küçük kareleri, ve `--wls` seçeneği Veraart'ın kaçınılmasını söylediğini.
   Kullanıcı bunu komuttan göremiyor.
3. **Gerçekçi gürültüde önemli.** SNR 30'da iki şema denk. SNR 10'da
   ölçülen-sinyal şeması yaklaşık iki kat MD yanlılığı taşıyor. Yüksek b-değerli
   gerçek veri SNR 10'a daha yakın.

**Özet:** FSL içinde tek bayrak değiştirmek, FSL'i başka bir araçla tamamen
değiştirmekten daha çok FA kaydırıyor.

---

## PART 2 — How the argument was corrected twice / Argüman nasıl iki kez düzeltildi

This section matters more than it looks. It is the strongest evidence that the
analysis was done carefully, and it is the part to tell in person.

Bu bölüm göründüğünden önemli. Analizin dikkatli yapıldığının en güçlü kanıtı,
ve yüz yüze anlatılacak kısım burası.

### First conclusion, which was wrong / Birinci sonuç, ki yanlıştı

**EN.** Running each toolkit as a user normally would, the result looked clear:
MRtrix3 and DIPY agreed closely (r = 0.9990), FSL sat apart from both
(r = 0.96). The obvious reading was "FSL is the outlier."

Two things did not fit. The FA offset *reversed sign* between the two datasets —
FSL lower on Stanford, higher on Sherbrooke. A genuine implementation difference
should not flip direction with the acquisition.

**The check:** MRtrix3's documentation says `dwi2tensor` performs WLS followed by
**two iterations of reweighting** by default. FSL `--wls` and DIPY do a single
weighted fit. We had been comparing different algorithms and calling the
difference a toolkit effect.

Rerunning MRtrix3 with `-iter 0` reversed the grouping completely: FSL and
MRtrix3 became *identical* (r = 1.0000), and MRtrix3 moved away from DIPY.

**TR.** Her aracı kullanıcının normalde çalıştıracağı gibi çalıştırınca sonuç net
görünüyordu: MRtrix3 ve DIPY yakın (r = 0.9990), FSL ikisinden de uzak (r = 0.96).
Bariz okuma "FSL aykırı" idi.

İki şey uymuyordu. FA kayması iki veri seti arasında **işaret değiştiriyordu** —
Stanford'da FSL düşük, Sherbrooke'ta yüksek. Gerçek bir uygulama farkı edinime
göre yön değiştirmez.

**Kontrol:** MRtrix3 belgesi `dwi2tensor`'ün varsayılanda WLS + **iki yeniden
ağırlıklandırma iterasyonu** yaptığını söylüyor. FSL `--wls` ve DIPY tek ağırlıklı
fit yapıyor. Farklı algoritmaları karşılaştırıp farkı araç etkisi sanmışız.

MRtrix3'ü `-iter 0` ile tekrar çalıştırınca gruplaşma tamamen tersine döndü: FSL
ve MRtrix3 **özdeş** oldu (r = 1.0000), MRtrix3 DIPY'den uzaklaştı.

### Second conclusion, also wrong / İkinci sonuç, o da yanlıştı

**EN.** With the estimator matched, DIPY still differed. We found why — DIPY
weights by a predicted signal, the others by the measured signal — and confirmed
it by giving DIPY measured-signal weights, which cut the disagreement by 98%.

We then tested accuracy on a phantom at SNR 30 and found both schemes recover
the truth to within 0.002 FA. So we wrote: *neither weighting is wrong*.

**That was wrong too.** Veraart et al. (2013) had compared exactly these two
schemes and found the measured-signal one "surprisingly" damaging to accuracy.
Our phantom missed it because SNR 30 is a favourable regime — the whole point is
that the weights are contaminated by noise, so the effect only appears when
there is enough noise.

Rerunning at SNR 20 and 10 reproduced Veraart's result cleanly.

**TR.** Estimator eşitlenince DIPY hâlâ farklıydı. Sebebini bulduk — DIPY tahmin
edilen sinyalle, diğerleri ölçülenle ağırlıklandırıyor — ve DIPY'ye ölçülen-sinyal
ağırlığı vererek doğruladık: fark %98 kapandı.

Sonra SNR 30'da fantomda doğruluğu test ettik, ikisinin de gerçeği 0.002 FA
içinde bulduğunu gördük. Ve yazdık: *hiçbiri yanlış değil*.

**O da yanlıştı.** Veraart ve ark. (2013) tam bu iki şemayı karşılaştırmış ve
ölçülen-sinyalinkini doğruluk açısından "şaşırtıcı" derecede zararlı bulmuştu.
Fantomumuz bunu kaçırdı çünkü SNR 30 iyimser bir rejim — meselenin özü
ağırlıkların gürültüyle kirlenmesi, dolayısıyla etki ancak yeterli gürültü varken
görünür.

SNR 20 ve 10'da tekrar çalıştırınca Veraart'ın sonucu net şekilde çıktı.

> **★ The lesson to state out loud:** both errors came from the same source —
> assuming that two things called by the same name are the same thing. "WLS" in
> three manuals meant three different computations. That is the paper's subject,
> and we walked into it twice before noticing.
>
> **★ Yüksek sesle söylenecek ders:** iki hata da aynı kaynaktan geldi — aynı adla
> anılan iki şeyin aynı şey olduğunu varsaymak. Üç kılavuzdaki "WLS" üç farklı
> hesap demekti. Makalenin konusu bu, ve fark etmeden önce iki kez içine düştük.

---

## PART 3 — Glossary / Terimler sözlüğü

| Term | EN | TR |
|---|---|---|
| **DTI** | Models diffusion in each voxel as an ellipsoid, described by three eigenvalues. | Her vokseldeki difüzyonu üç özdeğerle tanımlanan bir elipsoit olarak modeller. |
| **FA** | Fractional anisotropy: how elongated the ellipsoid is. Bounded 0–1. | Fraksiyonel anizotropi: elipsoidin ne kadar uzadığı. 0–1 arasında. |
| **MD** | Mean diffusivity: average of the three eigenvalues. Must be positive. | Ortalama difüzivite: üç özdeğerin ortalaması. Pozitif olmalı. |
| **OLS** | Ordinary least squares. Every measurement counts equally. FSL's default. | Sıradan en küçük kareler. Her ölçüm eşit sayılır. FSL'in varsayılanı. |
| **WLS** | Weighted least squares. Measurements are weighted, usually by signal. | Ağırlıklı en küçük kareler. Ölçümler, genelde sinyale göre ağırlıklandırılır. |
| **IWLS** | Iteratively reweighted: the fit is repeated, each time reweighting from the previous prediction. MRtrix3's default (2 iterations). | Yinelemeli yeniden ağırlıklandırma: fit tekrarlanır, her seferinde önceki tahminden yeniden ağırlıklandırılır. MRtrix3 varsayılanı (2 iterasyon). |
| **Measured-signal weights** | Weights taken from the observed data. Contaminated by noise. | Ağırlıklar gözlenen veriden alınır. Gürültüyle kirlenir. |
| **Predicted-signal weights** | Weights taken from a model prediction, so less noise-contaminated. | Ağırlıklar model tahmininden alınır, gürültüden daha az etkilenir. |
| **SNR** | Signal-to-noise ratio. Falls as b-value rises. | Sinyal-gürültü oranı. b-değeri arttıkça düşer. |
| **b-value** | Strength of diffusion weighting. Higher b = more diffusion contrast, less signal. | Difüzyon ağırlıklandırmasının gücü. Yüksek b = daha çok kontrast, daha az sinyal. |
| **Shell** | All volumes at one b-value. | Tek bir b-değerindeki tüm hacimler. |
| **Bias / RMSE** | Bias is systematic error; RMSE combines bias and scatter. | Yanlılık sistematik hata; RMSE yanlılık ve saçılmayı birleştirir. |
| **Dice (DSC)** | Overlap between two masks: 0 none, 1 identical. | İki maske arasındaki örtüşme: 0 yok, 1 özdeş. |
| **Phantom** | Synthetic data whose true answer is known by construction. | Gerçek cevabı yapısı gereği bilinen sentetik veri. |

---

## PART 4 — Every methodological choice and why / Her metodolojik tercih ve gerekçesi

Each choice below exists to rule out one alternative explanation.
Aşağıdaki her tercih bir alternatif açıklamayı elemek için var.

| Choice | Rules out / Elediği |
|---|---|
| One shared brain mask for all fits | that the difference is masking |
| One shared volume subset (`--shell`) | that the difference is shell selection |
| No preprocessing | that one toolkit's preprocessing leaked in |
| Physical plausibility filter | that failed fits dominate the correlation |
| Estimator matched (`-iter 0`) | that the difference is the algorithm, not the toolkit |
| DIPY given measured-signal weights | that the cause is anything but the weighting |
| Phantom with known truth | that one scheme is simply wrong |
| Three SNR levels | that the effect is confined to good data |
| Two datasets | that it is a one-off artefact |

### The choice most likely to be challenged / En çok itiraz görecek tercih

**EN — Why no preprocessing?** Because any preprocessing step is itself a
toolkit-specific choice. But note the asymmetry we *cannot* avoid: FSL has no
denoiser. Giving each toolkit "its own" preprocessing would leave FSL fitting
noisier data, and the difference would no longer be attributable to the fit. So
preprocessing is either absent (main analysis) or identical for all three
(sensitivity analysis). Both are reported.

**TR — Neden ön işleme yok?** Çünkü her ön işleme adımı kendisi araca özgü bir
tercih. Ama kaçınamadığımız asimetriye dikkat: FSL'de gürültü giderici yok. Her
araca "kendi" ön işlemesini vermek FSL'i gürültülü veriyle bırakırdı ve fark artık
uydurmaya atfedilemezdi. Bu yüzden ön işleme ya yok (ana analiz) ya da üçü için
aynı (duyarlılık analizi). İkisi de raporlanıyor.

---

## PART 5 — Results in one table / Sonuçlar tek tabloda

| Question | Answer |
|---|---|
| Do implementations differ? | **No.** FSL = MRtrix3 at matched estimator: r = 1.0000, MAE 0.0000 |
| What differs then? | The weighting scheme, and which one each toolkit defaults to |
| Why does DIPY differ? | Predicted-signal weights. Give it measured-signal weights → 98% of the gap closes |
| Is one scheme wrong? | Yes — measured-signal is less accurate (Veraart 2013), confirmed here |
| Does it matter? | At SNR 30 no; at SNR 10 the MD bias is ~2.4× larger |
| How big on real data? | 0.12–0.26 SD of white matter FA |
| Bigger than switching toolkit? | **Yes** — one FSL flag beats replacing FSL entirely |
| Does denoising fix it? | Reduces by ~half, does not close |
| Non-physical fits? | DIPY never produced one; FSL and MRtrix3 did, at rates depending on SNR |

---

## PART 6 — Figures / Figürler

**Figure 1 — Design.** Left: brain extraction, each tool on its own idiomatic
input, giving Dice. Right: tensor fitting, everything held identical and the
estimator varied deliberately. Arms labelled by weight source. *Point:* the two
branches make opposite choices about the input, on purpose.

*Sol: beyin çıkarımı, her araç kendi girdisiyle, Dice veriyor. Sağ: tensör
uydurma, her şey sabit, estimator kasıtlı değiştiriliyor. Kollar ağırlık
kaynağıyla etiketli. Amaç: iki kol girdi konusunda bilerek zıt tercihler yapıyor.*

**Figure 2 — Interface.** The environment at the fitting stage. *Point:* the
command is shown in full and runs unchanged outside the tool — an instrument,
not a black box.

**Figure 3 — Agreement at defaults.** (a) FA maps look the same. (b) scatter:
MRtrix3–DIPY a thin line, FSL pairs fat clouds. (c) Bland–Altman: FSL pairs
offset from zero. *Point:* panel (a) says they agree, (b)–(c) say not quite —
and Table 3 shows this follows the estimator, not the toolkit.

**Figure 4 — Brain masks.** FSL widest, MRtrix3 narrowest, DIPY excludes
ventricles. *Point:* Dice stays above 0.90 despite a 21% volume spread, and the
ordering flips between datasets.

---

## PART 7 — What the contribution is, honestly / Katkı gerçekte ne

### EN

**It is not a discovery.** Every component is documented. MRtrix3 says it
iterates; DIPY cites Chung 2006; FSL's flag is in its help text. Veraart et al.
(2013) established which scheme is more accurate.

**It is a translation gap, measured.** A decade after the estimation question was
settled, the three most used toolkits still ship different answers as defaults,
and users cannot see which they are getting. We quantify what that costs, at
which noise levels, and show it exceeds the effect of changing toolkit.

**Why that is worth publishing:**

1. Nobody has measured it. The magnitudes and the ordering are new.
2. It is directly actionable: report the estimator, not just the toolkit.
3. It reframes "software variability" — a phrase in wide use — as something more
   specific and fixable.
4. It is fully reproducible: open data, open code, one DOI, four commands.

**The honest framing to use out loud:** *"We did not find a new estimator problem.
We found that the field has one, already solved in the literature, still sitting
in the defaults — and we measured what it costs."*

### TR

**Bu bir keşif değil.** Her bileşen belgelenmiş. MRtrix3 iterasyon yaptığını
söylüyor; DIPY Chung 2006'ya atıf veriyor; FSL'in bayrağı yardım metninde.
Veraart ve ark. (2013) hangi şemanın daha doğru olduğunu göstermişti.

**Bu, ölçülmüş bir teori-pratik boşluğu.** Estimation sorusu çözüldükten on yıl
sonra, en çok kullanılan üç araç hâlâ farklı cevapları varsayılan olarak
dağıtıyor ve kullanıcı hangisini aldığını göremiyor. Bunun bedelini, hangi
gürültü seviyelerinde ve araç değiştirmenin etkisini aştığını ölçüyoruz.

**Neden yayımlanmaya değer:**

1. Kimse ölçmemiş. Büyüklükler ve sıralama yeni.
2. Doğrudan eyleme dönüşür: aracı değil estimator'ü raporla.
3. Yaygın kullanılan "yazılım değişkenliği" ifadesini daha belirli ve
   düzeltilebilir bir şeye dönüştürüyor.
4. Tamamen tekrarlanabilir: açık veri, açık kod, tek DOI, dört komut.

**Yüksek sesle kullanılacak dürüst çerçeve:** *"Yeni bir estimator problemi
bulmadık. Alanın, literatürde çoktan çözülmüş bir problemi hâlâ varsayılanlarında
taşıdığını bulduk — ve bedelini ölçtük."*

---

## PART 8 — Questions an expert will ask / Uzmanın soracakları

**Q: Have you read Veraart 2013?**
*EN:* Yes — it is the paper's starting point, cited in the abstract, introduction
and discussion. We reproduce its result for the specific configurations these
toolkits ship, and show the recommendation has not reached the defaults.
*TR:* Evet — makalenin başlangıç noktası, abstract, introduction ve discussion'da
atıflı. Sonucunu bu araçların dağıttığı yapılandırmalar için tekrarlıyor ve
tavsiyenin varsayılanlara ulaşmadığını gösteriyoruz.

**Q: Your reference arm is the scheme the literature discourages. Deliberate?**
*EN:* Yes. It is the arm two toolkits reach when asked for "weighted least
squares", so it is the one users will most often believe they are getting. We
state in the discussion that it is the less accurate of the two.
*TR:* Evet. "Ağırlıklı en küçük kareler" istendiğinde iki aracın vardığı kol bu,
yani kullanıcıların aldıklarını en çok sandıkları kol. Discussion'da ikisinden
daha az doğru olanı olduğunu belirtiyoruz.

**Q: r = 1.0000 — isn't that just a sanity check?**
*EN:* It is, and that is the point. The field's framing assumes implementation is
the variable. Showing it is exactly zero removes that explanation and forces the
question onto the estimator.
*TR:* Öyle, ve mesele de bu. Alanın çerçevesi değişkenin uygulama olduğunu
varsayıyor. Tam sıfır olduğunu göstermek o açıklamayı eliyor ve soruyu
estimator'e mecbur bırakıyor.

**Q: Your phantom uses Gaussian noise; dMRI noise is Rician.**
*EN:* Correct, and it is stated as a limitation. The phantom is a sanity check on
accuracy, not a noise model. It reproduces the expected ordering across three SNR
levels, which is what it was built to test. Rician noise would be the natural
extension.
*TR:* Doğru, ve sınırlama olarak belirtildi. Fantom doğruluk için bir kontrol, bir
gürültü modeli değil. Üç SNR seviyesinde beklenen sıralamayı üretiyor, ki test
etmek için kurulmuştu. Rician gürültü doğal uzantı olur.

**Q: One subject per dataset.**
*EN:* Stated in limitations. The central claim — that two implementations of one
estimator agree — needed no sample, since the answer was exact equality. The
claim it cannot support is how the between-scheme difference varies with
acquisition, and we do not make it.
*TR:* Limitations'ta yazılı. Merkezi iddia — bir estimator'ün iki uygulamasının
uyuştuğu — örneklem gerektirmiyor, çünkü cevap tam eşitlik. Destekleyemeyeceği
iddia, şemalar arası farkın edinime göre nasıl değiştiği; onu da öne sürmüyoruz.

**Q: So which should I use?**
*EN:* Predicted-signal weighting, which MRtrix3 and DIPY apply by default. In FSL
that means being aware that `--wls` is not that scheme. More important than the
choice is recording it.
*TR:* Tahmin-edilen-sinyal ağırlıklandırması — MRtrix3 ve DIPY varsayılanda
uyguluyor. FSL'de bu, `--wls`'in o şema olmadığının farkında olmak demek.
Seçimden daha önemlisi, onu kaydetmek.

---

## Rapid recall / Hızlı hatırlama

| Cue | Say this |
|---|---|
| What is the paper? | Toolkit differences in tensor fitting are estimator differences, not implementation differences — and the recommended estimator is not the default everywhere. |
| Strongest single result | FSL and MRtrix3 agree at r = 1.0000 when the estimator is matched; MAE 0.0000. |
| Most quotable result | One flag inside FSL changes FA more than replacing FSL with another toolkit. |
| Why two datasets? | Replication — and the noisier one showed twice the effect, which the SNR sweep then explained. |
| Why three SNR levels? | The theoretical flaw is noise-dependent, so one SNR cannot test it. SNR 30 hid it. |
| Prior work | Veraart et al. (2013) settled which scheme is better. We show the toolkits have not followed. |
| Novelty, honestly | Not a discovery; a measured translation gap, with magnitudes nobody had reported. |
| Biggest limitation | One subject per dataset; Gaussian not Rician phantom noise; tensor model only. |
