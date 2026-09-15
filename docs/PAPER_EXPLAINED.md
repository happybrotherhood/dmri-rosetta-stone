# Study Companion / Çalışma Rehberi

Everything needed to explain and defend this paper: what it claims, why each
choice was made, what every table and figure shows, how the argument was
corrected four times, and the questions an expert will ask.

Bu makaleyi anlatmak ve savunmak için gereken her şey: ne iddia ediyor, her
tercih neden yapıldı, her tablo ve figür neyi gösteriyor, argüman dört kez nasıl
düzeltildi, ve bir uzmanın soracağı sorular.

---

## PART 1 — The claim in one page / Tek sayfada iddia

### EN

Diffusion MRI is analysed with three packages: FSL, MRtrix3 and DIPY. When their
outputs differ, the field calls this "software-related variability" and moves on.

This paper shows that phrase is wrong in a specific and correctable way.

**Fitting a diffusion tensor is a regression problem.** A signal is measured in
many directions and an ellipsoid is fitted to it. Because the logarithm distorts
the noise, the fit should be *weighted*. The question is where the weights come
from, and there are two answers in use:

| Weights from | Who uses it |
|---|---|
| the **measured** signal | FSL `dtifit --wls`, MRtrix3 `dwi2tensor -iter 0` |
| a **predicted** signal, from a first rough fit | DIPY `WLS`, MRtrix3's default |

**Veraart et al. (2013) already established that the second is more accurate in
MD.** Weighting by the measured signal means the weights are contaminated by the
very noise they are meant to suppress.

Three findings:

1. **Implementation is not the variable.** FSL and MRtrix3, given the same
   estimator, produce *identical* tensors: r = 1.0000, mean absolute error below
   0.0001. Two independent codebases, same answer.
2. **The default is the variable.** MRtrix3 and DIPY ship the recommended
   scheme. FSL ships ordinary least squares, and its `--wls` option implements
   the scheme Veraart advises against. The user cannot see this from the command.
3. **It costs something real.** In the phantom, measured-signal weighting
   underestimates MD by 0.054 µm²/ms at SNR 10, while the other linear fits stay
   within 0.007 of truth. On simulations of both real protocols its MD bias is
   the largest in every condition. On real data, one flag inside FSL changes FA
   more than replacing FSL with another toolkit at a matched estimator.

### TR

Difüzyon MRI üç paketle analiz ediliyor: FSL, MRtrix3 ve DIPY. Çıktıları
farklılaştığında alan buna "yazılım kaynaklı değişkenlik" deyip geçiyor.

Bu makale o ifadenin belirli ve düzeltilebilir bir şekilde yanlış olduğunu
gösteriyor.

**Difüzyon tensörü uydurmak bir regresyon problemi.** Çok sayıda yönde ölçülmüş
bir sinyale elipsoit uyduruluyor. Logaritma gürültüyü bozduğu için uydurma
*ağırlıklı* olmalı. Soru şu: ağırlıklar nereden geliyor? Kullanımda iki cevap
var: ölçülen sinyal (FSL `--wls`, MRtrix3 `-iter 0`) ya da ilk kaba fitten
tahmin edilen sinyal (DIPY, MRtrix3 varsayılanı).

**Veraart ve ark. (2013) ikincisinin MD'de daha doğru olduğunu zaten
göstermişti.** Ölçülen sinyalle ağırlıklandırmak, ağırlıkların tam da
bastırmaları gereken gürültüyle kirlenmesi demek.

Üç bulgu:

1. **Değişken uygulama değil.** Aynı estimator verildiğinde FSL ve MRtrix3
   *özdeş* tensör üretiyor: r = 1.0000, ortalama mutlak hata 0.0001'in altında.
2. **Değişken varsayılan.** MRtrix3 ve DIPY tavsiye edileni dağıtıyor. FSL
   sıradan en küçük kareleri, `--wls` seçeneği de Veraart'ın kaçınılmasını
   söylediği şemayı uyguluyor. Kullanıcı bunu komuttan göremiyor.
3. **Bedeli gerçek.** Fantomda SNR 10'da ölçülen-sinyal ağırlıklandırma MD'yi
   0.054 µm²/ms düşük tahmin ediyor; diğer doğrusal fitler gerçeğin 0.007
   yakınında kalıyor. İki gerçek protokolün simülasyonunda MD yanlılığı her
   koşulda en büyük. Gerçek veride ise FSL içinde tek bayrak değiştirmek, FSL'i
   aynı estimator'le başka bir araçla değiştirmekten daha çok FA kaydırıyor.

---

## PART 2 — How the argument was corrected four times / Argüman dört kez nasıl düzeltildi

### EN

This section matters more than it looks. It is the strongest evidence that the
analysis was checked rather than assumed, and it is the part to tell in person.

**First correction: "FSL is the outlier" was wrong.** MRtrix3's `dwi2tensor`
performs weighted least squares followed by **two reweighting iterations** by
default. We had compared different algorithms and called the difference a
toolkit effect. Constrained to one weighted fit (`-iter 0`), MRtrix3 and FSL
became identical and MRtrix3 moved away from DIPY. *Found because the FA
difference reversed sign between the two datasets.*

**Second correction: "neither weighting is wrong" was wrong.** That rested on a
phantom at SNR 30. The objection to measured-signal weighting is that the
weights are correlated with the noise, so the bias scales as 1/SNR² — and SNR 30
is where it is smallest. At SNR 20 and 10 the effect appeared, and the MD bias
grew 2.3-fold and 8.3-fold, against 2.25 and 9.00 predicted by the mechanism.
*Found because the result contradicted an established finding.*

**Third correction: the simplified simulation, not the data, was the problem.**
It predicted the opposite FA sign on Sherbrooke, and we reported that as
unexplained. Its tensors had a fixed MD of 0.70 µm²/ms (the real median is
0.594), one symmetric shape, random orientation and uniform S₀ and σ. No single
idealisation reverses the sign under every rule; all four together do. With each
voxel's own tensor, S₀ and noise level, noise reproduces the observed sign.

**Fourth correction: we had been selecting on the outcome.** The first version of
that analysis dropped a simulated voxel when the measured-signal fit came out
non-physical — exactly where the offset is largest — and the voxel set had
already been chosen the same way. It made noise look as though it explained only
60% of the Sherbrooke FA offset. With voxels and bins taken from the DIPY fit
alone, and non-physical fits handled identically in observed and simulated data,
noise reproduces 89–106% of it. *Found by an independent code review.*

> **★ What the four have in common.** Every one came from assuming that two
> things with the same name were the same thing: "WLS" in three manuals meant
> three computations; "the phantom test" at one SNR meant something different
> from a test of a noise-dependent effect; "the simulation" meant an
> idealisation; "the voxels" meant a set already filtered by the arm under test.
> That is the paper's own subject, and we walked into it four times.

### TR

Bu bölüm göründüğünden önemli. Analizin varsayılmak yerine kontrol edildiğinin
en güçlü kanıtı, ve yüz yüze anlatılacak kısım burası.

**Birinci düzeltme: "FSL aykırı" yanlıştı.** MRtrix3 varsayılanda ağırlıklı en
küçük kareler ve ardından **iki yeniden ağırlıklandırma** yapıyor. Farklı
algoritmaları karşılaştırıp farkı araca atfetmişiz. `-iter 0` ile MRtrix3 ve FSL
özdeş oldu, MRtrix3 DIPY'den uzaklaştı. *Fark edilme sebebi: FA farkı iki veri
seti arasında işaret değiştiriyordu.*

**İkinci düzeltme: "hiçbir ağırlıklandırma yanlış değil" yanlıştı.** Bu, SNR
30'daki bir fantoma dayanıyordu. Oysa kusur gürültüye bağlı ve yanlılık 1/SNR²
ile ölçekleniyor; SNR 30 tam da en küçük olduğu yer. SNR 20 ve 10'da etki
göründü: MD yanlılığı 2.3 ve 8.3 kat büyüdü, mekanizmanın öngördüğü 2.25 ve
9.00'a karşı. *Fark edilme sebebi: yerleşik bir bulguyla çelişiyorduk.*

**Üçüncü düzeltme: sorun veride değil, basit simülasyondaydı.** Simülasyon
Sherbrooke'ta ters FA işareti öngörüyordu ve bunu açıklanamadı diye yazmıştık.
Oysa tensörleri sabit MD = 0.70 µm²/ms (gerçek ortanca 0.594), tek bir simetrik
şekil, rastgele yön ve her yerde aynı S₀ ve σ içeriyordu. Hiçbir idealleştirme
tek başına her kuralda işareti çevirmiyor; dördü birlikte çeviriyor.

**Dördüncü düzeltme: seçimi sonuca göre yapıyormuşuz.** İlk sürümde, ölçülen
sinyal fit'i fiziksel olmayan bir değer verince voksel atılıyordu; yani farkın en
büyük olduğu yer. Voksel kümesi de aynı şekilde seçilmişti. Bu, gürültünün
Sherbrooke FA farkının yalnızca %60'ını açıkladığı izlenimini veriyordu. Voksel
kümesi ve binler yalnızca DIPY fit'inden alınınca, ve fiziksel olmayan fit'ler
gözlenen ve simüle veride aynı şekilde ele alınınca, gürültü farkın %89–106'sını
üretiyor. *Bağımsız bir kod incelemesi buldu.*

---

## PART 3 — Terms / Terimler

| Term | EN | TR |
|---|---|---|
| **DTI** | Models diffusion in each voxel as an ellipsoid, described by three eigenvalues. | Her vokseldeki difüzyonu üç özdeğerle tanımlanan bir elipsoit olarak modeller. |
| **FA** | Fractional anisotropy: how elongated the ellipsoid is. Bounded 0–1. | Fraksiyonel anizotropi: elipsoidin ne kadar uzadığı. 0–1 arasında. |
| **MD** | Mean diffusivity: the average of the three eigenvalues. Must be positive. | Ortalama difüzivite: üç özdeğerin ortalaması. Pozitif olmalı. |
| **OLS** | Ordinary least squares. Every measurement counts equally. FSL's default. | Sıradan en küçük kareler. Her ölçüm eşit sayılır. FSL'in varsayılanı. |
| **WLS** | Weighted least squares. Measurements are weighted, usually by signal. | Ağırlıklı en küçük kareler. Ölçümler genelde sinyale göre ağırlıklandırılır. |
| **IWLS** | Iteratively reweighted: the fit is repeated, reweighting from the previous prediction. MRtrix3's default, twice. | Yinelemeli yeniden ağırlıklandırma: fit, önceki tahminden yeniden ağırlıklandırılarak tekrarlanır. MRtrix3 varsayılanı, iki kez. |
| **Measured-signal weights** | Weights taken from the observed data, so contaminated by noise. | Ağırlıklar gözlenen veriden alınır, bu yüzden gürültüyle kirlenir. |
| **Predicted-signal weights** | Weights taken from a model prediction, so far less noise-contaminated. | Ağırlıklar model tahmininden alınır, gürültüden çok daha az etkilenir. |
| **SNR** | Signal-to-noise ratio. Falls as the b-value rises. | Sinyal-gürültü oranı. b-değeri arttıkça düşer. |
| **Bias / RMSE** | Bias is systematic error; RMSE combines bias and scatter. | Yanlılık sistematik hata; RMSE yanlılık ve saçılmayı birleştirir. |
| **Non-physical fit** | FA above 1 or MD at or below zero, from a negative eigenvalue. | Negatif özdeğerden doğan FA > 1 veya MD ≤ 0 değeri. |
| **Offset** | The difference between the two weighting schemes on the same data. | Aynı veride iki ağırlıklandırma şeması arasındaki fark. |

---

## PART 4 — Every methodological choice and why / Her metodolojik tercih ve gerekçesi

### EN

Each choice below exists to rule out one alternative explanation.

| Choice | Rules out |
|---|---|
| One shared brain mask for all fits | that the difference is masking |
| One shared volume subset (`--shell`) | that the difference is shell selection |
| No preprocessing in the main analysis | that one toolkit's preprocessing leaked in |
| Physical admissibility filter | that failed fits dominate the correlation |
| Estimator matched (`-iter 0`) | that the difference is the algorithm, not the toolkit |
| DIPY given measured-signal weights | that the cause is anything but the weighting |
| Phantoms with known eigenvalues | that no scheme is actually less accurate |
| Three SNR levels | that the effect is confined to good data |
| Simulations on both real gradient tables | that the result is specific to one protocol |
| Voxels and bins from the DIPY fit alone | that the comparison selects on its own outcome |
| Three rules for non-physical fits | that one arbitrary rule drives the answer |
| Noise-only controls for every check | that an artefact, not noise, produced the pattern |
| Two datasets | that it is a one-off artefact |

**The choice most likely to be challenged: why no preprocessing?** Because any
preprocessing step is itself a toolkit-specific choice. Note the asymmetry we
cannot escape: FSL ships no denoiser, so giving each toolkit "its own"
preprocessing would leave FSL fitting noisier data and the difference would no
longer be attributable to the fit. So preprocessing is either absent (main
analysis) or identical for all three (sensitivity analysis). Both are reported.

### TR

Aşağıdaki her tercih bir alternatif açıklamayı elemek için var: ortak maske
(maskeleme değil), ortak hacim alt kümesi (kabuk seçimi değil), ön işleme yok
(bir aracın ön işlemesi sızmasın), fiziksel kabul edilebilirlik filtresi (bozuk
fitler korelasyonu belirlemesin), eşleşmiş estimator (fark algoritmadan mı
araçtan mı), DIPY'ye ölçülen-sinyal ağırlığı vermek (sebep ağırlıklandırma mı),
bilinen özdeğerli fantomlar (hangi şema daha az doğru), üç SNR seviyesi (etki
yalnızca iyi veride mi), iki protokolün simülasyonu (sonuç tek protokole mi
özgü), voksel ve binlerin yalnızca DIPY fit'inden alınması (karşılaştırma kendi
sonucuna göre seçim yapmasın), fiziksel olmayan fitler için üç kural (cevabı
keyfi bir kural mı belirliyor), her kontrol için salt gürültü karşılaştırması
(deseni gürültü mü yoksa bir artefakt mı üretti), iki veri seti (tek seferlik
bir yapaylık mı).

**En çok itiraz görecek tercih: neden ön işleme yok?** Çünkü her ön işleme adımı
kendisi araca özgü bir tercih. Kaçınamadığımız asimetriye dikkat: FSL'de gürültü
giderici yok; her araca "kendi" ön işlemesini vermek FSL'i gürültülü veriyle
bırakırdı ve fark artık uydurmaya atfedilemezdi. Bu yüzden ön işleme ya yok (ana
analiz) ya da üçü için aynı (duyarlılık analizi). İkisi de raporlanıyor.

---

## PART 5 — Results in one table / Sonuçlar tek tabloda

| Question | Answer |
|---|---|
| Do implementations differ? | **No.** FSL = MRtrix3 at a matched estimator: r = 1.0000, MAE below 0.0001 |
| What differs then? | The weighting scheme, and which one each toolkit defaults to |
| Why does DIPY differ? | Predicted-signal weights. Give it measured-signal weights and 98% of the gap closes |
| Is one scheme less accurate? | Yes, in MD: measured-signal weighting, as Veraart (2013) reported |
| Does it matter? | At SNR 30 the MD bias is −0.0065 µm²/ms; at SNR 10 it is −0.0542 |
| Does the FA result hold everywhere? | No. On the phantom and the Stanford protocol yes; on the Sherbrooke protocol its FA bias was the largest in only 8 of 30 conditions |
| How big on real data? | Differences of 0.09–0.25 SD of white matter FA |
| Bigger than switching toolkit? | **Yes** — one FSL flag beats replacing FSL entirely at a matched estimator |
| Do the real-data differences come from noise? | Mostly. At the measured noise level, noise on each voxel's own tensor reproduces 101% of the Stanford FA offset, 83% of its MD offset, and 89–106% and 86–91% on Sherbrooke |
| What is left unexplained? | 13–17% of the MD offsets, and Stanford's most anisotropic bin |
| Does denoising fix it? | It halves the MD offset (44–61%) but does not close it |
| Non-physical fits? | DIPY returns none because it clips eigenvalues; FSL and MRtrix3 return them in 0.14–3.97% of white matter voxels |

---

## PART 6 — Figures / Figürler

**Figure 1 — Design.** Left: brain extraction, each tool on its own idiomatic
input. Right: tensor fitting, everything held identical and the estimator varied
deliberately, with arms labelled by weight source. *Point:* the two branches make
opposite choices about the input, on purpose.

**Figure 2 — Agreement with the estimator matched.** FA maps, pairwise scatter
and Bland–Altman, with each panel labelled by the command it ran. FSL and
MRtrix3 coincide; both differ from DIPY by the same amount. The FSL–MRtrix3
panel names the 57 voxels that fall outside its axis, all of them voxels
containing a measurement at or below zero.

**Supplementary Figure S1 — Interface.** The environment at the fitting stage.
*Point:* the command is shown in full and runs unchanged outside the tool.

**Supplementary Figures S2–S3 — Brain masks.** FSL widest, MRtrix3 narrowest,
DIPY excluding the ventricles. *Point:* Dice stays above 0.90 despite a 21%
spread in mask volume, and the ordering flips between datasets.

**Supplementary Figure S4 — Sherbrooke agreement.** As Figure 2, for the second
dataset.

---

## PART 7 — What the contribution is, honestly / Katkı gerçekte ne

### EN

**It is not a discovery.** Every component is documented. MRtrix3 says it
iterates; DIPY cites Chung et al. (2006); FSL's flag is in its help text.
Veraart et al. (2013) established which scheme is more accurate.

**It is a translation gap, measured.** A decade after the estimation question was
settled, the three most used toolkits still ship different answers as defaults,
and users cannot see which they are getting. We quantify what that costs, at
which noise levels, and show it exceeds the effect of changing toolkit.

**Why that is worth publishing:** nobody had measured it; it is directly
actionable (report the estimator, not just the toolkit); it reframes
"software variability" as something specific and fixable; and it is fully
reproducible from open data with no credentials.

**The honest framing to use out loud:** *"We did not find a new estimator
problem. We found that the field has one, already solved in the literature,
still sitting in the defaults — and we measured what it costs."*

### TR

**Bu bir keşif değil.** Her bileşen belgelenmiş. MRtrix3 iterasyon yaptığını
söylüyor; DIPY Chung ve ark. 2006'ya atıf veriyor; FSL'in bayrağı yardım
metninde. Veraart ve ark. (2013) hangi şemanın daha doğru olduğunu göstermişti.

**Bu, ölçülmüş bir teori-pratik boşluğu.** Estimation sorusu çözüldükten on yıl
sonra, en çok kullanılan üç araç hâlâ farklı cevapları varsayılan olarak
dağıtıyor ve kullanıcı hangisini aldığını göremiyor. Bunun bedelini, hangi
gürültü seviyelerinde ve araç değiştirmenin etkisini aştığını ölçüyoruz.

**Neden yayımlanmaya değer:** kimse ölçmemiş; doğrudan eyleme dönüşür (aracı
değil estimator'ü raporla); yaygın "yazılım değişkenliği" ifadesini daha belirli
ve düzeltilebilir bir şeye çeviriyor; ve kimlik bilgisi gerektirmeyen açık
veriyle tamamen tekrarlanabilir.

**Yüksek sesle kullanılacak dürüst çerçeve:** *"Yeni bir estimator problemi
bulmadık. Alanın, literatürde çoktan çözülmüş bir problemi hâlâ
varsayılanlarında taşıdığını bulduk — ve bedelini ölçtük."*

---

## PART 8 — Questions an expert will ask / Uzmanın soracakları

**Q: Have you read Veraart 2013?**
*EN:* Yes — it is the paper's starting point, cited in the abstract, introduction
and discussion. We reproduce its result for the configurations these toolkits
distribute, add the SNR dependence the mechanism predicts, and show the
recommendation has not reached the defaults.
*TR:* Evet — makalenin başlangıç noktası. Sonucunu bu araçların dağıttığı
yapılandırmalar için tekrarlıyor, mekanizmanın öngördüğü SNR bağımlılığını
ekliyor ve tavsiyenin varsayılanlara ulaşmadığını gösteriyoruz.

**Q: Is measured-signal weighting always the worst scheme?**
*EN:* In MD, in every condition we simulated, yes. In FA it depends on the
protocol: on a single-b = 0, b = 1000 acquisition its negative FA bias partly
cancels the upward bias that noise causes in every estimator, so its absolute FA
bias can be smaller. The paper says this explicitly.
*TR:* MD'de simüle ettiğimiz her koşulda evet. FA'da protokole bağlı: tek b = 0'lı
b = 1000 edinimde negatif FA yanlılığı, bütün yöntemlerde ortak olan pozitif
gürültü yanlılığını kısmen dengeliyor. Makalede bu açıkça yazıyor.

**Q: How do you know the real-data differences are noise, not artefacts?**
*EN:* We simulated noise on each voxel's own fitted tensor, at a noise level
measured from the ten b = 0 volumes, and compared like with like. The outlier
exclusions and the residual shuffle were also run on noise-only data as
controls. What noise does not reproduce is 13–17% of the MD offsets and
Stanford's most anisotropic bin.
*TR:* Her vokselin kendi tensörü üzerine, on b = 0 hacminden ölçülen gürültü
seviyesinde gürültü ekleyip benzeri benzerle karşılaştırdık. Uç değer atma ve
rezidüel karıştırma testleri salt gürültü verisinde de yapıldı. Gürültünün
üretemediği kısım: MD farklarının %13–17'si ve Stanford'un en anizotropik bini.

**Q: Why report three rules for non-physical fits?**
*EN:* Because the measured-signal fit returns FA above 1 in 5.3% of Sherbrooke
voxels, and any rule that drops them selects on the quantity being measured.
Reporting all three shows how much the answer depends on that choice: 89% to
106% for the Sherbrooke FA offset.
*TR:* Çünkü ölçülen-sinyal fit'i Sherbrooke vokselinin %5.3'ünde FA > 1
döndürüyor ve bunları atan her kural, ölçülen büyüklüğe göre seçim yapmış olur.
Üç kuralı birlikte vermek cevabın bu tercihe ne kadar bağlı olduğunu gösteriyor:
Sherbrooke FA farkı için %89–106.

**Q: One subject per dataset.**
*EN:* Stated in the limitations. The central claim needs no sample, because the
answer is exact equality. What two subjects cannot support is how the
between-scheme difference varies with acquisition, and we do not claim it.
*TR:* Limitations'ta yazılı. Merkezi iddia örneklem gerektirmiyor, çünkü cevap tam
eşitlik. İki deneğin destekleyemeyeceği iddia, şemalar arası farkın edinime göre
nasıl değiştiği; onu da öne sürmüyoruz.

**Q: So which should I use?**
*EN:* Predicted-signal weighting, which MRtrix3 and DIPY apply by default. In FSL
that means knowing that `--wls` is not that scheme. More important than the
choice is recording it.
*TR:* Tahmin-edilen-sinyal ağırlıklandırması — MRtrix3 ve DIPY varsayılanda
uyguluyor. FSL'de bu, `--wls`'in o şema olmadığının farkında olmak demek.
Seçimden daha önemlisi, onu kaydetmek.

---

## Rapid recall / Hızlı hatırlama

| Cue | Say this |
|---|---|
| What is the paper? | Toolkit differences in tensor fitting are estimator differences, not implementation differences — and the recommended estimator is not the default everywhere. |
| Strongest single result | FSL and MRtrix3 agree at r = 1.0000 when the estimator is matched. |
| Strongest design element | DIPY run twice on the same data with the weights swapped: 98% of the difference closes. |
| Most useful for a reader | One flag inside FSL changes FA more than replacing FSL with another toolkit. |
| Where the real-data differences come from | Mostly noise acting through the estimator: 89–106% of the FA offsets at the measured noise level. |
| What is honestly unexplained | 13–17% of the MD offsets, and Stanford's most anisotropic bin. |
| Prior work | Veraart et al. (2013) settled which scheme is better; Koay et al. (2006) gave the framework. |
| Novelty, honestly | Not a discovery; a measured translation gap, with magnitudes nobody had reported. |
| Biggest limitation | One subject per dataset; Rician phantoms without artefacts; the tensor model only. |
| If it all collapses to one line | "Weighted least squares" is a family, not an algorithm — and the members are not equally good. |
