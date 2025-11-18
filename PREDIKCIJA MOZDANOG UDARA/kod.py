# Importovanje potrebnih biblioteka
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# Modeli
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

# Importi za evaluaciju i pripremu podataka
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

# Rešavanje warninga
warnings.filterwarnings("ignore")

# Učitavanje podataka
stroke_data = pd.read_csv('healthcare-dataset-stroke-data.csv')

# Prikazujem prvih 5 redova DataFrame-a
print("Prvih 5 redova skupa podataka:")
print(stroke_data.head())
print("\n")
# Prikaz informacija o podacima i provera nedostajućih vrednosti
print("Informacije o skupu podataka:")
stroke_data.info()
print("\n")
print("Broj nedostajućih vrednosti po kolonama:")
print(stroke_data.isnull().sum())
print("\n")

# Popunjavanje nedostajućih vrednosti u bmi koloni srednjom vrednošću svih postojećih bmi vrednosti
stroke_data['bmi'] = stroke_data['bmi'].fillna(stroke_data['bmi'].mean())
# Uklanjanje id kolone jer mi nije neophodna za predikciju modela
stroke_data = stroke_data.drop(columns='id', axis=1)
# U skupu podataka je postojao jedan podatak za pol koji je bio Other pa sam ga uklonio
if 'Other' in stroke_data['gender'].unique():
    stroke_data = stroke_data[stroke_data['gender'] != 'Other']
# Nakon uklanjanja anomalija i popunjavanja nedostajućih vrednosti proverio sam da li je sve okej
print("Provera nakon popunjavanja i uklanjanja nepotrebnih podataka:")
print(stroke_data.isnull().sum())
print("\n")
# Pošto modeli mašinskog učenja ne mogu raditi sa tekstualnim podacima morao sam ih prebaciti u numeričke vrednosti
categorical_cols = ['gender', 'ever_married', 'work_type', 'Residence_type', 'smoking_status']
# Pretvorio sam svaku kategoričku kolonu u kolonu sa nulama i jedinicama kako bi modeli mogli posle da rade
stroke_data = pd.get_dummies(stroke_data, columns=categorical_cols, drop_first=True)
# Ponovo sam prikazao skup podataka
print("Skup podataka nakon preprocesiranja:")
print(stroke_data.head())
print("\n")

# Vizualizacija distribucije ciljne promenljive i njenog odnosa sa ključnim faktorima rizika (hipertenzija, srčana bolest, nivo šećera u krvi)
sns.set(style="whitegrid")
plt.rc('axes', labelsize=20)
print("Prikaz grafičke analize podataka...")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Analiza ključnih atributa u odnosu na moždani udar', fontsize=24)
sns.countplot(x='stroke', data=stroke_data, ax=axes[0, 0]).set_title('Distribucija moždanog udara (0 = Ne, 1 = Da)', fontsize = 16)
sns.countplot(x='hypertension', hue='stroke', data=stroke_data, ax=axes[0, 1]).set_title('Moždani udar po hipertenziji', fontsize = 20)
sns.countplot(x='heart_disease', hue='stroke', data=stroke_data, ax=axes[1, 0]).set_title(
    'Moždani udar po bolestima srca', fontsize = 20)
sns.histplot(data=stroke_data, x='avg_glucose_level', hue='stroke', multiple="stack", kde=True,
             ax=axes[1, 1]).set_title('Distribucija nivoa šećera i moždani udar', fontsize = 20)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

# Prikazujem Pirsonovu korelacionu matricu za sve parove atributa
plt.figure(figsize=(16, 12))
correlation_matrix = stroke_data.corr()
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Mapa korelacija između atributa', fontsize = 20)
plt.show()

# Dodeljivanje vrednosti X i Y
X = stroke_data.drop('stroke', axis=1)
Y = stroke_data['stroke']

# Podela podataka na trening i test skup, stratify omogućava da proporcija klasa bude ista u trening i test skupu
X_train_df, X_test_df, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42, stratify=Y)

# Skaliranje podataka
# Standardizacija predstavlja tehniku skaliranja koja transformiše atribute tako da imaju srednju vrednost 0 i standardnu devijaciju 1
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_df)
X_test_scaled = scaler.transform(X_test_df)

'''
    Kako bih rešio disbalans koji sam primetio vizuelno kada sam prikazao klase koristio sam SMOTE tehniku.
    Dakle broj pacijenata bez moždanog udara je bio daleko veći od onih koji su imali moždani udar
    To bi navodilo model da bude pristrasan samo tim primerima, to dovodi do visoke preciznosti i loše sposobnosti detekcije (lažna predikcija)
    SMOTE rešava ovaj problem tako što kopira manjinske uzorke tako što kreira nove, sintetičke uzorke
'''
print("\nDistribucija klasa PRE SMOTE:")
print(Y_train.value_counts())
print("\n")

smote = SMOTE(random_state=42)
X_train_resampled, Y_train_resampled = smote.fit_resample(X_train_scaled, Y_train)

print("Distribucija klasa NAKON SMOTE:")
print(pd.Series(Y_train_resampled).value_counts())
print("\n")

# Isprobavao sam više modela koristeći unakrsnu validaciju
print("Poređenje performansi različitih modela pomoću unakrsne validacije (na balansiranom skupu):")
models = {
    "Logistic Regression": LogisticRegression(class_weight='balanced'),
    "Random Forest": RandomForestClassifier(random_state=42, class_weight='balanced'),
    "Support Vector Machine": SVC(random_state=42, probability=True),  # probability=True je potrebno za roc_auc
    "K-Nearest Neighbors": KNeighborsClassifier()
}
# Inicijalizovao sam rečnik za čuvanje rezultata
results = {}
# Izvršavanje 5-struke unakrsne validacije
for name, model in models.items():
    # cv = 5 deli trening skup na 5 delova, model se trenira na 4, testira na petom i to se ponavlja 5 puta
    # roc krivu sam koristio za ocenu, idealna je za nebalansirane podatke
    scores = cross_val_score(model, X_train_resampled, Y_train_resampled, cv=5, scoring='roc_auc')
    # Izračunao sam prosečnu vrednost 5 dobijenih razultata za stabilnu procenu
    results[name] = scores.mean()
    print(f"{name}: Srednji ROC AUC = {scores.mean():.4f} (Standardna devijacija = {scores.std():.4f})")

# Sortirao sam modele na osnovu performansi
sorted_models = sorted(results.items(), key=lambda item: item[1], reverse=True)
# Izdvojio sam 3 najbolja modela
top_3_model_names = [model[0] for model in sorted_models[:3]]
print(f"\nTri najbolja modela su: {top_3_model_names}")
print("\n")

# Nakon toga sam podesio hiperparametre za modele
param_grids = {
    "Logistic Regression": {
        'C': [0.1, 1, 10], 'solver': ['liblinear'], 'class_weight': ['balanced']
    },
    "Random Forest": {
        'n_estimators': [100, 200], 'max_depth': [10, 20], 'min_samples_leaf': [1, 2], 'class_weight': ['balanced']
    },
    "Support Vector Machine": {
        'C': [1, 10], 'gamma': ['scale'], 'kernel': ['rbf'], 'probability': [True]
    },
    "K-Nearest Neighbors": {
        'n_neighbors': [5, 7, 9], 'weights': ['uniform', 'distance']
    }
}
# Inicijalizovao sam rečnik za čuvanje najbolje podešenih modela
best_estimators = {}
# Prolazim kroz 3 najbolja modela i podešavam hiperparametre
for model_name in top_3_model_names:
    print(f"Podešavanje hiperparametara za {model_name}...")
    model = models[model_name]
    param_grid = param_grids[model_name]
    # Pomoću gridsearcha pokrećem proces 5-struke unakrsne validacije tako što će ona isprobati sve kombinacije parametara iz param_grid
    grid_search = GridSearchCV(model, param_grid, cv=5, scoring='roc_auc', n_jobs=-1, verbose=1)
    # Pokrećem proces pretrage na balansiranom trening skupu
    grid_search.fit(X_train_resampled, Y_train_resampled)
    # Čuvam najbolje pronađene kombinacije modela i parametara
    best_estimators[model_name] = grid_search.best_estimator_
    print(f"Najbolji parametri za {model_name}: {grid_search.best_params_}")
    print("\n")

print("EVALUACIJA FINALNIH MODELA NA TEST SKUPU \n")
# Petlja kojom prolazim kroz svaki od 3 najbolja podešena modela
for model_name, final_model in best_estimators.items():
    # Koristim finalni model za predikciju na nevidljivom test skupu
    Y_pred = final_model.predict(X_test_scaled)
    # Prikazujem rezultate računanjem tačnosti za modele
    print(f"\nRezultati za: {model_name}")
    print(f"Tačnost (Accuracy): {accuracy_score(Y_test, Y_pred):.4f}")
    # Generišem detaljan izveštaj o klasifikaciji koji sadrži preciznost, odziv i F1-score
    print("\nIzveštaj o klasifikaciji:")
    print(classification_report(Y_test, Y_pred, target_names=['Nema moždani udar', 'Ima moždani udar']))

    # Iscrtavam matricu konfuzije kako bih prikazao gde je model bio u pravu, a gde je grešio
    conf_matrix = confusion_matrix(Y_test, Y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Greens',
                xticklabels=['Nema moždani udar', 'Ima moždani udar'],
                yticklabels=['Nema moždani udar', 'Ima moždani udar'])
    plt.xlabel('Predviđena klasa')
    plt.ylabel('Stvarna klasa')
    plt.title(f'Matrica konfuzije za {model_name} (sa SMOTE)', fontsize = 18)
    plt.show()

# Proveravam da li je Random Forest među najboljim modelima pre pokušaja analize
if "Random Forest" in best_estimators:
    print("\nZNAČAJNOST ATRIBUTA (RANDOM FOREST)\n")
    # Izdvajam najbolji model - Random Forest
    rf_model = best_estimators["Random Forest"]
    # Pristupam karakteristikama modela kako bih izlistao koja je najznačajnija bila karakteristika u predikciji
    importances = rf_model.feature_importances_
    # Uzimam imena kolona za lakše mapiranje
    feature_names = X.columns
    # Kreiram DataFrame kako bih lakše sortirao i vizualizovao rezultate
    feature_importance_df = pd.DataFrame({
        'Atribut': feature_names,
        'Značajnost': importances
    }).sort_values(by='Značajnost', ascending=False)
    # Ispisujem rezultate
    print("Značajnost atributa:")
    print(feature_importance_df)
    print("\n")
    # Vizuelni prikaz značajnosti svakog atributa pri predikciji
    plt.figure(figsize=(12, 10))
    plt.rc('axes', labelsize=18)
    sns.barplot(x='Značajnost', y='Atribut', data=feature_importance_df, palette='viridis')
    plt.title('Značajnost atributa za predikciju moždanog udara (Random Forest)', fontsize = 20)
    plt.xlabel('Značajnost')
    plt.ylabel('Atribut')
    plt.show()