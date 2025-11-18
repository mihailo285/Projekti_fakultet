# Importovanje neophodnih biblioteka
import numpy as np
import matplotlib.pyplot as plt
import random

# Definišu se konstante koje opisuju fizički sistem i simulaciju.
gravitacija = 9.81  # Ubrzanje zemljine teže (m/s^2)
masa_stapa = 0.1  # Masa štapa (kg)
masa_kolica = 1.0  # Masa kolica (kg)
duzina_stapa = 0.5  # Polovina dužine štapa (m)
k = 1/3
vremenski_korak = 0.02  # Dužina jednog diskretnog vremenskog koraka (s). Manji korak = preciznija simulacija.

# Definicija prostora mogućih akcija koje agent može da preduzme.
akcije = [-10, 10]  # Agent može da primeni silu od -10N (guranje ulevo) ili +10N (guranje udesno).

# --- JEDNAČINE KRETANJA (FIZIKA SISTEMA) ---
# Ove funkcije modeliraju fiziku inverznog klatna. Na osnovu trenutnog stanja i primenjene sile,
# one izračunavaju kako će se sistem ponašati (ubrzanje štapa i kolica).

# Funkcija za izračunavanje ugaonog ubrzanja (θ¨) štapa.
def funkcija_ugaona(stanje, sila):
    # Raspakivanje vektora stanja radi lakšeg korišćenja
    pozicija, brzina, ugao, ugaona_brzina = stanje
    kos = np.cos(ugao)  # Kosinus trenutnog ugla
    sin = np.sin(ugao)  # Sinus trenutnog ugla

    # Formula izvedena iz Njutnovih zakona kretanja za rotaciju.
    # Ona opisuje kako gravitacija i primenjena sila utiču na rotaciju štapa.
    brojilac = gravitacija * sin - kos * (sila + masa_stapa * duzina_stapa * ugaona_brzina ** 2 * sin) / (
                masa_kolica + masa_stapa)
    imenilac = duzina_stapa * (4 / 3 - masa_stapa * kos ** 2 / (masa_kolica + masa_stapa))

    return brojilac / imenilac

# Funkcija za izračunavanje linearnog ubrzanja (x¨) kolica.
def funkcija_pomeraj(stanje, sila):
    # Raspakivanje vektora stanja
    pozicija, brzina, ugao, ugaona_brzina = stanje
    kos = np.cos(ugao)
    sin = np.sin(ugao)

    # Ova formula je takođe izvedena iz Njutnovih zakona (za translaciju).
    # Bitno je da se oslanja na rezultat ugaonog ubrzanja, jer su kretanja povezana.
    privremeno = (sila + masa_stapa * duzina_stapa * ugaona_brzina ** 2 * sin)
    ugaono_ubrzanje = funkcija_ugaona(stanje, sila)  # Ponovni poziv da bi se dobilo trenutno ugaono ubrzanje

    return (privremeno - masa_stapa * duzina_stapa * ugaono_ubrzanje * kos) / (masa_kolica + masa_stapa)

# --- SIMULACIJA KORAKA ---
# Ova funkcija pomera sistem za jedan mali vremenski interval unapred.
def simuliraj_korak(stanje, sila):
    # Raspakivanje trenutnog stanja
    pozicija, brzina, ugao, ugaona_brzina = stanje

    # Primena Eulerove metode za numeričku integraciju.
    # novo_stanje = staro_stanje + vremenski_korak * izvod_starog_stanja

    # Izračunavanje novih vrednosti za svaku komponentu stanja.
    # Ubrzanja se prvo izračunavaju na osnovu TRENUTNOG stanja.
    ubrzanje_kolica = funkcija_pomeraj(stanje, sila)
    ugaono_ubrzanje = funkcija_ugaona(stanje, sila)

    # Ažuriranje brzina
    nova_brzina = brzina + vremenski_korak * ubrzanje_kolica
    nova_ugaona_brzina = ugaona_brzina + vremenski_korak * ugaono_ubrzanje

    # Ažuriranje pozicija
    nova_pozicija = pozicija + vremenski_korak * nova_brzina  # Koristi se nova brzina za veću preciznost (Semi-implicit Euler)
    novi_ugao = ugao + vremenski_korak * nova_ugaona_brzina

    # Vraćanje novog stanja sistema kao tuple (n-torka).
    return (nova_pozicija, nova_brzina, novi_ugao, nova_ugaona_brzina)

# --- DISKRETIZACIJA PROSTORA STANJA ---
# Pošto Q-learning u tabelarnoj formi ne može da radi sa kontinualnim vrednostima (beskonačno mnogo stanja),
# moramo kontinualni prostor stanja (pozicija, brzina, itd.) podeliti u konačan broj "kanti" ili diskretnih stanja.
def diskretizuj_stanje(stanje):
    # Definišemo granice i broj kanti za svaku komponentu stanja.
    granice = [np.linspace(-2.4, 2.4, 20),  # 20 kanti za poziciju od -2.4 do 2.4
               np.linspace(-2, 2, 20),  # 20 kanti za brzinu od -2 do 2
               np.linspace(-0.2, 0.2, 20),  # 20 kanti za ugao od -0.2 do 0.2 radijana (~12 stepeni)
               np.linspace(-2, 2, 20)]  # 20 kanti za ugaonu brzinu od -2 do 2

    # Za svaku kontinualnu vrednost iz stanja, 'np.digitize' pronalazi u koju kantu (po indeksu) ona upada.
    # Rezultat je n-torka celih brojeva (npr. (10, 8, 11, 9)) koja jedinstveno identifikuje stanje.
    diskretizovano = tuple(int(np.digitize(vrednost, granica)) for vrednost, granica in zip(stanje, granice))
    return diskretizovano

# --- FUNKCIJA NAGRADE ---
# Ova funkcija daje agentu povratnu informaciju o tome koliko je dobar bio njegov potez.
def izracunaj_nagradu(stanje):
    ugao = stanje[2]  # Uzimamo samo ugao iz vektora stanja

    # Proveravamo da li je sistem u "terminalnom" (neuspešnom) stanju.
    # Ugao od 12 stepeni se često koristi kao granica neuspeha.
    if abs(ugao) >= np.radians(12):
        return -1000  # Velika negativna nagrada (kazna) za pad štapa.

    # Ako štap nije pao, agent dobija malu pozitivnu nagradu.
    # Ovo ga motiviše da ostane u ispravnom stanju što je duže moguće.
    return 1

# --- Q-LEARNING PODEŠAVANJA I ALGORITAM ---
q_tabela = {}  # Q-tabela, implementirana kao rečnik (dictionary). Ključevi su (stanje, akcija), vrednosti su Q-vrednosti.
faktor_ucenja = 0.1  # Alfa: Koliko brzo agent uči (koliko nova informacija menja staru).
faktor_diskonta = 0.99  # Gama: Koliko su buduće nagrade važne. Vrednost blizu 1 znači da agent misli dugoročno.
verovatnoca_istrazivanja = 0.1  # Epsilon: Početna verovatnoća da će agent izabrati nasumičnu akciju (istraživanje) umesto najbolje poznate (iskorišćavanje).
uspesne_epizode_zaredom = 0  # Brojač za praćenje uzastopnih uspešnih epizoda.

# Pomoćna funkcija za bezbedno preuzimanje Q-vrednosti iz tabele.
def uzmi_q_vrednost(stanje, akcija):
    # .get() metoda vraća vrednost za ključ, a ako ključ ne postoji, vraća podrazumevanu vrednost (ovde 0.0).
    # Ovo sprečava greške kada agent prvi put naiđe na neko stanje.
    return q_tabela.get((stanje, akcija), 0.0)

# Funkcija koja implementira epsilon-greedy politiku za izbor akcije.
def izaberi_akciju(stanje):
    # Generiše se nasumičan broj između 0 i 1.
    if random.random() < verovatnoca_istrazivanja:
        # ISTRAŽIVANJE (Exploration): Bira se nasumična akcija.
        # posto je nama epsilon (verovatnoca_istrazivanja) 0.1, onda će ovaj uslov biti tačan u 10% slučajeva
        return random.choice(akcije)  # Ova funkcija uzima listu akcije (koja sadrži [-10, 10]) i nasumično bira jedan od elemenata
    else:
        # ISKORIŠĆAVANJE (Exploitation): Bira se akcija koja ima najveću Q-vrednost za dato stanje.
        vrednosti = [uzmi_q_vrednost(stanje, a) for a in akcije]
        return akcije[np.argmax(vrednosti)]

# --- GLAVNA PETLJA ZA TRENIRANJE ---
broj_epizoda = 1000  # Ukupan broj epizoda (pokušaja balansiranja) koje će agent proći.
maksimalni_koraci = 500  # Maksimalan broj koraka unutar jedne epizode pre nego što se proglasi uspešnom.
nagrade_po_epizodi = []  # Lista za čuvanje ukupne nagrade za svaku epizodu (koristi se za crtanje grafika).

brojac_stabilnih_ispisa = 0  # Brojač za praćenje uzastopnih stabilnih ispisa
PRAG_ZA_ZAUSTAVLJANJE = 10      # Koliko uzastopnih stabilnih ispisa je potrebno za prekid

prosecne_nagrade = []
prozor_za_prosek = 100

# Petlja koja se izvršava za svaku epizodu.
for epizoda in range(broj_epizoda):
    # Postepeno smanjivanje verovatnoće istraživanja (epsilon decay).
    # Kako agent uči, sve se više oslanja na naučeno znanje.
    if uspesne_epizode_zaredom < 3:
        verovatnoca_istrazivanja = max(0.01, verovatnoca_istrazivanja * 0.995)

    # Resetovanje sistema na početno stanje na početku svake epizode.
    stanje = (0.0, 0.0, 0.0, 0.0)
    diskretizovano_stanje = diskretizuj_stanje(stanje)
    ukupna_nagrada = 0

    # Petlja koja se izvršava za svaki korak unutar jedne epizode.
    for korak in range(maksimalni_koraci):
        # 1. Agent bira akciju na osnovu trenutnog stanja.
        akcija = izaberi_akciju(diskretizovano_stanje)

        # 2. Simulacija izvršava tu akciju i vraća novo stanje sistema.
        novo_stanje = simuliraj_korak(stanje, akcija)
        novo_diskretizovano_stanje = diskretizuj_stanje(novo_stanje)

        # 3. Izračunava se nagrada za prelazak u novo stanje.
        nagrada = izracunaj_nagradu(novo_stanje)

        # 4. Ažuriranje Q-tabele pomoću Bellmanove jednačine (srž Q-learninga).
        stara_q = uzmi_q_vrednost(diskretizovano_stanje, akcija)
        maksimalna_nova_q = max([uzmi_q_vrednost(novo_diskretizovano_stanje, a) for a in akcije])

        # Formula za ažuriranje: NovaQ = StaraQ + alfa * (nagrada + gama * max(Q_sledece) - StaraQ)
        q_tabela[(diskretizovano_stanje, akcija)] = stara_q + faktor_ucenja * (
                    nagrada + faktor_diskonta * maksimalna_nova_q - stara_q)

        # 5. Prebacivanje u novo stanje za sledeći korak.
        stanje = novo_stanje
        diskretizovano_stanje = novo_diskretizovano_stanje
        ukupna_nagrada += nagrada

        # Ako je epizoda završena (štap je pao), prekida se unutrašnja petlja.
        if nagrada == -1000:
            break

    # Pametna logika: ako je agent uspešan 3 puta zaredom, gasi se istraživanje.
    if ukupna_nagrada >= maksimalni_koraci:  # Proverava da li je epizoda bila uspešna
        uspesne_epizode_zaredom += 1
    else:
        uspesne_epizode_zaredom = 0

    if uspesne_epizode_zaredom >= 3:
        verovatnoca_istrazivanja = 0.0

    # Čuvanje rezultata i ispisivanje napretka na svakih 25 epizoda.
    nagrade_po_epizodi.append(ukupna_nagrada)

    prosek_nagrada = np.mean(nagrade_po_epizodi[-prozor_za_prosek:])
    prosecne_nagrade.append(prosek_nagrada)

    if (epizoda + 1) % 25 == 0:
        print(f"Epizoda {epizoda + 1}: {ukupna_nagrada} koraka, Epsilon: {verovatnoca_istrazivanja:.3f}")

        # Provera da li je ispis stabilan (maksimalni koraci i epsilon na minimumu)
        if ukupna_nagrada >= maksimalni_koraci and verovatnoca_istrazivanja == 0.0:
            brojac_stabilnih_ispisa += 1
        else:
            # Ako ispis nije stabilan, resetujemo brojač
            brojac_stabilnih_ispisa = 0

        # Ako je brojač dostigao prag, prekini trening
        if brojac_stabilnih_ispisa >= PRAG_ZA_ZAUSTAVLJANJE:
            print(f"\nTrening se prekida nakon epizode {epizoda + 1} jer su performanse stabilne.")
            break

# --- PRIKAZ REZULTATA ---
# Korišćenje matplotlib biblioteke za crtanje grafika koji pokazuje napredak učenja.
plt.plot(nagrade_po_epizodi, label='Nagrada po epizodi (sirovi podaci)', alpha=0.4)
# Iscrtavanje pokretnog proseka koji jasno pokazuje trend učenja
plt.plot(prosecne_nagrade, label=f'Prosečna nagrada (prozor od {prozor_za_prosek} epizoda)', color='red', linewidth=2)
plt.xlabel("Epizoda")
plt.ylabel("Ukupna nagrada (broj koraka pre pada)")
plt.title("Napredak učenja Q-learning agenta")
plt.grid(True)  # Dodaje mrežu na grafik radi lakšeg čitanja
plt.legend(loc='lower right', fontsize=5)
plt.show()  # Prikazuje prozor sa grafikom```

