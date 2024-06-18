from flask import Flask, render_template, request
import pandas as pd
import folium
from folium.plugins import MarkerCluster

app = Flask(__name__)

# Charger les données
df_final = pd.read_csv(r"df_final.csv", low_memory=False)
df_final = df_final.dropna(subset=['latitude', 'longitude'])
df_final['latitude'] = pd.to_numeric(df_final['latitude'], errors='coerce')
df_final['longitude'] = pd.to_numeric(df_final['longitude'], errors='coerce')
df_final = df_final.dropna(subset=['latitude', 'longitude'])
df_final['type_operation'] = df_final['type_operation'].astype(str).replace('nan', 'Inconnu')
df_final['departement'] = df_final['departement'].astype(str).replace('nan', 'Inconnu')

@app.route('/', methods=['GET', 'POST'])
def index():
    # Filtres initiaux ou mis à jour
    type_operation = request.form.get('type_operation', 'Tous')
    departement = request.form.get('departement', 'Tous')

    filtered_data = df_final.copy()
    if type_operation != 'Tous':
        filtered_data = filtered_data[filtered_data['type_operation'] == type_operation]
    if departement != 'Tous':
        filtered_data = filtered_data[filtered_data['departement'] == departement]

    # Prendre un échantillon après filtrage
    df_sample = filtered_data.sample(n=1000, random_state=42) if len(filtered_data) > 1000 else filtered_data

    # Création de la carte
    map1 = folium.Map(location=[10, 20], zoom_start=2, tiles='OpenStreetMap')
    marker_cluster = MarkerCluster().add_to(map1)

    for _, row in df_sample.iterrows():
        popup_content = (
            f"<b>Événement:</b> {row['evenement']}<br>"
            f"<b>Type d'opération:</b> {row['type_operation']}<br>"
            f"<b>Département:</b> {row['departement']}<br>"
            f"<b>Catégorie d'événement:</b> {row['categorie_evenement']}<br>"
            f"<b>Date et heure de réception d'alerte (UTC):</b> {row['date_heure_reception_alerte']}<br>"
            f"<b>Zone de responsabilité:</b> {row['zone_responsabilite']}<br>"
            f"<b>CROSS Sitrep:</b> {row['cross_sitrep']}<br>"
            f"<b>Type de flotteurs impliqués:</b> {row['type_flotteur']}<br>"
            f"<b>Nombre de personnes décédées ou disparues:</b> {row['nombre_personnes_decedees']}<br>"
            f"<b>Distance des côtes (mètres):</b> {row['distance_cote_metres']}<br>"
        )
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup_content,
            icon=folium.Icon(color='blue', icon='info', prefix='fa')
        ).add_to(marker_cluster)

    map_html = map1._repr_html_()

    # Rendre le template avec les données
    return render_template('template.html', df_final=df_final, type_operation=type_operation, departement=departement, map_html=map_html)

if __name__ == '__main__':
    app.run(debug=True)
