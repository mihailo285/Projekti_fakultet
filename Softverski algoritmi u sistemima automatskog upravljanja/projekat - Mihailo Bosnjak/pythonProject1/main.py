# unapred se izvinjavam ukoliko odredjeni delovi koda budu nepregledni :)

import pandas as pd 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import warnings

from sklearn.feature_selection import SelectFromModel
#import imblearn.under_sampling as RandomUnderSampler #iz nekog razloga ne radi
from sklearn.svm import SVC
from collections import Counter
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier, AdaBoostClassifier, StackingClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_auc_score, roc_curve
from sklearn.neighbors import KNeighborsClassifier

# resavanje warninga
warnings.filterwarnings("ignore")

#  *** 1. TACKA ***

df = pd.read_csv("diabetes_prediction_dataset.csv")
#print(df.head(10))
#df.info() # provera tipova podataka
df.isnull().sum() # nema nedostajucih podataka
df = df.drop_duplicates()
df.duplicated().sum() # uklonjeni su duplikati

'''for i in df.select_dtypes(include= "object").columns:
    print(df[i].value_counts())
    print("***"*10)''' # provera da li ima smeca medju podacima

'''df.hist(bins = 50, figsize = (20, 15))
plt.show()''' # provera putem histograma postojanja anomalija

# provera i uklanjanje anomalija
z_scores = stats.zscore(df.select_dtypes(include= ['float64', 'int64']))
abs_z_scores = np.abs(z_scores)
outliers = (abs_z_scores > 3).any(axis = 1)
print("Broj odstupanja: ", outliers.sum())
print("Velicina podataka pre uklanjanja anomalija: ", df.shape)

clean_df = df[~outliers]
print("Velicina skupa podataka nakon uklanjanja anomalija: ", clean_df.shape)

df.describe(include = "object")


irelevantna_kolona = ['hypertension']
df = df.drop(columns = irelevantna_kolona) # kolona sa atributima koji mi ne uticu na dijabetes

# *** 2. TACKA ***

# Koristio sam pivot_table da prekrstim podatke
gender_diabetes_pivot = df.pivot_table(index='gender', columns='diabetes', aggfunc='size', fill_value=0)
gender_diabetes_pivot.plot(kind = 'bar')
plt.title('Dijabetes prema polu')
plt.xlabel('Pol')
plt.ylabel('Broj osoba')
plt.legend(title='Dijabetes', labels=['Nedijabeticar', 'Dijabeticar'])
plt.xticks(rotation=0)
#print(gender_diabetes_pivot)

smoking_diabetes_pivot = df.pivot_table(index='smoking_history', columns='diabetes', aggfunc='size', fill_value=0)
smoking_diabetes_pivot.plot(kind = 'bar')
plt.title('Dijabetes prema pusackom statusu')
plt.xlabel('Pusacki status')
plt.ylabel('Broj osoba')
plt.legend(title='Dijabetes', labels=['Nedijabeticar', 'Dijabeticar'])
plt.xticks(rotation=0)
#print(gender_diabetes_pivot)
#plt.show()

# pronalazenje korelacije putem scattera
df.select_dtypes(include = 'number').columns
for i in ['age', 'heart_disease', 'bmi', 'HbA1c_level',
       'blood_glucose_level']:
    sns.scatterplot(data = df, x = i, y = 'diabetes')
    #plt.show()

# pronalazenje korelacije putem hitmapa
izuzete_kolone = ['gender', 'smoking_history']
izuzete = df.drop(columns = izuzete_kolone)
s = izuzete.select_dtypes(include = 'number').corr()
sns.heatmap(s, annot = True)
corelation_with_target = s['diabetes'].abs().sort_values(ascending = False)
#print(corelation_with_target)
#plt.show()

# pronalazenje korelacije putem pairplota
sns.pairplot(pd.DataFrame(df))
#plt.show()

# pronalazenje korelacije putem pie charta

category_counts = df['diabetes'].value_counts()
plt.figure(figsize=(8, 8))
plt.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=140)
plt.title('Proporcije kategorija')
#plt.show()

# *** 3. TACKA ***

# diabetes - ciljni atribut
X = df.drop(columns=['diabetes'])
y = df['diabetes']


# rucna implementacija random undersamplinga
def random_undersampling(X, y):
    # pronalazenje broja primera u manjinskoj klasi
    minority_class = y.value_counts().idxmin()
    majority_class = y.value_counts().idxmax()

    n_minority = y.value_counts().min()

    # indeksi manjinske klase
    minority_indices = y[y == minority_class].index
    # indeksi vecinske klase
    majority_indices = y[y == majority_class].index

    # nasumicni odabir primera iz vecinske klase
    random_majority_indices = np.random.choice(majority_indices, n_minority, replace=False)

    # kombinacija novog skupa podataka
    undersampled_indices = np.concatenate([minority_indices, random_majority_indices])
    X_undersampled = X.loc[undersampled_indices]
    y_undersampled = y.loc[undersampled_indices]

    return X_undersampled, y_undersampled


# random undersampling na podatke
X_under, y_under = random_undersampling(X, y)

# nakon balansiranja
print(f"Nakon random undersampling-а: {Counter(y_under)}")

# sacuvao sam novi skup podataka u csv
undersampled_dataset = pd.concat([X_under, y_under], axis=1)
undersampled_dataset.to_csv("undersampled_dataset.csv", index=False)

# *** 4. TACKA, 5. TACKA, 7. TACKA ***
df = pd.DataFrame(df)
df = pd.get_dummies(data = df, columns = ['gender', 'smoking_history'], drop_first = True)
X = df.drop('diabetes', axis = 1)
y = df['diabetes']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 1. Stacking
estimators = [
    ('rf', RandomForestClassifier(n_estimators=10, random_state=42, max_depth=3)),
    ('gb', GradientBoostingClassifier(n_estimators=10, random_state=42, max_depth=3))

]
stacking_model = StackingClassifier(estimators=estimators, final_estimator=RandomForestClassifier(n_estimators= 10, random_state=42))
param_grid_stacking = {
    'final_estimator__n_estimators': [5, 10],
    'final_estimator__max_depth': [2, 3]
}
print("Pokretanje Grid Search za Stacking model...")
grid_search_stacking = GridSearchCV(estimator=stacking_model, param_grid=param_grid_stacking, cv=5, n_jobs=-1)
print("Izvrsava se unakrsna validacija za Stacking model tokom Grid Search...")
grid_search_stacking.fit(X_train, y_train)
best_stacking_model = grid_search_stacking.best_estimator_

stacking_pred = best_stacking_model.predict(X_test)
stacking_accuracy = accuracy_score(y_test, stacking_pred)
print("Best Stacking Model Parameters:", grid_search_stacking.best_params_)
print("Stacking preciznost:", stacking_accuracy)
print("Stacking Confusion Matrix:\n", confusion_matrix(y_test, stacking_pred))
print("Stacking Classification Report:\n", classification_report(y_test, stacking_pred))

# 2. Boosting
boosting_model = GradientBoostingClassifier(random_state=42)

# hiperparametri
param_grid_boosting = {
    'n_estimators': [30, 50],
    'learning_rate': [0.1, 0.2],
    'max_depth': [3, 4]
}
print("Pokretanje Grid Search za Boosting model...")
grid_search_boosting = GridSearchCV(estimator=boosting_model, param_grid=param_grid_boosting, cv=5, n_jobs=-1)
print("Izvrsava se unakrsna validacija za Boosting model tokom Grid Search...")
grid_search_boosting.fit(X_train, y_train)
best_boosting_model = grid_search_boosting.best_estimator_

boosting_pred = best_boosting_model.predict(X_test)
boosting_accuracy = accuracy_score(y_test, boosting_pred)
print("Best Boosting Model Parameters:", grid_search_boosting.best_params_)
print("Boosting preciznost:", boosting_accuracy)
print("Boosting Confusion Matrix:\n", confusion_matrix(y_test, boosting_pred))
print("Boosting Classification Report:\n", classification_report(y_test, boosting_pred))

# 3. Bagging
bagging_model = RandomForestClassifier(random_state=42)

# hiperparametri
param_grid_bagging = {
    'n_estimators': [30, 50],
    'max_depth': [3, 5]
}

print("Pokretanje Grid Search za Bagging model...")
grid_search_bagging = GridSearchCV(estimator=bagging_model, param_grid=param_grid_bagging, cv=5, n_jobs=-1)
print("Izvrsava se unakrsna validacija za Bagging model tokom Grid Search...")
grid_search_bagging.fit(X_train, y_train)
best_bagging_model = grid_search_bagging.best_estimator_

bagging_pred = best_bagging_model.predict(X_test)
bagging_accuracy = accuracy_score(y_test, bagging_pred)
print("Best Bagging Model Parameters:", grid_search_bagging.best_params_)
print("Bagging preciznost:", bagging_accuracy)
print("Bagging Confusion Matrix:\n", confusion_matrix(y_test, bagging_pred))
print("Bagging Classification Report:\n", classification_report(y_test, bagging_pred))

# ovaj ispod deo je pokusaj rada sa SVC modelom, koji mi je iz nekog razloga izbacivao error, vise puta sam pokusao
# da resim error, ali nisam nazalost uspeo :(
'''bagging_model = BaggingClassifier(estimator=SVC(random_state=42))

# hiperparametri
param_grid_bagging = {
    'n_estimators': [10, 50, 100],
    'base_estimator__C': [0.1, 1, 10],  # Regularization parameter for SVC
    'base_estimator__kernel': ['linear', 'rbf']  # Kernel type for SVC
}

grid_search_bagging = GridSearchCV(estimator=bagging_model, param_grid=param_grid_bagging, cv=5, n_jobs=-1)
grid_search_bagging.fit(X_train, y_train)
best_bagging_model = grid_search_bagging.best_estimator_

bagging_pred = best_bagging_model.predict(X_test)
bagging_accuracy = accuracy_score(y_test, bagging_pred)
print("Best Bagging Model Parameters:", grid_search_bagging.best_params_)
print("Bagging preciznost:", bagging_accuracy)
print("Bagging Confusion Matrix:\n", confusion_matrix(y_test, bagging_pred))
print("Bagging Classification Report:\n", classification_report(y_test, bagging_pred))'''
# *** 6. TACKA ***

# Unakrsna validacija za kreirane modele
print("Pokretanje unakrsne validacije za odabrane modele...")
models = {
    "Stacking": best_stacking_model,
    "Boosting": best_boosting_model,
    "Bagging": best_bagging_model
}

for model_name, model in models.items():
    print(f"Pokretanje unakrsne validacije za {model_name} model...")
    cv_scores = cross_val_score(model, X, y, cv=5, n_jobs=-1)
    print(f"{model_name} CV preciznost: {np.mean(cv_scores)} ± {np.std(cv_scores)}")

# *** 8. TACKA ***

plt.figure(figsize=(10, 8))

for model_name, model in models.items():
    if hasattr(model, "predict_proba"):
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    else:
        continue

    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    plt.plot(fpr, tpr, label=f'{model_name} (AUC = {roc_auc:.2f})')

plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend(loc='lower right')

# *** 9. TACKA ***


selector = SelectFromModel(RandomForestClassifier(n_estimators=100, random_state=42))
selector.fit(X_train, y_train)

# Prikazivanje odabranih atributa
selected_features = X_train.columns[(selector.get_support())]
print("Selected Features:", selected_features)

X_train_selected = selector.transform(X_train)
X_test_selected = selector.transform(X_test)

# Treniranje modela sa odabranim atributima
models_with_selected_features = {}

for model_name, model in models.items():
    model.fit(X_train_selected, y_train)
    models_with_selected_features[model_name] = model

# Evaluacija modela sa odabranim atributima
for model_name, model in models_with_selected_features.items():
    y_pred = model.predict(X_test_selected)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"{model_name} Accuracy with Selected Features: {accuracy}")
    print(f"{model_name} Confusion Matrix with Selected Features:\n", confusion_matrix(y_test, y_pred))
    print(f"{model_name} Classification Report with Selected Features:\n", classification_report(y_test, y_pred))

# Unakrsna validacija sa odabranim atributima
for model_name, model in models_with_selected_features.items():
    print(f"Pokretanje unakrsne validacije za {model_name} model sa odabranim atributima...")
    cv_scores = cross_val_score(model, X_train_selected, y_train, cv=5, n_jobs=-1)
    print(f"{model_name} CV Accuracy with Selected Features: {np.mean(cv_scores)} ± {np.std(cv_scores)}")

# ROC krive za modele sa odabranim atributima
plt.figure(figsize=(10, 8))

for model_name, model in models_with_selected_features.items():
    if hasattr(model, "predict_proba"):
        y_pred_proba = model.predict_proba(X_test_selected)[:, 1]
    else:
        continue

    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    plt.plot(fpr, tpr, label=f'{model_name} (AUC with Selected Features = {roc_auc:.2f})')

plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve with Selected Features')
plt.legend(loc='lower right')
plt.show()




















