import pandas as pd

# Chemins des fichiers CSV
flotteurs_file = r"C:\Users\svienne\OneDrive - BLANCHON\Bureau\DATA_STATANDMORE/flotteurs.csv"
operations_file = r"C:\Users\svienne\OneDrive - BLANCHON\Bureau\DATA_STATANDMORE/operations.csv"
operations_stats_file = r"C:\Users\svienne\OneDrive - BLANCHON\Bureau\DATA_STATANDMORE/operations_stats.csv"
resultats_humain_file = r"C:\Users\svienne\OneDrive - BLANCHON\Bureau\DATA_STATANDMORE/resultats_humain.csv"

# Charger les données CSV dans des DataFrames pandas
df_flotteurs = pd.read_csv(flotteurs_file)
df_operations = pd.read_csv(operations_file)
df_operations_stats = pd.read_csv(operations_stats_file)
df_resultats_humain = pd.read_csv(resultats_humain_file)

# Jointure entre 'operations' et 'flotteurs'
df_joined = pd.merge(df_operations, df_flotteurs, on='operation_id', how='left')

# Jointure entre le résultat précédent et 'operations_stats'
df_joined = pd.merge(df_joined, df_operations_stats, on='operation_id', how='left')

# Jointure entre le résultat précédent et 'resultats_humain'
df_final = pd.merge(df_joined, df_resultats_humain, on='operation_id', how='left')

# Convertissez la colonne 'date_heure_reception_alerte' en datetime
df_final['date_heure_reception_alerte'] = pd.to_datetime(df_final['date_heure_reception_alerte'])

# Définissez la fonction qui détermine la saison
def determine_saison(date):
    if 5 <= date.month <= 9:
        return 'Haute saison'
    else:
        return 'Basse saison'

# Appliquez cette fonction pour créer la nouvelle colonne 'saison'
df_final['saison'] = df_final['date_heure_reception_alerte'].apply(determine_saison)

# Sauvegarde du DataFrame final dans un fichier CSV
output_file_path = r"C:\Users\svienne\Downloads\Porjet STATANDMORE\df_final.csv"
df_final.to_csv(output_file_path, index=False)
