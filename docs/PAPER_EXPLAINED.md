# dMRI Rosetta Stone — Study Companion / Çalışma Rehberi

A section-by-section companion to the manuscript: what we did, why we did it that
way, what every term means, what each figure shows, and — the question that
matters most — why the work is worth publishing when every method in it is
already standard.

Makalenin bölüm bölüm rehberi: ne yaptık, neden böyle yaptık, her terim ne
anlama geliyor, her figür neyi gösteriyor ve — en önemli soru — içindeki her
yöntem zaten standartken bu çalışma neden yayımlanmaya değer.

---

## PART 1 — The aim / Amaç

### EN

Diffusion MRI is analysed almost entirely with three software packages: **FSL**,
**MRtrix3**, and **DIPY**. They do the same science but speak different
languages. Brain extraction is `bet` in FSL, `dwi2mask` in MRtrix3, and
`median_otsu` in DIPY. Mean diffusivity is `MD` in one, `ADC` in another. A
researcher trained in one ecosystem cannot easily read, reproduce, or extend
work done in another.

The paper does two things:

1. **A teaching platform.** A browser application that shows the *same* pipeline
   step in all three toolkits side by side, executes each on real open brain
   data, and displays the outputs together. Seven stages, from brain extraction
   through tractography to group analysis. Containerised, so nothing has to be
   installed.

2. **A measurement.** Using that platform's machinery, we ask a question the
   field assumes it knows the answer to: *do the three toolkits actually agree?*
   We measure it on two independent open datasets under tightly controlled
   conditions.

The second part is what turns a teaching tool into a research contribution.

### TR

Difüzyon MRI analizi neredeyse tamamen üç yazılımla yapılıyor: **FSL**,
**MRtrix3** ve **DIPY**. Aynı bilimi yapıyorlar ama farklı diller konuşuyorlar.
Beyin çıkarımı FSL'de `bet`, MRtrix3'te `dwi2mask`, DIPY'de `median_otsu`.
Ortalama difüzivite birinde `MD`, diğerinde `ADC`. Bir ekosistemde eğitilmiş
araştırmacı, diğerinde yapılmış işi kolayca okuyamıyor, tekrarlayamıyor ya da
geliştiremiyor.

Makale iki iş yapıyor:

1. **Bir öğretim platformu.** *Aynı* boru hattı adımını üç araçta yan yana
   gösteren, her birini gerçek açık beyin verisi üzerinde çalıştıran ve
   çıktıları birlikte sunan tarayıcı uygulaması. Beyin çıkarımından
   traktografiye ve grup analizine kadar yedi aşama. Konteynerli, yani hiçbir
   şey kurmaya gerek yok.

2. **Bir ölçüm.** Bu platformun altyapısını kullanarak, alanın cevabını bildiğini
   varsaydığı bir soruyu soruyoruz: *üç araç gerçekten uyuşuyor mu?* Bunu iki
   bağımsız açık veri setinde, sıkı kontrollü koşullarda ölçüyoruz.

İkinci kısım, öğretim aracını bir araştırma katkısına dönüştüren şey.

---

## PART 2 — Glossary / Terimler sözlüğü

| Term | EN — what it means | TR — ne demek |
|---|---|---|
| **dMRI** | Diffusion MRI. Measures how water molecules move; movement is restricted by axon membranes, so it reveals fibre structure. | Difüzyon MRI. Su moleküllerinin hareketini ölçer; hareket akson zarlarıyla kısıtlandığı için lif yapısını ortaya çıkarır. |
| **DWI / volume** | One 3-D image acquired with diffusion sensitised in one direction. A scan is many such volumes. | Difüzyona bir yönde duyarlı tek bir 3B görüntü. Bir tarama bunlardan çok sayıda içerir. |
| **b-value** | Strength of diffusion weighting (s/mm²). b = 0 means no weighting — a plain image. Higher b = more diffusion sensitivity, less signal. | Difüzyon ağırlıklandırmasının gücü (s/mm²). b = 0 ağırlıklandırma yok demek. Yüksek b = daha çok difüzyon duyarlılığı, daha az sinyal. |
| **Shell** | All volumes acquired at one b-value. "Single-shell" = one non-zero b. "Multi-shell" = several. | Tek bir b-değerinde alınan tüm hacimler. "Tek kabuk" = bir sıfırdan farklı b. "Çok kabuk" = birkaç tane. |
| **HARDI** | High Angular Resolution Diffusion Imaging — many directions, so crossing fibres can be resolved. | Yüksek açısal çözünürlüklü difüzyon görüntüleme — çok sayıda yön, böylece kesişen lifler çözülebilir. |
| **Voxel** | One 3-D pixel. Here 2 × 2 × 2 mm. | Bir 3B piksel. Burada 2 × 2 × 2 mm. |
| **DTI** | Diffusion Tensor Imaging. Models diffusion in each voxel as an ellipsoid described by three eigenvalues. | Difüzyon Tensör Görüntüleme. Her vokseldeki difüzyonu üç özdeğerle tanımlanan bir elipsoit olarak modeller. |
| **Eigenvalue** | The three numbers giving diffusion rate along the ellipsoid's three axes. **Must be positive** — negative is physically impossible. | Elipsoidin üç ekseni boyunca difüzyon hızını veren üç sayı. **Pozitif olmalı** — negatif fiziksel olarak imkânsız. |
| **FA** | Fractional Anisotropy. How elongated the ellipsoid is. Bounded **0 to 1**. High in compact tracts, low in grey matter and CSF. | Fraksiyonel Anizotropi. Elipsoidin ne kadar uzadığı. **0 ile 1** arasında sınırlı. Sıkı traktlarda yüksek, gri madde ve BOS'ta düşük. |
| **MD** | Mean Diffusivity. Average of the three eigenvalues — overall how fast water moves. Must be **positive**. | Ortalama Difüzivite. Üç özdeğerin ortalaması — suyun genel olarak ne kadar hızlı hareket ettiği. **Pozitif** olmalı. |
| **AD / RD** | Axial / Radial diffusivity — along vs across the main fibre direction. | Aksiyel / Radyal difüzivite — ana lif yönü boyunca ve ona dik. |
| **WLS** | Weighted Least Squares — the fitting method used to estimate the tensor. "Unconstrained" means it is allowed to return negative eigenvalues. | Ağırlıklı En Küçük Kareler — tensörü kestirmek için kullanılan uydurma yöntemi. "Kısıtsız", negatif özdeğer döndürebilmesi demek. |
| **CSD** | Constrained Spherical Deconvolution. Goes beyond DTI: recovers *multiple* fibre directions per voxel. | Kısıtlı Küresel Dekonvolüsyon. DTI'nın ötesine geçer: voksel başına *birden çok* lif yönü çıkarır. |
| **Tractography** | Following fibre orientations voxel to voxel to reconstruct tracts (streamlines). | Lif yönelimlerini voksel voksel takip ederek traktları (akım çizgilerini) yeniden oluşturma. |
| **TBSS** | Tract-Based Spatial Statistics. FSL's pipeline for comparing FA across subjects on a white matter "skeleton". | Trakt-Tabanlı Uzaysal İstatistik. FSL'in, denekler arası FA karşılaştırmasını beyaz madde "iskeleti" üzerinde yapan hattı. |
| **MP-PCA** | Marchenko–Pastur PCA denoising — uses random matrix theory to separate signal from thermal noise. | Marchenko–Pastur PCA gürültü giderme — sinyali termal gürültüden ayırmak için rastgele matris teorisi kullanır. |
| **Eddy correction** | Correcting distortions caused by rapidly switched gradients, plus head motion. | Hızla değişen gradyanların yol açtığı bozulmaların ve kafa hareketinin düzeltilmesi. |
| **Brain mask** | Binary image marking which voxels are brain. Everything downstream depends on it. | Hangi voksellerin beyin olduğunu işaretleyen ikili görüntü. Sonraki her şey buna bağlı. |
| **Dice (DSC)** | Overlap between two masks. 0 = none, 1 = identical. | İki maske arasındaki örtüşme. 0 = yok, 1 = özdeş. |
| **Pearson r** | Linear correlation. **Highly sensitive to outliers** — this matters enormously here. | Doğrusal korelasyon. **Aykırı değerlere çok duyarlı** — bu, burada çok önemli. |
| **Spearman ρ** | Rank correlation. Robust to outliers; reported alongside r as a cross-check. | Sıra korelasyonu. Aykırı değerlere dayanıklı; kontrol amaçlı r ile birlikte verilir. |
| **MAE** | Mean Absolute Error — average size of the difference. Robust, unlike r. | Ortalama Mutlak Hata — farkın ortalama büyüklüğü. r'nin aksine dayanıklı. |
| **Bland–Altman** | Plots difference against mean for each voxel. Reveals **systematic bias** (a consistent offset) as distinct from random scatter. | Her voksel için farkı ortalamaya karşı çizer. **Sistematik yanlılığı** (tutarlı bir kayma) rastgele saçılmadan ayırt eder. |
| **LoA** | Limits of Agreement — bias ± 1.96 SD. The range containing 95% of differences. | Uyum Sınırları — yanlılık ± 1.96 SS. Farkların %95'ini içeren aralık. |

---

## PART 3 — The three toolkits / Üç araç

### EN

**FSL** (Oxford). The oldest and most widely taught. Strong preprocessing
(`eddy` is the field standard), DTI fitting, and TBSS for group statistics. Has
**no** dedicated denoising and **no** CSD. Its licence restricts commercial use.

**MRtrix3** (Florey Institute). Built around CSD and modern tractography (iFOD2,
SIFT2). Strongest for fibre orientation and connectome work. Steeper learning
curve.

**DIPY** (Python). A library rather than a command suite. Everything is
inspectable Python; best when you need to see or modify the algorithm. Slower on
large data.

The paper is not arguing one is best. It argues that their *differences* — what
each has, what each lacks, and how each behaves numerically — are pedagogically
and methodologically important, and currently invisible unless you run all three
yourself.

### TR

**FSL** (Oxford). En eski ve en yaygın öğretileni. Güçlü ön işleme (`eddy` alanın
standardı), DTI uydurma ve grup istatistiği için TBSS. Özel gürültü giderme
**yok**, CSD **yok**. Lisansı ticari kullanımı kısıtlıyor.

**MRtrix3** (Florey Enstitüsü). CSD ve modern traktografi (iFOD2, SIFT2) etrafında
kurulmuş. Lif yönelimi ve konnektom işi için en güçlüsü. Öğrenme eğrisi dik.

**DIPY** (Python). Komut takımı değil, bir kütüphane. Her şey incelenebilir
Python; algoritmayı görmen ya da değiştirmen gerektiğinde en iyisi. Büyük veride
daha yavaş.

Makale birinin en iyi olduğunu savunmuyor. *Farklarının* — her birinde ne var, ne
yok ve sayısal olarak nasıl davrandıkları — pedagojik ve metodolojik olarak
önemli olduğunu, ve üçünü birden kendin çalıştırmadıkça görünmez olduğunu
savunuyor.

---

## PART 4 — Methods and why / Yöntemler ve gerekçeleri

This is the part to know cold. Every choice below exists to remove one
alternative explanation for the differences we report.

Bu kısmı çok iyi bilmek gerekiyor. Aşağıdaki her tercih, raporladığımız farklar
için alternatif bir açıklamayı elemek üzere var.

### 4.1 One shared brain mask for all three tensor fits

**EN — What.** All three toolkits were given the *same* brain mask (generated by
`median_otsu`) when fitting the tensor.

**Why.** If each tool used its own mask, they would be fitting different sets of
voxels. Any difference in FA could then be a masking difference rather than a
fitting difference. Fixing the mask removes that explanation. **This isolates the
tensor-fitting stage**, which is precisely what we claim to measure.

**TR — Ne.** Tensör uydurulurken üç araca da *aynı* beyin maskesi (`median_otsu`
ile üretilmiş) verildi.

**Neden.** Her araç kendi maskesini kullansaydı, farklı voksel kümelerine
uyduruyor olurlardı. FA'daki herhangi bir fark, uydurma farkı değil maskeleme
farkı olabilirdi. Maskeyi sabitlemek bu açıklamayı eler. **Bu, tensör uydurma
aşamasını yalıtır** — ölçtüğümüzü iddia ettiğimiz tam olarak budur.

### 4.2 Brain masks compared separately, each tool on its own input

**EN — What.** For the *mask comparison* (Dice), each tool was run the way it is
designed to be run: `bet` on the mean b = 0 image, `dwi2mask` on the full DWI
series, `median_otsu` on the full series with b = 0 indexed.

**Why.** Forcing all three onto one input would measure something artificial. The
input a tool expects is part of the algorithm. We want the difference a real user
would encounter. Note this is the *opposite* choice from 4.1 — and deliberately
so, because the two comparisons ask different questions.

**TR — Ne.** *Maske karşılaştırması* (Dice) için her araç, tasarlandığı şekilde
çalıştırıldı: `bet` ortalama b = 0 görüntüsünde, `dwi2mask` tüm DWI serisinde,
`median_otsu` b = 0 indeksli tüm seride.

**Neden.** Üçünü tek bir girdiye zorlamak yapay bir şey ölçerdi. Bir aracın
beklediği girdi, algoritmanın parçasıdır. Gerçek bir kullanıcının karşılaşacağı
farkı istiyoruz. Bunun 4.1'in *tersi* bir tercih olduğuna dikkat — ve bilerek
öyle, çünkü iki karşılaştırma farklı soru soruyor.

### 4.3 Identical volume subset on multi-shell data (`--shell`)

**EN — What.** Sherbrooke has three shells (b = 1000/2000/3500). We extracted
b = 0 + b = 1000 **once** and gave that identical subset to all three tools.

**Why.** The single-tensor model assumes monoexponential signal decay, which
breaks across shells. FSL and MRtrix3 silently fit *every* volume handed to them;
DIPY requires the user to choose. Left alone, the three would fit different data,
and our "tensor-fitting difference" would be contaminated by shell selection.
This is itself one of the paper's teaching points.

**TR — Ne.** Sherbrooke üç kabuklu (b = 1000/2000/3500). b = 0 + b = 1000'i **bir
kez** çıkarıp aynı alt kümeyi üç araca da verdik.

**Neden.** Tek tensör modeli monoeksponansiyel sinyal azalması varsayar, bu da
kabuklar arasında bozulur. FSL ve MRtrix3 kendilerine verilen *her* hacmi sessizce
uydurur; DIPY kullanıcının seçmesini ister. Kendi haline bırakılsa üçü farklı
veriye uydururdu ve "tensör uydurma farkımız" kabuk seçimiyle kirlenirdi. Bu
zaten makalenin öğretim noktalarından biri.

### 4.4 No denoising, no eddy correction — deliberately

**EN — What.** We fitted the tensor on unprocessed data.

**Why.** Any preprocessing step is *itself* a toolkit-specific choice. Applying
MRtrix3's denoising to all three would import MRtrix3's assumptions into the
comparison and confound exactly what we are trying to isolate. The cost, which we
state openly, is that our numbers describe **one pipeline step, not a complete
analysis**. That is an honest limitation, not an oversight — and stating it
pre-empts the obvious reviewer question.

**TR — Ne.** Tensörü işlenmemiş veri üzerinde uydurduk.

**Neden.** Herhangi bir ön işleme adımı *kendisi* araca özgü bir tercihtir.
MRtrix3'ün gürültü gidermesini üçüne birden uygulamak, MRtrix3'ün varsayımlarını
karşılaştırmaya sokar ve tam da yalıtmaya çalıştığımız şeyi karıştırır. Açıkça
belirttiğimiz bedeli şu: sayılarımız **tam bir analizi değil, tek bir boru hattı
adımını** tarif ediyor. Bu dürüst bir sınırlama, bir ihmal değil — ve bunu
söylemek hakemin bariz sorusunu önceden karşılıyor.

### 4.5 Physical plausibility filter — the subtle one

**EN — What.** Statistics use only voxels where the values are physically
possible in *both* tools of a pair: FA in [0, 1], and 0 < MD ≤ 3.0 × 10⁻³ mm²/s
(the diffusivity of free water at body temperature).

**Why.** Unconstrained WLS can return **negative eigenvalues**. These push FA
above 1 and MD below 0 — physically impossible values. There were only a few
hundred such voxels (0–4% of white matter). But **Pearson correlation is
dominated by extreme values**. Leaving them in made MRtrix3–DIPY MD agreement
look like r = 0.118 when it is actually r = 0.9965, while the mean absolute error
moved by less than 2%.

This is the single most important methodological point in the paper. Without the
filter we would have reported that two nearly identical toolkits are unrelated.

**TR — Ne.** İstatistikler yalnızca, bir çiftteki *her iki* araçta da fiziksel
olarak mümkün değerlere sahip voksellerini kullanıyor: FA ∈ [0, 1] ve
0 < MD ≤ 3.0 × 10⁻³ mm²/s (vücut sıcaklığında serbest suyun difüzivitesi).

**Neden.** Kısıtsız WLS **negatif özdeğer** döndürebilir. Bunlar FA'yı 1'in
üstüne, MD'yi 0'ın altına iter — fiziksel olarak imkânsız değerler. Böyle
vokseller birkaç yüz taneydi (beyaz maddenin %0–4'ü). Ama **Pearson korelasyonuna
uç değerler hâkim olur**. Onları bırakmak, MRtrix3–DIPY MD uyumunu gerçekte
r = 0.9965 iken r = 0.118 gibi gösterdi; ortalama mutlak hata ise %2'den az
değişti.

Makaledeki en önemli tek metodolojik nokta bu. Filtre olmadan, neredeyse özdeş
iki aracın ilgisiz olduğunu raporlamış olacaktık.

### 4.6 Pearson *and* Spearman *and* MAE *and* Bland–Altman

**EN — Why four measures?** Each answers a different question, and using one
alone would mislead.

- **Pearson r** — do they co-vary linearly? Sensitive to outliers.
- **Spearman ρ** — do they rank voxels the same way? Robust; a cross-check on r.
- **MAE** — how big is the typical difference, in real units?
- **Bland–Altman** — is the difference a *consistent offset* (bias) or random
  scatter? Two toolkits can correlate at r = 0.99 and still be systematically
  offset. Correlation cannot detect that; Bland–Altman is designed to.

The FSL finding depends entirely on Bland–Altman. Correlation alone would have
missed it.

**TR — Neden dört ölçüt?** Her biri farklı soruyu yanıtlıyor ve tek başına biri
yanıltırdı.

- **Pearson r** — doğrusal olarak birlikte mi değişiyorlar? Aykırı değerlere
  duyarlı.
- **Spearman ρ** — voksellerini aynı şekilde mi sıralıyorlar? Dayanıklı; r için
  çapraz kontrol.
- **MAE** — tipik fark gerçek birimlerle ne kadar büyük?
- **Bland–Altman** — fark *tutarlı bir kayma* mı (yanlılık) yoksa rastgele saçılma
  mı? İki araç r = 0.99 ile korele olup yine de sistematik olarak kaymış
  olabilir. Korelasyon bunu göremez; Bland–Altman bunun için tasarlanmıştır.

FSL bulgusu tamamen Bland–Altman'a dayanıyor. Sadece korelasyon bunu kaçırırdı.

### 4.7 Two independent datasets

**EN — What.** Stanford HARDI (single-shell, b = 2000, 10 b = 0 volumes) and
Sherbrooke 3-shell (b = 1000 subset, only 1 b = 0 volume). Different sites,
protocols, and — importantly — different numbers of b = 0 volumes.

**Why.** This is the design decision that changed the paper's conclusion. With
Stanford alone we would have reported "FSL gives about 4% lower FA — a fixed,
correctable bias." Sherbrooke showed the FA offset **reverses sign**. One dataset
would have produced a confident, wrong claim. Replication is what separates a
finding from an artefact.

**TR — Ne.** Stanford HARDI (tek kabuk, b = 2000, 10 adet b = 0 hacmi) ve
Sherbrooke 3-shell (b = 1000 alt kümesi, sadece 1 adet b = 0 hacmi). Farklı
merkezler, protokoller ve — önemlisi — farklı sayıda b = 0 hacmi.

**Neden.** Makalenin sonucunu değiştiren tasarım kararı bu. Sadece Stanford ile
"FSL yaklaşık %4 daha düşük FA veriyor — sabit, düzeltilebilir bir yanlılık"
diye raporlayacaktık. Sherbrooke, FA kaymasının **işaret değiştirdiğini**
gösterdi. Tek veri seti kendinden emin ve yanlış bir iddia üretecekti. Tekrar,
bir bulguyu bir yapaylıktan ayıran şeydir.

---

## PART 5 — Figures explained / Figürlerin açıklaması

### Figure 1 — Container architecture / Konteyner mimarisi

**EN.** Two halves. *Build time* (top): a two-stage Docker build. Stage 1 pulls
MRtrix3 binaries from the official image; Stage 2 starts from Ubuntu 22.04,
installs FSL 6.0.7 and the Python stack, and copies MRtrix3 in. Two stages
because installing FSL and MRtrix3 into one stage causes dependency conflicts.
*Run time* (bottom): the user's browser talks to the Streamlit app on port 8501;
the app dispatches commands to all three toolkits via Python `subprocess`; open
data is mounted from the host. **Point of the figure:** nothing is installed on
the user's machine — that is the "zero installation barrier" design principle
made concrete.

**TR.** İki yarım. *Derleme zamanı* (üst): iki aşamalı Docker derlemesi. Aşama 1
MRtrix3 ikili dosyalarını resmi imajdan çeker; Aşama 2 Ubuntu 22.04'ten başlar,
FSL 6.0.7 ve Python yığınını kurar, MRtrix3'ü içine kopyalar. İki aşama, çünkü
FSL ve MRtrix3'ü tek aşamaya kurmak bağımlılık çakışması yaratıyor. *Çalışma
zamanı* (alt): kullanıcının tarayıcısı 8501 portundan Streamlit uygulamasıyla
konuşur; uygulama komutları Python `subprocess` ile üç araca dağıtır; açık veri
ana makineden bağlanır. **Figürün amacı:** kullanıcının makinesine hiçbir şey
kurulmuyor — "sıfır kurulum engeli" tasarım ilkesinin somut hali.

### Figure 2 — The interface / Arayüz

**EN.** Stage 4 (DTI Fitting), representative of all seven stages. Sidebar shows
the resolved dataset (detected shells, volume count) and the eight pages. Main
panel has three tabs — one per toolkit — and the selected tab shows the exact
runnable command, the outputs it will produce, a Run button that streams live
output, and the resulting FA and MD maps. **Point of the figure:** the command is
shown in full and can be copied and run *outside* the platform unchanged. It is a
translator, not a black box.

**TR.** Aşama 4 (DTI Uydurma), yedi aşamanın tümünü temsilen. Kenar çubuğu
çözümlenen veri setini (algılanan kabuklar, hacim sayısı) ve sekiz sayfayı
gösteriyor. Ana panelde üç sekme — araç başına bir tane — ve seçili sekmede tam
çalıştırılabilir komut, üreteceği çıktılar, canlı çıktı akıtan bir Run düğmesi ve
sonuçtaki FA ile MD haritaları. **Figürün amacı:** komut tam olarak gösteriliyor
ve platformun *dışında* değiştirilmeden kopyalanıp çalıştırılabiliyor. Bu bir
çevirmen, kara kutu değil.

### Figure 3 — FA agreement / FA uyumu

**EN.** Three rows. **(a)** FA maps from the three toolkits — visually they look
the same, which is the point: the eye cannot detect the differences. **(b)**
Scatter plots, one per pair. The MRtrix3–DIPY panel is a thin line on the
identity diagonal; the two FSL panels are visibly fatter clouds. **(c)**
Bland–Altman. The MRtrix3–DIPY bias line sits essentially on zero with tight
limits; both FSL panels show the cloud displaced off zero — that displacement
*is* the systematic bias. **Point of the figure:** panel (a) says "they agree",
panels (b) and (c) say "not quite, and not symmetrically". That contrast is the
paper's argument in one image.

**TR.** Üç satır. **(a)** Üç aracın FA haritaları — görsel olarak aynı
görünüyorlar, ki mesele de bu: göz farkları algılayamıyor. **(b)** Çift başına
saçılım grafikleri. MRtrix3–DIPY paneli özdeşlik köşegeninde ince bir çizgi; iki
FSL paneli gözle görülür şekilde daha şişkin bulutlar. **(c)** Bland–Altman.
MRtrix3–DIPY yanlılık çizgisi esasen sıfırda ve sınırlar dar; her iki FSL
panelinde bulut sıfırdan kaymış — bu kayma *sistematik yanlılığın kendisi*.
**Figürün amacı:** (a) paneli "uyuşuyorlar" diyor, (b) ve (c) panelleri "tam
değil ve simetrik değil" diyor. Bu karşıtlık, makalenin argümanı tek bir görselde.

### Figure 4 — Brain extraction / Beyin çıkarımı

**EN.** The mean b = 0 image in greyscale with each tool's mask overlaid in red.
FSL keeps the most tissue (203,984 voxels), MRtrix3 the least (167,950), DIPY in
between (187,948) — a 21% spread, even though every pairwise Dice exceeds 0.90.
The visible difference is at the lateral ventricles: DIPY excludes ventricular
CSF, the other two keep it. **Two points:** (i) Dice stays high for a large
compact object even when boundary decisions differ appreciably — a useful lesson
about the metric itself; (ii) a mask that includes ventricles admits
high-diffusivity, near-isotropic voxels into any later group statistics.

**TR.** Gri tonlamalı ortalama b = 0 görüntüsü, üzerine kırmızıyla her aracın
maskesi. FSL en çok dokuyu tutuyor (203.984 voksel), MRtrix3 en azını (167.950),
DIPY arada (187.948) — her ikili Dice 0.90'ı aşmasına rağmen %21'lik bir yayılım.
Görünür fark yan ventriküllerde: DIPY ventriküler BOS'u dışlıyor, diğer ikisi
tutuyor. **İki nokta:** (i) Dice, büyük ve sıkı bir nesnede sınır kararları hatırı
sayılır ölçüde farklı olsa bile yüksek kalıyor — ölçütün kendisi hakkında yararlı
bir ders; (ii) ventrikülleri içeren bir maske, sonraki grup istatistiklerine
yüksek difüzivitedeki, neredeyse izotropik voksellerini sokar.

### Supplementary S1 / S2

**EN.** The same two analyses repeated on Sherbrooke. Their job is to show the
replication visually: the MRtrix3–DIPY panel stays tight, the FSL panels stay
scattered — but the FSL bias line has moved to the *other side* of zero for FA.

**TR.** Aynı iki analizin Sherbrooke'ta tekrarı. Görevleri tekrarı görsel olarak
göstermek: MRtrix3–DIPY paneli dar kalıyor, FSL panelleri saçılmış kalıyor — ama
FSL yanlılık çizgisi FA için sıfırın *öbür tarafına* geçmiş.

---

## PART 6 — Results in one page / Sonuçlar tek sayfada

| Measure | Stanford | Sherbrooke | Reading |
|---|---|---|---|
| MRtrix3–DIPY FA r | 0.9990 | 0.9966 | Effectively interchangeable |
| MRtrix3–DIPY MD r | 0.9965 | 0.9991 | Effectively interchangeable |
| FSL vs others, FA r | 0.960–0.965 | 0.890–0.916 | Consistently lower |
| **FSL FA bias** | **−0.018 (lower)** | **+0.014 (higher)** | **Sign reverses** |
| FSL MD bias | −0.033 (≈5%) | −0.127 (≈19%) | Same direction, 4× larger |
| Mask Dice (all pairs) | 0.90–0.93 | 0.91–0.97 | High everywhere |
| Non-physical voxels | FSL 0.40%, MRtrix3 0.27%, DIPY 0% | FSL 3.97%, MRtrix3 2.03%, DIPY 0% | Same ranking both times |

**EN — The three findings.**
1. MRtrix3 and DIPY agree to four significant figures. Interchangeable in practice.
2. FSL is systematically offset from both — **and the offset is not fixed.** MD is
   always lower but by 5% then 19%; FA is lower on one dataset and higher on the
   other. A bias whose sign depends on the acquisition **cannot be corrected by a
   scaling factor**, because there is nothing stable to correct for.
3. DIPY never produced a physically impossible tensor fit; FSL produced the most.
   The ranking held on both datasets. The rate rose roughly tenfold on Sherbrooke,
   which has one b = 0 volume against Stanford's ten — so acquisition design
   affects fit failure rate.

**TR — Üç bulgu.**
1. MRtrix3 ve DIPY dört anlamlı basamağa kadar uyuşuyor. Pratikte birbirinin
   yerine kullanılabilir.
2. FSL ikisinden de sistematik olarak kaymış — **ve kayma sabit değil.** MD hep
   daha düşük ama önce %5 sonra %19; FA bir veri setinde daha düşük, diğerinde
   daha yüksek. İşareti edinime bağlı olan bir yanlılık **bir ölçek katsayısıyla
   düzeltilemez**, çünkü düzeltilecek sabit bir şey yok.
3. DIPY hiç fiziksel olarak imkânsız tensör uydurması üretmedi; FSL en çoğunu
   üretti. Sıralama iki veri setinde de korundu. Oran Sherbrooke'ta yaklaşık on
   kat arttı — Stanford'un on b = 0 hacmine karşı bir tane var — yani edinim
   tasarımı uydurma başarısızlık oranını etkiliyor.

---

## PART 7 — Why this is valuable / Bu çalışma neden değerli

This is the question to have a confident answer to. Every method in the paper is
standard: Dice, Pearson, Bland–Altman, DTI. So what is the contribution?

Bu, kendinden emin bir cevabın olması gereken soru. Makaledeki her yöntem
standart: Dice, Pearson, Bland–Altman, DTI. Peki katkı ne?

### EN

**1. Standard methods applied to an unasked question still produce new knowledge.**
Novelty in science lies in the *question and the finding*, not only in the
instrument. A thermometer is not novel; measuring something nobody thought to
measure with it can be. Everyone assumed the three toolkits agree. Nobody had
tested it under controlled conditions across acquisitions and published the
result. We did, and the answer is more interesting than the assumption: they
agree in pairs, not as a trio, and the disagreement does not behave like a fixed
bias.

**2. The negative result is the valuable one.** Had FSL been offset by a constant
4%, the finding would be a footnote — measure it once, correct for it, move on.
Because the sign flips between two ordinary open datasets, it is *not
correctable*, and an analyst pooling FA across studies processed with different
software cannot even anticipate the direction. That is an actionable warning for
multi-site studies, meta-analyses, and normative reference ranges.

**3. We document a methodological trap with immediate practical use.** A few
hundred non-physical voxels drop an MD correlation from 0.997 to 0.118. Anyone
computing agreement statistics on raw tensor maps — a common exercise — can
silently produce a badly wrong number. We quantify the trap and give the fix.

**4. The article type exists for exactly this.** Frontiers' *Technology and Code*
does not require algorithmic novelty. It requires working, documented, openly
archived software that meets a real community need. Judging this paper by the
standard of a new-method paper is judging it against the wrong criterion.

**5. The tool converts a one-off comparison into a reusable instrument.** Our
benchmark is two datasets, which we state plainly is not enough to characterise
how the FSL divergence varies. But adding a dataset is one fetcher entry and two
commands. We have made it cheap for anyone — including a reviewer — to extend or
contradict us. That is the opposite of an unfalsifiable claim.

**6. The educational gap is real and documented.** Table 2 compares against every
existing resource. No other places all three toolkits side by side, executable,
on the same real data, with no installation. Reducing the barrier for people
learning dMRI has value independent of the benchmark.

**Honest framing to use:** "We did not invent a method. We built an instrument
that makes an existing comparison cheap to perform, then performed it carefully
enough to find something the field had assumed away."

### TR

**1. Standart yöntemlerin sorulmamış bir soruya uygulanması yine de yeni bilgi
üretir.** Bilimde yenilik yalnızca alette değil, *soruda ve bulguda* yatar.
Termometre yeni değildir; kimsenin onunla ölçmeyi düşünmediği bir şeyi ölçmek
olabilir. Herkes üç aracın uyuştuğunu varsayıyordu. Kimse bunu kontrollü
koşullarda, farklı edinimlerde test edip yayımlamamıştı. Biz yaptık ve cevap
varsayımdan daha ilginç: ikişerli uyuşuyorlar, üçlü olarak değil, ve uyuşmazlık
sabit bir yanlılık gibi davranmıyor.

**2. Asıl değerli olan negatif sonuç.** FSL sabit %4 kaymış olsaydı, bulgu bir
dipnot olurdu — bir kez ölç, düzelt, geç. İşaret iki sıradan açık veri seti
arasında değiştiği için **düzeltilebilir değil**, ve farklı yazılımlarla işlenmiş
çalışmalardan FA havuzlayan bir analist yönü bile öngöremez. Bu; çok merkezli
çalışmalar, meta-analizler ve normatif referans aralıkları için eyleme
dönüştürülebilir bir uyarı.

**3. Hemen pratik faydası olan bir metodolojik tuzağı belgeliyoruz.** Birkaç yüz
fiziksel olmayan voksel, bir MD korelasyonunu 0.997'den 0.118'e düşürüyor. Ham
tensör haritalarında uyum istatistiği hesaplayan herkes — yaygın bir alıştırma —
sessizce fena halde yanlış bir sayı üretebilir. Tuzağı niceliyor ve çözümünü
veriyoruz.

**4. Makale tipi tam bunun için var.** Frontiers'ın *Technology and Code* türü
algoritmik yenilik istemiyor. Çalışan, belgelenmiş, açıkça arşivlenmiş ve gerçek
bir topluluk ihtiyacını karşılayan yazılım istiyor. Bu makaleyi yeni-yöntem
makalesi ölçütüyle yargılamak, yanlış ölçütle yargılamaktır.

**5. Araç, tek seferlik bir karşılaştırmayı tekrar kullanılabilir bir enstrümana
dönüştürüyor.** Benchmark'ımız iki veri seti ve FSL sapmasının nasıl
değiştiğini karakterize etmeye yetmediğini açıkça söylüyoruz. Ama veri seti
eklemek bir indirici kaydı ve iki komut. Bizi genişletmeyi ya da çürütmeyi
herkes için — hakem dahil — ucuz hale getirdik. Bu, yanlışlanamaz bir iddianın
tam tersi.

**6. Eğitim boşluğu gerçek ve belgeli.** Tablo 2 mevcut tüm kaynaklarla
karşılaştırıyor. Hiçbiri üç aracı aynı gerçek veri üzerinde, çalıştırılabilir
şekilde, kurulum gerektirmeden yan yana koymuyor. dMRI öğrenenler için engeli
azaltmanın, benchmark'tan bağımsız bir değeri var.

**Kullanılacak dürüst çerçeve:** "Bir yöntem icat etmedik. Var olan bir
karşılaştırmayı ucuza yapılabilir kılan bir enstrüman kurduk, sonra da alanın
varsayıp geçtiği bir şeyi bulacak kadar dikkatli yaptık."

---

## PART 8 — Likely questions / Muhtemel sorular

**Q: Isn't this just documentation?**
*EN:* No — documentation tells you what a command does. This measures what three
implementations actually produce on identical input, and finds they differ in a
way none of the three documentations mentions.
*TR:* Hayır — dokümantasyon bir komutun ne yaptığını söyler. Bu, üç
uygulamanın aynı girdide gerçekte ne ürettiğini ölçüyor ve üç dokümantasyonun da
bahsetmediği bir farklılık buluyor.

**Q: One subject per dataset is not enough.**
*EN:* Agreed, and we say so in Limitations. Two acquisitions are enough to show
the offset is *not fixed* — which is our claim — but not enough to characterise
how it varies. We state that establishing that would need tens of datasets, and
we have made doing so cheap.
*TR:* Katılıyorum, Limitations'ta söylüyoruz. İki edinim, kaymanın *sabit
olmadığını* göstermeye yeter — iddiamız bu — ama nasıl değiştiğini karakterize
etmeye yetmez. Bunun onlarca veri seti gerektireceğini söylüyoruz ve yapmayı
ucuzlattık.

**Q: Why no preprocessing? Real analyses always preprocess.**
*EN:* Precisely because real analyses do. Preprocessing is itself a
toolkit-specific choice; importing one tool's version into all three would
confound the comparison. Our numbers characterise the fitting stage alone, and we
say so explicitly rather than implying pipeline-level generality.
*TR:* Tam da gerçek analizler yaptığı için. Ön işleme kendisi araca özgü bir
tercih; birinin sürümünü üçüne birden sokmak karşılaştırmayı karıştırır.
Sayılarımız yalnızca uydurma aşamasını tarif ediyor ve boru hattı düzeyinde
genellik ima etmek yerine bunu açıkça söylüyoruz.

**Q: Is excluding voxels not cherry-picking?**
*EN:* The exclusion criterion is physical, not empirical: FA outside [0, 1] and
MD ≤ 0 are impossible by definition, not merely inconvenient. We report the
counts per tool as a result in its own right, and show the exclusion changes MAE
by under 2% — so it is not moving the substantive answer, only removing values
that are not measurements at all.
*TR:* Dışlama ölçütü fiziksel, ampirik değil: [0, 1] dışındaki FA ve MD ≤ 0
tanım gereği imkânsız, sadece rahatsız edici değil. Sayıları araç başına başlı
başına bir sonuç olarak raporluyoruz ve dışlamanın MAE'yi %2'den az değiştirdiğini
gösteriyoruz — yani esas cevabı oynatmıyor, sadece ölçüm bile olmayan değerleri
çıkarıyor.

**Q: Which toolkit should I use, then?**
*EN:* The paper deliberately does not crown one. MRtrix3 and DIPY are
interchangeable for tensor metrics. FSL differs, but we cannot say it is *wrong* —
we have no ground truth. What we can say is that mixing toolkits across studies
carries an unquantified risk, and that DIPY was the only one that never returned
an impossible fit.
*TR:* Makale bilerek birini taçlandırmıyor. Tensör ölçütleri için MRtrix3 ve DIPY
birbirinin yerine geçer. FSL farklı, ama *yanlış* olduğunu söyleyemeyiz — gerçek
referansımız yok. Söyleyebileceğimiz, çalışmalar arası araç karıştırmanın
nicelenmemiş bir risk taşıdığı ve DIPY'nin hiç imkânsız uydurma döndürmeyen tek
araç olduğu.

---

## Rapid recall / Hızlı hatırlama

| Cue | Say this |
|---|---|
| What is the paper? | A cross-toolkit teaching platform, plus a controlled benchmark of whether FSL, MRtrix3 and DIPY actually agree. |
| Core finding | MRtrix3 ≈ DIPY (r > 0.996). FSL offset from both, and the offset's sign flips between datasets — so it is not correctable. |
| Why two datasets? | Because one would have supported the opposite conclusion. |
| Why one shared mask? | To isolate tensor fitting from brain extraction. |
| Why the plausibility filter? | Negative eigenvalues make FA > 1 and MD < 0; a few hundred such voxels drop MD r from 0.997 to 0.118. |
| Why Bland–Altman? | Correlation cannot distinguish a systematic offset from random scatter. The FSL finding depends on it. |
| Novelty defence | The methods are standard; the question, the finding, and the reusable instrument are not. |
| Biggest limitation | One subject per dataset; tensor-fitting stage only; no preprocessing. |
