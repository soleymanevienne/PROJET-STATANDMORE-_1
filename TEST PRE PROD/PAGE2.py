from flask import Flask, render_template, request
import folium
import io
import pandas as pd
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt
import base64
import seaborn as sns
import matplotlib
from datetime import datetime

matplotlib.use('Agg')  # Set the backend before importing pyplot
import matplotlib.pyplot as plt
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static', template_folder='templates')  # Maintenant, Flask cherchera les modèles dans le dossier 'templates'

# Définir la fonction sorted dans le contexte de rendu de modèle
@app.context_processor
def utility_processor():
    def custom_sorted(iterable):
        return sorted(iterable)
    return dict(sorted=custom_sorted)

# Charger les données
df_final = pd.read_csv(r"df_final.csv", low_memory=False)
df_final = df_final.dropna(subset=['latitude', 'longitude'])
df_final['latitude'] = pd.to_numeric(df_final['latitude'], errors='coerce')
df_final['longitude'] = pd.to_numeric(df_final['longitude'], errors='coerce')
df_final = df_final.dropna(subset=['latitude', 'longitude'])
df_final['type_operation'] = df_final['type_operation'].astype(str).replace('nan', 'Inconnu')
df_final['departement'] = df_final['departement'].astype(str).replace('nan', 'Inconnu')

# Convertir les colonnes de dates en datetime
df_final['date_heure_reception_alerte'] = pd.to_datetime(df_final['date_heure_reception_alerte'], errors='coerce')
df_final['date_heure_fin_operation'] = pd.to_datetime(df_final['date_heure_fin_operation'], errors='coerce')

# Route pour la page 2 (page2.html)


if __name__ == '__main__':
    app.run(debug=True)
