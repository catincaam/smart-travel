# Smart Travel - Explicatii Pipeline Si Machine Learning

Acest document explica pas cu pas ce face proiectul Smart Travel.

Ideea principala:

```text
Nu am luat un dataset gata facut si am pus direct un model.
Am construit un pipeline complet de Data Science.
```

Pipeline-ul este:

```text
destinatii brute
    -> coordonate
    -> vreme
    -> puncte de interes
    -> feature engineering
    -> EDA
    -> Machine Learning
```

## 1. collect_base_data.py

Fisier:

- `src/collect_base_data.py`

Input:

- `data/raw/european_destinations.csv`

Fisierul de input contine:

```text
destination_name
search_name
country
```

Ce inseamna coloanele:

```text
destination_name = numele destinatiei pe care il vede utilizatorul
search_name      = numele folosit pentru cautare mai precisa in API
country          = tara
```

Exemplu:

```text
destination_name = Kefalonia
search_name = Argostoli
country = Greece
```

De ce avem `search_name`?

Pentru unele destinatii, numele este prea general. Kefalonia este o insula, nu
un punct exact. Pentru coordonate mai bune, folosim un oras reprezentativ, cum
este Argostoli.

### Pasul 1 - Geocoding

Scriptul intreaba API-ul Nominatim:

```text
Unde este Argostoli, Greece?
```

Nominatim cauta in OpenStreetMap si raspunde cu coordonate:

```json
{
  "lat": 38.18,
  "lon": 20.48
}
```

Noi salvam:

```text
latitude
longitude
```

Deci din:

```text
Kefalonia, Argostoli, Greece
```

obtinem:

```text
Kefalonia, Greece, 38.18, 20.48
```

### Pasul 2 - Weather

Dupa ce avem coordonatele, mergem la Open-Meteo.

Intrebam API-ul:

```text
Cum a fost vremea aici intre 2023 si 2025?
```

Open-Meteo raspunde cu valori zilnice:

```text
temperatura medie zilnica
precipitatii zilnice
```

Noi nu pastram fiecare zi separat. Calculam medii pe anotimpuri:

```text
winter_avg_temp
spring_avg_temp
summer_avg_temp
autumn_avg_temp

winter_avg_daily_rain
spring_avg_daily_rain
summer_avg_daily_rain
autumn_avg_daily_rain
```

Rezultatul este primul dataset imbogatit:

- `data/processed/destinations_enriched_weather.csv`

Pe scurt:

```text
destinatii brute
    -> Nominatim pentru coordonate
    -> Open-Meteo pentru vreme
    -> dataset cu coordonate + vreme
```

## 2. collect_places.py

Fisier:

- `src/collect_places.py`

Aici colectam ce exista in jurul fiecarei destinatii.

Important:

```text
Nu folosim un dataset gata facut.
Folosim un API.
```

API-ul este:

```text
Overpass API
```

Overpass citeste date din:

```text
OpenStreetMap
```

### Ce intrebam API-ul?

Pentru fiecare destinatie avem coordonate:

```text
latitude
longitude
```

Exemplu pentru Kefalonia / Argostoli:

```text
latitude = 38.18
longitude = 20.49
```

Scriptul intreaba:

```text
Intr-o raza de 3 km in jurul acestor coordonate,
cate restaurante exista?
```

Overpass cauta in OpenStreetMap obiecte de tip:

```text
amenity=restaurant
```

Si raspunde cu un numar:

```text
44
```

Noi salvam:

```text
restaurant_count = 44
```

Apoi intrebam:

```text
Cate cafenele exista?
```

Cauta:

```text
amenity=cafe
```

Si salvam:

```text
cafe_count
```

Facem acelasi lucru pentru:

```text
restaurant_count -> amenity=restaurant
cafe_count       -> amenity=cafe
bar_count        -> amenity=bar
museum_count     -> tourism=museum
park_count       -> leisure=park
beach_count      -> natural=beach
```

Aceste valori nu sunt inventate. Ele vin din OpenStreetMap.

Exemplu:

```text
Kefalonia:
restaurant_count = 44
cafe_count = 21
bar_count = 13
museum_count = 5
park_count = 4
beach_count = 13
```

### De ce folosim raza de 3 km?

Pentru ca vrem sa vedem ce exista in jurul punctului reprezentativ al
destinatiei.

Nu intrebam:

```text
Cate restaurante exista in toata Grecia?
```

Ci:

```text
Cate restaurante exista in jurul orasului Argostoli?
```

Asta face datele mai relevante pentru un turist.

### Problema descoperita

La inceput, unele destinatii aveau valori 0.

Exemplu:

```text
Kefalonia = 0 restaurante
Mallorca = 0 restaurante
```

Asta nu avea sens.

Problema nu era OpenStreetMap. Problema era geocoding-ul.

Pentru insule/regiuni, coordonatele erau prea generale. De aceea am introdus:

```text
search_name
```

Exemple:

```text
Kefalonia -> Argostoli
Mallorca -> Palma de Mallorca
Sardinia -> Cagliari
Cinque Terre -> Monterosso al Mare
```

Dupa asta, rezultatele au devenit mult mai bune.

### Output

Scriptul produce:

- `data/processed/destinations_with_places.csv`

Acesta contine:

```text
destinatii
coordonate
vreme
restaurant_count
cafe_count
bar_count
museum_count
park_count
beach_count
food_score
nightlife_score
culture_score
nature_score
beach_score
```

## 3. Scorurile

Dupa ce avem count-uri, construim scoruri mai usor de interpretat.

Exemplu:

```text
restaurant_count
cafe_count
```

devin:

```text
food_score
```

Ideea este:

```text
food_score = cat de puternica este scena de food a destinatiei
```

Similar:

```text
bar_count    -> nightlife_score
museum_count -> culture_score
park_count   -> nature_score
beach_count  -> beach_score
```

Important:

```text
Scorurile sunt pentru interpretare si produs.
Pentru Machine Learning putem folosi count-urile brute, dar standardizate.
```

Limitare:

```text
Scorurile actuale sunt relative la dataset.
Daca adaugam destinatii foarte mari, cum ar fi Tokyo sau New York,
maximele se schimba si scorurile se pot recalcula.
```

Pentru V1 este acceptabil. Pentru V2 putem folosi percentile, log scaling sau
density features.

## 3.5 Preference Translation

La inceput, motorul de recomandare primea direct scoruri numerice:

```text
food = 8
beach = 9
culture = 3
nature = 6
nightlife = 4
```

Acest lucru era simplu pentru cod, dar mai putin natural pentru utilizator.

Dashboard-ul a fost schimbat astfel incat utilizatorul sa raspunda in limbaj
mai apropiat de turism:

```text
Trip type: Beach Holiday
Travelling with: Partner
Budget: Medium
Preferred weather: Warm
Must-do activities: Beach, Local food
Free text: I want a warm beach destination with good food.
```

Acum exista un pas intermediar:

```text
User answers
    ->
Preference Translator
    ->
food / beach / culture / nature / nightlife signals
    ->
Recommendation Engine
```

Fisier:

- `src/preference_translation.py`

Acest modul transforma raspunsurile naturale in scoruri interne.

Exemple:

```text
Beach Holiday -> beach creste mult
Local food    -> food creste
Museums       -> culture creste
Nature        -> nature creste
Friends       -> nightlife si food cresc
Family        -> nature/culture cresc, nightlife scade
```

Important:

```text
UI-ul nu mai trimite direct scoruri numerice.
UI-ul trimite raspunsuri naturale, iar codul le traduce in scoruri numerice.
```

Aceasta separare face proiectul mai curat:

- dashboard-ul se ocupa de experienta utilizatorului;
- `preference_translation.py` se ocupa de traducerea raspunsurilor;
- `recommend.py` se ocupa de calculul recomandarilor.

## 4. feature_engineering.py

Fisier:

- `src/feature_engineering.py`

Acest script transforma datele brute in features mai semantice.

Adica trecem de la:

```text
summer_avg_temp = 27.01
```

la:

```text
warm_destination = True
summer_destination = True
climate_category = Warm
```

Exemplu:

Daca:

```text
summer_avg_temp >= 24
```

atunci:

```text
warm_destination = True
```

Daca:

```text
summer_avg_temp >= 24
si
summer_avg_daily_rain <= 1.5
```

atunci:

```text
summer_destination = True
```

Alte features create:

```text
island_destination
mountain_destination
coastal_destination
city_destination
rain_risk
overall_score
balanced_destination
dominant_travel_style
```

Exemple:

```text
Kefalonia -> Beach
Mallorca -> Nature
Paris -> Food & Nightlife
Prague -> Culture
```

Output:

- `data/processed/destinations_feature_engineered.csv`

Acesta este datasetul pregatit pentru Machine Learning.

## 5. Machine Learning

Primul model:

```text
K-Means Clustering
```

Intrebarea:

```text
Exista grupuri naturale de destinatii turistice?
```

Noi nu ii spunem modelului:

```text
asta este beach destination
asta este city break
asta este nature destination
```

Modelul incearca singur sa grupeze destinatiile dupa asemanari.

Pentru primul K-Means folosim count-uri + vreme:

```text
restaurant_count
cafe_count
bar_count
museum_count
park_count
beach_count
summer_avg_temp
summer_avg_daily_rain
```

Aceste 8 coloane sunt pregatite de:

```text
src/prepare_ml_features.py
```

Scriptul produce:

```text
data/processed/ml_features_raw.csv
data/processed/ml_features_scaled.csv
data/processed/ml_feature_scaling_summary.csv
```

`ml_features_raw.csv` pastreaza valorile originale care intra in model.

Exemplu:

```text
Kefalonia:
restaurant_count = 44
beach_count = 13
summer_avg_temp = 27.01
```

`ml_features_scaled.csv` contine aceleasi coloane dupa standardizare.

`ml_feature_scaling_summary.csv` arata media si deviatia standard inainte si
dupa scalare.

### De ce nu folosim direct scorurile?

Pentru primul model vrem sa pornim de la datele de baza:

```text
count-uri reale din OpenStreetMap
vreme reala din Open-Meteo
```

Scorurile raman utile pentru:

```text
interpretare
aplicatie
recomandari explicabile
afisare catre utilizator
```

### De ce standardizam?

Valorile au scari diferite.

Exemplu:

```text
restaurant_count poate fi 4000
summer_avg_temp poate fi 27
beach_count poate fi 13
```

Daca nu standardizam, modelul va considera ca restaurantele sunt mult mai
importante doar pentru ca numerele sunt mai mari.

Standardizarea face ca toate variabilele sa fie comparabile.

Folosim:

```python
StandardScaler()
```

Dupa standardizare:

```text
media fiecarei coloane este aproximativ 0
deviatia standard a fiecarei coloane este aproximativ 1
```

Exemplu din proiect:

```text
restaurant_count:
media inainte de scalare = 798.7
media dupa scalare = aproximativ 0
std dupa scalare = 1

summer_avg_temp:
media inainte de scalare = 22.91
media dupa scalare = aproximativ 0
std dupa scalare = 1
```

Dupa standardizare, aplicam:

```python
KMeans()
```

Apoi folosim PCA ca sa vizualizam clusterele in 2D.

### Cum alegem numarul de clustere?

La K-Means trebuie sa alegem `k`, adica numarul de grupuri.

Nu alegem acest numar la intamplare. Testam mai multe variante:

```text
k = 2, 3, 4, 5, 6
```

Pentru fiecare varianta verificam:

```text
inertia
silhouette_score
```

Rezultatele obtinute:

```text
k   silhouette_score
2   0.4102
3   0.2923
4   0.2730
5   0.2442
6   0.2307
```

Din punct de vedere statistic, cea mai buna varianta este:

```text
k = 2
```

Pentru ca are cel mai mare `silhouette_score`.

Dar apoi ne uitam si la interpretarea de business.

Cu `k = 2`, modelul separa destul de clar:

```text
orase mari / urbane
vs
destinatii mai mici / coastal / nature
```

Este corect statistic, dar cam prea general pentru un produs de travel.

Cu `k = 3`, modelul separa mai bine destinatiile in profiluri utile:

```text
Urban Culture & Food
Cool Balanced & Nature
Warm Coastal & Beach
```

De aceea, pentru V1 folosim `k = 3` ca model principal de produs.

Explicatia este:

```text
Although k=2 achieved the highest silhouette score, the resulting clusters were
too broad to provide meaningful travel profiles. The k=3 solution produced more
interpretable and actionable destination groups while still maintaining
acceptable cluster separation. Since Smart Travel is designed as a recommendation
system, interpretability and usefulness for end users were prioritized over
achieving the highest clustering metric.
```

Aceasta este o decizie normala in Data Science: nu alegem doar dupa metrici, ci
si dupa cat de bine poate fi folosit rezultatul in produs.

## 6. Recommendation Engine V1

Fisier:

- `src/recommend.py`

Dupa K-Means, proiectul are primul model de Machine Learning.

Dar K-Means nu face recomandari direct.

K-Means raspunde la intrebarea:

```text
Ce destinatii seamana intre ele?
```

Recommendation Engine raspunde la alta intrebare:

```text
Ce destinatii se potrivesc cel mai bine preferintelor utilizatorului?
```

Inputul este un set de preferinte:

```text
food
beach
culture
nature
nightlife
travel_month
```

Exemplu:

```text
food = 8
beach = 9
culture = 3
nature = 6
nightlife = 4
travel_month = August
```

Pentru V1 folosim un content-based recommender.

Adica nu avem nevoie de ratinguri de la utilizatori. Folosim caracteristicile
destinatiilor si le comparam cu preferintele utilizatorului.

### De ce nu folosim direct K-Means pentru recomandare?

Pentru ca un cluster este doar un grup.

Exemplu:

```text
Warm Coastal & Beach
```

Acest lucru ne spune ca destinatiile din acel grup seamana intre ele, dar nu ne
spune automat care este cea mai buna destinatie pentru un anumit utilizator.

Recommendation Engine calculeaza un scor separat pentru fiecare destinatie.

### Cum calculeaza scorul?

Motorul foloseste mai multe componente:

```text
preference_score
weather_score
cost_score
cluster_bonus
must_have_penalty
```

Formula V1:

```text
recommendation_score =
    0.60 * preference_score
  + 0.20 * weather_score
  + 0.15 * cost_score
  + cluster_bonus
  - must_have_penalty
```

`preference_score` compara preferintele utilizatorului cu semnalele fiecarei
destinatii.

Important:

```text
Pentru recomandare folosim percentile/rank signals, nu doar scorurile min-max.
```

De ce?

Pentru ca scorurile min-max pot fi dominate de orase foarte mari.

Exemplu:

```text
Paris poate avea foarte multe restaurante,
dar asta nu inseamna ca este cea mai buna alegere pentru beach = 9.
```

De aceea, in recommender folosim semnale mai robuste:

```text
food_recommendation_signal
nightlife_recommendation_signal
culture_recommendation_signal
nature_recommendation_signal
beach_recommendation_signal
```

Acestea sunt calculate cu percentile rank peste count-uri.

`weather_score` foloseste luna aleasa de utilizator si o transforma in anotimp:

```text
August -> summer
October -> autumn
January -> winter
```

Apoi verifica:

```text
temperatura medie
precipitatiile medii zilnice
```

`cluster_bonus` adauga un mic avantaj daca profilul destinatiei se potriveste cu
preferinta principala.

Exemplu:

```text
Daca beach >= 7 si destinatia este in Warm Coastal & Beach,
primeste un bonus.
```

`budget_match_score` compara doua lucruri diferite:

```text
Budget preference = ce alege utilizatorul in interfata
Travel cost level / cost_level = cat de scumpa este destinatia
Budget match score = cat de bine se potrivesc cele doua
```

In V1:

```text
cost_score = budget_match_score
```

Am pastrat ambele nume deoarece `budget_match_score` explica metoda de calcul,
iar `cost_score` explica rolul in formula finala.

Exemplu:

```text
Utilizatorul alege Low (Essential)
Destinatia are cost_level = Luxury
=> budget_match_score = 25

Utilizatorul alege High (Luxury)
Destinatia are cost_level = Luxury
=> budget_match_score = 100
```

Matricea V1 este:

```text
                  Budget destination   Mid-range destination   Luxury destination
Low user                 100                    65                     25
Medium user               75                   100                     70
High user                 60                    85                    100
```

Nu penalizam prea agresiv destinatiile bune, pentru ca datele de cost sunt inca
un proxy, nu preturi turistice reale.

Important:

```text
In implementarea actuala, cost_level este bazat in principal pe fallback-ul
cost_of_living_index.

travel_cost_index real este pregatit pentru V2, dar are nevoie de API keys
Numbeo si Amadeus.
```

`must_have_penalty` scade scorul daca utilizatorul cere ceva important, dar
destinatia nu ofera acel lucru.

Exemplu:

```text
Daca beach = 9 si destinatia are beach signal foarte mic,
primeste penalty.
```

### Output

Motorul returneaza:

```text
destination_name
country
recommendation_score
preference_score
weather_score
cost_score
budget_match_score
cost_level
cluster_profile
explanation
```

Exemplu de explicatie:

```text
strong beach match; good summer weather; belongs to Warm Coastal & Beach
```

Outputul de test este salvat in:

```text
data/processed/recommendation_sample.csv
```

## 7. FastAPI

Fisier:

- `src/api.py`

Pana acum, recommendation engine putea fi rulat din terminal:

```text
python src/recommend.py --food 8 --beach 9 --culture 3 --nature 6 --nightlife 4 --month August
```

FastAPI transforma aceasta logica intr-un API.

Adica aplicatia web nu va rula scripturi manual. Va trimite un request catre
backend.

Endpoint principal:

```text
POST /recommend
```

Input JSON:

```json
{
  "food": 8,
  "beach": 9,
  "culture": 3,
  "nature": 6,
  "nightlife": 4,
  "month": "August",
  "top_n": 5
}
```

API-ul transforma acest JSON in preferinte, apeleaza functia:

```python
recommend_destinations()
```

si returneaza rezultatul tot in JSON.

Output JSON:

```text
travel_month
season
preferences
recommendations
```

Fiecare recomandare contine:

```text
destination_name
country
recommendation_score
preference_score
weather_score
cluster_profile
dominant_travel_style
climate_category
explanation
natural_reason
reason
```

`explanation` este o explicatie scurta.

`natural_reason` este o propozitie mai naturala, potrivita pentru utilizator.

`reason` este explicatia structurata a recomandarii:

```json
{
  "weather": 89.98,
  "food": 65.0,
  "beach": 72.5,
  "culture": 45.0,
  "nature": 85.0,
  "nightlife": 65.0,
  "cluster_bonus": 5.0,
  "must_have_penalty": 0.0
}
```

Aceasta face sistemul explicabil. Utilizatorul nu primeste doar o destinatie, ci
vede si de ce a fost recomandata.

Comanda pentru pornirea API-ului:

```text
uvicorn src.api:app --reload
```

Dupa pornire, documentatia interactiva apare automat la:

```text
http://127.0.0.1:8000/docs
```

Acesta este pasul in care Smart Travel devine un produs utilizabil de un
frontend.

## 8. EDA notebooks

EDA inseamna:

```text
Exploratory Data Analysis
```

Adica etapa in care ne uitam la date ca sa le intelegem inainte sa aplicam
Machine Learning.

In aceasta etapa nu colectam date noi si nu antrenam modelul. Verificam daca
datasetul are sens.

Notebook-urile EDA sunt:

```text
02_exploratory_data_analysis.ipynb
03_feature_validation.ipynb
```

Ele raspund la intrebari precum:

```text
Avem valori lipsa?
Valorile par corecte?
Exista destinatii suspecte?
Care destinatii au cele mai multe restaurante?
Care destinatii au cele mai multe plaje?
Care destinatii au cel mai bun food_score?
Exista legatura intre restaurante si baruri?
Paris si Barcelona domina datasetul?
Feature-urile create au sens?
```

Exemplu concret:

```text
Daca vedem ca Kefalonia are 0 restaurante,
inseamna ca ceva este suspect.
```

In cazul nostru, EDA si validarea datelor ne-au ajutat sa descoperim ca problema
nu era OpenStreetMap, ci coordonatele prea generale pentru insule si regiuni.
De aceea am introdus `search_name`.

Alt exemplu:

```text
Daca Paris are foarte multe restaurante, cafenele si baruri,
trebuie sa intelegem ca Paris poate domina count-urile pentru ca este un oras mare.
```

Aceasta observatie este importanta inainte de ML, pentru ca modelul ar putea
invata prea mult din marimea oraselor, nu neaparat din tipul experientei
turistice.

Pe scurt:

```text
EDA = verificam, exploram si interpretam datele inainte sa construim modelul.
```

## 9. Notebook-uri

Notebook-urile explica fiecare etapa:

```text
01_data_exploration.ipynb
02_exploratory_data_analysis.ipynb
03_feature_validation.ipynb
04_machine_learning.ipynb
```

`04_machine_learning.ipynb` este structurat asa:

```text
Question
Method
Feature Selection
Standardization
Choosing k
Model
Interpretation
PCA Visualization
Save Output
```

## 10. Interactive Map

Fisier:

- `src/create_interactive_map.py`

Output:

- `maps/smart_travel_map.html`

Aceasta etapa creeaza o harta interactiva cu Folium.

Scopul hartii este sa faca proiectul usor de demonstrat vizual.

Pe harta avem cate un marker pentru fiecare destinatie.

Exista trei layer-e:

```text
Summer Weather Score
Beach Score
Culture Score
```

Fiecare layer coloreaza marker-ele dupa scor:

```text
80+      = scor puternic
50-79    = scor mediu
sub 50   = scor mai slab
```

Popup-ul fiecarei destinatii arata:

```text
destination_name
country
cluster_profile
dominant_travel_style
weather score
food score
beach score
culture score
nature score
summer temperature
summer rain
```

Aceasta harta este utila pentru portofoliu deoarece arata imediat ca proiectul
nu este doar un notebook, ci un sistem care produce rezultate vizuale si
interpretabile.

## 11. Streamlit Dashboard

Fisier:

- `dashboard/streamlit_app.py`

Scop:

```text
Sa transforme motorul de recomandare intr-o interfata interactiva.
```

Dashboard-ul nu cere utilizatorului sa gandeasca in scoruri numerice precum
`food = 8` sau `beach = 9`.

In schimb, pune intrebari mai naturale:

```text
When are you travelling?
What kind of trip are you looking for?
Who are you travelling with?
What do you want to do on your trip?
Describe your ideal trip
```

In spate, aceste raspunsuri sunt traduse in aceleasi preferinte numerice de care
are nevoie motorul de recomandare:

```text
Relaxing beach holiday -> beach ridicat
City break             -> culture + food ridicat
Nature and hiking      -> nature ridicat
Food and wine          -> food ridicat
Nightlife with friends -> nightlife ridicat
```

Regulile de traducere sunt tinute in dictionare in
`PREFERENCE_TRANSLATION_RULES`, nu imprastiate in multe `if`-uri. Asta face
logica mai usor de citit, modificat si explicat.

`Who are you travelling with?` nu este doar text in UI. Raspunsul schimba
preferintele interne:

```text
Solo    -> culture +2, food +1
Partner -> beach +2, food +2, nightlife +1
Friends -> nightlife +3, food +2
Family  -> nature +2, culture +1, nightlife -2
```

De exemplu, daca doua persoane aleg acelasi tip de vacanta, dar una merge cu
partenerul si alta cu prietenii, sistemul poate produce ranking diferit deoarece
preferintele finale trimise catre recommendation engine nu mai sunt identice.

`Preferred weather` este tratat separat prin `weather_score`:

```text
Warm -> scor maxim in jur de 27C
Mild -> scor maxim in jur de 21C
Cool -> scor maxim in jur de 15C
Any  -> foloseste o temperatura confortabila inferata din intentia calatoriei
```

Nu folosim doar praguri rigide. Folosim o curba de confort: destinatia primeste
scor mare cand temperatura este aproape de ideal si scorul scade treptat pe
masura ce temperatura se indeparteaza.

Acest scor meteo contribuie 20% la `recommendation_score`.

Campul liber `Describe your ideal trip` foloseste keyword extraction simplu.
Exemplu:

```text
warm beach with good food
```

este interpretat ca:

```text
beach +3
food +3
weather_preference = Warm, daca userul a lasat Preferred weather = Any
```

Aceasta nu este inca NLP avansat. Este o etapa intermediara explicabila intre
formular simplu si o viitoare versiune cu model NLP/LLM.

Pentru a nu depinde de cuvinte exacte, extractorul foloseste:

```text
sinonime
expresii scurte
fuzzy matching pentru typo-uri mici
```

Exemplu:

```text
weather good enough to go for a hike
```

este interpretat ca:

```text
nature +3
weather_preference = Mild
```

Chiar si typo-ul `wether good enough to go for a hike` este tratat similar.

Dashboard-ul include:

```text
selectbox pentru luna
radio pentru tipul de vacanta
radio pentru companion
multiselect pentru activitati
camp text pentru descrierea calatoriei ideale
Top N recomandari
explicatii naturale
reason scores
harta interactiva
tabel cu datasetul
```

Dashboard-ul foloseste direct functia:

```python
recommend_destinations()
```

Deci nu dubleaza logica. Aceeasi logica este folosita de:

```text
scriptul din terminal
FastAPI
Streamlit dashboard
```

Comanda de pornire:

```text
streamlit run dashboard/streamlit_app.py
```

URL local:

```text
http://127.0.0.1:8501
```

Acesta este cel mai potrivit frontend pentru versiunea Data Science a
proiectului, deoarece permite un demo rapid fara sa construim inca o aplicatie
React completa.

## Rezumat Final

Tot pipeline-ul:

```text
1. european_destinations.csv
   destinatii brute

2. collect_base_data.py
   adauga coordonate + vreme

3. collect_places.py
   adauga restaurante, cafenele, baruri, muzee, parcuri, plaje

4. feature_engineering.py
   construieste features semantice

5. EDA notebooks
   verifica daca datele sunt corecte, cauta valori suspecte,
   compara destinatii si descopera pattern-uri

6. machine_learning notebook
   aplica K-Means pentru gruparea destinatiilor

7. recommend.py
   calculeaza Top N recomandari pe baza preferintelor utilizatorului

8. api.py
   expune motorul de recomandare prin POST /recommend

9. create_interactive_map.py
   genereaza o harta Folium cu destinatiile si scorurile principale

10. streamlit_app.py
    dashboard interactiv pentru recomandari si explorarea hartii
```

Ideea principala:

```text
Acesta este un proiect end-to-end de Data Science.
Machine Learning este doar o componenta dintr-un sistem mai mare.
```
