from flask import Flask, request, render_template, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta, datetime
import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import folium
from folium.plugins import MarkerCluster
import matplotlib.ticker as ticker
import numpy as np
import matplotlib
matplotlib.use('Agg')
import plotly.graph_objects as go
import plotly.express as px
from flask import jsonify

from app import db
from generate_plot import (generate_graph_evolution_personnes_impliquees,
                           generate_graph_evolution_deces, generate_graph_top5_evenements,
                           generate_graph_resultat_humain, generate_graph_evolution_operations,
                           generate_graph_operations_par_saison, generate_graph_operations_par_zone,
                           generate_graph_top5_operation, generate_graph_operations_by_phase_of_day,
                           generate_graph_evolution_flotteurs, generate_graph_operations_par_type_flotteur,
                           generate_graph_top5_categories_decedees_disparues, generate_graph_evolution_operations_par_type_flotteur,
                           generate_graph_operations_par_categorie_flotteur_et_phase_journee, generate_graph_operations_par_categorie_flotteur_et_departement,
                           generate_graph_operations_par_categorie_qui_alerte, generate_donut_chart_operations_par_pavillon,
                           generate_bar_chart_operations_par_zone_responsabilite, generate_bar_chart_operations_par_categorie_personne)

# Création de l'application Flask
app = Flask(__name__)

# Configuration de l'application Flask
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/yourdatabase.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'yoursecretkey')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

# Initialisation de l'extension SQLAlchemy avec l'application Flask pour la gestion de la base de données
db = SQLAlchemy(app)

# Initialisation de l'outil de migration de base de données Flask-Migrate
migrate = Migrate(app, db)

# Initialisation et configuration du gestionnaire de connexion Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Création du dossier static si il existe pas
if not os.path.exists('static'):
    os.makedirs('static')

# Classe User représentant un utilisateur dans la base de données
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    avatar = db.Column(db.String(150), nullable=True, default='avatar-1.jpg')
    role = db.Column(db.String(50), nullable=False, default='USER')

    def set_password(self, password):
        self.password = generate_password_hash(password)
    

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Fonction de rappel pour charger un utilisateur par ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Fonction exécutée avant chaque requête pour rendre la session permanente
@app.before_request
def make_session_permanent():
    session.permanent = True

# Décorateur pour vérifier si un utilisateur est administrateur
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=session['email']).first()
        if user.role != 'ADMIN':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('template'))
        
        return f(*args, **kwargs)
    return decorated_function

# Route pour gérer les utilisateurs administrateurs
@app.route('/admin/manage_users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        new_user = User(name=name, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Utilisateur ajouté !', 'success')
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

# Route pour supprimer un utilisateur
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('Utilisateur supprimé !', 'success')
        print(f"User {user.email} deleted.") 
    else:
        flash('Utilisateur pas trouvé !', 'error')
    return redirect(url_for('manage_users'))

# Fonction de rappel pour charger un utilisateur par ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route pour modifier un utilisateur
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        password = request.form['password']
        if password:
            user.set_password(password) 
        db.session.commit()
        flash('Utilisateur mis à jour !', 'success')
        return redirect(url_for('manage_users'))
    
    return render_template('edit_user.html', user=user)

# Route pour afficher la page de bienvenue
@app.route('/', methods=['GET', 'POST'])
def welcome():
    return render_template('login.html')

# Route pour gérer la connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Email ou mot de passe incorect. Ressayer.', 'danger')
            return redirect(url_for('login'))

        if user.email == 'admin@statandmore.fr':
            user.role = 'ADMIN'
            db.session.commit()

        session['email'] = user.email
        login_user(user)
        return redirect(url_for('template'))

    return render_template('login.html')

# Route pour gérer l'inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        avatar = request.form.get('avatar')
        role = request.form.get('role', 'USER')  # Default role is USER if not provided

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email déjà existant')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, avatar=avatar, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Inscription réussi. Connectez-vous !')
        return redirect(url_for('login')) 

    return render_template('register.html')


# Route pour réinitialiser le mot de passe
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(email=email).first()
        if user:
            if new_password == confirm_password:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Mot de passe réinitialisé !', 'success')
            else:
                flash('Les mots de passe ne correspondent pas.', 'error')
        else:
            flash('Aucun utilisateur trouvé avec cet e-mail.', 'error')

    return render_template('reset_password.html')

# Route pour gérer la déconnexion
@app.route('/logout')
def logout():
    session.pop('email', None)
    logout_user()
    return redirect(url_for('login'))

# Route pour gérer le profil utilisateur
@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=session['email']).first()
    if user:
        avatar_path = os.path.join('static', 'static', 'image', user.avatar)
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'update_email':
                new_email = request.form.get('email')
                user.email = new_email
            elif action == 'update_password':
                new_password = request.form.get('password')
                user.password = generate_password_hash(new_password)
            elif action == 'update_avatar':
                new_avatar = request.form.get('avatar')
                user.avatar = new_avatar
                avatar_path = os.path.join('static', 'static', 'image', new_avatar)
            db.session.commit()
            return redirect(url_for('profil'))
        return render_template('profil.html', user=user, avatar_path=avatar_path)
    return redirect(url_for('login'))

# Route pour gérer les erreurs 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

# Fonction personnalisée pour trier les éléments
def custom_sorted(iterable):
    return sorted(iterable, key=lambda x: str(x))

app.jinja_env.filters['custom_sorted'] = custom_sorted

df_final = pd.read_csv(r"df_final.csv", low_memory=False)
df_final = df_final.dropna(subset=['latitude', 'longitude'])
df_final['latitude'] = pd.to_numeric(df_final['latitude'], errors='coerce')
df_final['longitude'] = pd.to_numeric(df_final['longitude'], errors='coerce')
df_final = df_final.dropna(subset=['latitude', 'longitude'])
df_final['type_operation'] = df_final['type_operation'].astype(str).replace('nan', 'Inconnu')
df_final['departement'] = df_final['departement'].astype(str).replace('nan', 'Inconnu')
df_final['date_heure_reception_alerte'] = pd.to_datetime(df_final['date_heure_reception_alerte'], errors='coerce', utc=True)
df_final['date_heure_fin_operation'] = pd.to_datetime(df_final['date_heure_fin_operation'], errors='coerce', utc=True)

graph_cache = {}

# Fonction pour envelopper les étiquettes
def wrap_labels(labels, max_words_per_line=2):
    return ['\n'.join(textwrap.wrap(label.get_text(), max_words_per_line)) for label in labels]

# Fonction pour obtenir l'intervalle de dates
def get_date_range(page=None):
    if page:
        date_start = session.get(f'{page}_date_start', '01/01/2021')
        date_end = session.get(f'{page}_date_end', '12/31/2021')
    else:
        date_start = session.get('global_date_start', '01/01/2021')
        date_end = session.get('global_date_end', '12/31/2021')
    return date_start, date_end

# Route pour définir les dates pour le template
@app.route('/set_dates_template', methods=['POST'])
def set_dates_template():
    session['template_date_start'] = request.form.get('template_date_start', '01/01/2021')
    session['template_date_end'] = request.form.get('template_date_end', '12/31/2021')
    return redirect(url_for('template'))

# Route pour définir les dates pour la page 1
@app.route('/set_dates_page1', methods=['POST'])
def set_dates_page1():
    session['page1_date_start'] = request.form.get('page1_date_start', '01/01/2021')
    session['page1_date_end'] = request.form.get('page1_date_end', '12/31/2021')
    return redirect(url_for('page1'))

# Route pour définir les dates pour la page 2
@app.route('/set_dates_page2', methods=['POST'])
def set_dates_page2():
    session['page2_date_start'] = request.form.get('page2_date_start', '01/01/2021')
    session['page2_date_end'] = request.form.get('page2_date_end', '12/31/2021')
    return redirect(url_for('page2'))

# Route pour définir les dates pour la page 3
@app.route('/set_dates_page3', methods=['POST'])
def set_dates_page3():
    session['page3_date_start'] = request.form.get('page3_date_start', '01/01/2021')
    session['page3_date_end'] = request.form.get('page3_date_end', '12/31/2021')
    return redirect(url_for('page3'))

# Route pour définir les dates pour la page 4
@app.route('/set_dates_page4', methods=['POST'])
def set_dates_page4():
    session['page4_date_start'] = request.form.get('page4_date_start', '01/01/2021')
    session['page4_date_end'] = request.form.get('page4_date_end', '12/31/2021')
    return redirect(url_for('page4'))

# Route pour afficher la page d'accueil
@app.route('/accueil')
def accueil():
    return render_template('Accueil.html')

# Route pour afficher le template principal
@app.route('/template', methods=['GET', 'POST'])
def template():
    global df_final

    if 'email' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session.get('email')).first()
    if not user:
        flash('Utilisateur non trouvé. Reconnectez-vous.')
        return redirect(url_for('login'))

    if user.email == 'admin@statandmore.fr':
        user.role = 'ADMIN'
        db.session.commit()

    type_operation = request.form.get('type_operation', 'Tous')
    departement = request.form.get('departement', 'Tous')
    evenement = request.form.get('evenement', 'Tous')
    saison = request.form.get('saison', 'Tous')
    pavillon = request.form.get('pavillon', 'Tous')
    date_reception_alerte, date_fin_operation = get_date_range(page='template')
    zone_responsabilite = request.form.get('zone_responsabilite', 'Tous')
    autorite = request.form.get('autorite', 'Tous')
    categorie_evenement = request.form.get('categorie_evenement', 'Tous')
    cross = request.form.get('cross', 'Tous')
    operation_id = request.form.get('operation_id', None)
    nombre_personnes_tous_deces = request.form.get('nombre_personnes_tous_deces', None)
    nombre_personnes_tous_deces_ou_disparues = request.form.get('nombre_personnes_tous_deces_ou_disparues', None)
    resultat_humain = request.form.get('resultat_humain', 'Tous')
    categorie_personne = request.form.get('categorie_personne', 'Tous')

    filtered_data = df_final.copy()
    filters = {
        'type_operation': type_operation,
        'departement': departement,
        'evenement': evenement,
        'saison': saison,
        'pavillon': pavillon,
        'zone_responsabilite': zone_responsabilite,
        'autorite': autorite,
        'categorie_evenement': categorie_evenement,
        'cross': cross,
        'operation_id': int(operation_id) if operation_id else None,
        'nombre_personnes_tous_deces': int(nombre_personnes_tous_deces) if nombre_personnes_tous_deces else None,
        'nombre_personnes_tous_deces_ou_disparues': int(nombre_personnes_tous_deces_ou_disparues) if nombre_personnes_tous_deces_ou_disparues else None,
        'resultat_humain': resultat_humain,
        'categorie_personne': categorie_personne,
        'date_reception_alerte': (datetime.strptime(date_reception_alerte, '%m/%d/%Y').astimezone(), datetime.strptime(date_fin_operation, '%m/%d/%Y').astimezone()) if date_reception_alerte and date_fin_operation else None
    }

    for key, value in filters.items():
        if value and value != 'Tous':
            if key == 'date_reception_alerte':
                filtered_data = filtered_data[
                    (filtered_data['date_heure_reception_alerte'] >= value[0]) & 
                    (filtered_data['date_heure_reception_alerte'] <= value[1])
                ]
            elif key in ['operation_id', 'nombre_personnes_tous_deces', 'nombre_personnes_tous_deces_ou_disparues']:
                filtered_data = filtered_data[filtered_data[key] == value]
            else:
                filtered_data = filtered_data[filtered_data[key] == value]

    df_sample = filtered_data.dropna(subset=['latitude', 'longitude'])

    df_sample['latitude'] = df_sample['latitude'].astype(float)
    df_sample['longitude'] = df_sample['longitude'].astype(float)

    invalid_coordinates = df_sample[(df_sample['latitude'] < -90) | (df_sample['latitude'] > 90) |
                                    (df_sample['longitude'] < -180) | (df_sample['longitude'] > 180)]
    if not invalid_coordinates.empty:
        print("Invalid coordinates detected:")
        print(invalid_coordinates)

    total_operations = len(filtered_data)
    total_deces = int(filtered_data['nombre_personnes_tous_deces'].sum())
    total_deces_disparus = int(filtered_data['nombre_personnes_tous_deces_ou_disparues'].sum())
    total_evenements = filtered_data['evenement'].nunique()

    map1 = folium.Map(location=[-40, 10], zoom_start=2, min_zoom=2, max_zoom=90, tiles='OpenStreetMap', max_bounds=True,
                      min_lon=-200, max_lon=200, min_lat=-200, max_lat=200)
    marker_cluster = MarkerCluster().add_to(map1)

    for _, row in df_sample.iterrows():
        popup_content = (
            f"<b>ID de l'opération:</b> {row['operation_id']}<br>"
            f"<b>Événement:</b> {row['evenement']}<br>"
            f"<b>Type d'opération:</b> {row['type_operation']}<br>"
            f"<b>Département:</b> {row['departement']}<br>"
        )
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=popup_content,
            icon=folium.Icon(color='blue', icon='info', prefix='fa')
        ).add_to(marker_cluster)

    map_html = map1._repr_html_()
    top5_events = filtered_data['evenement'].value_counts().nlargest(5)
    other_events_sum = filtered_data['evenement'].value_counts().iloc[5:].sum()
    top5_events['Autres'] = other_events_sum

    def truncate_labels(labels, max_length=20):
        return [label if len(label) <= max_length else label[:max_length] + '...' for label in labels]

    plt.figure(figsize=(8, 6))  
    colors = sns.color_palette('viridis', len(top5_events))

    labels = truncate_labels(top5_events.index)

    wedges, texts, autotexts = plt.pie(top5_events, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, wedgeprops=dict(edgecolor='w'))

    for text in texts:
        text.set_color('white')
    for autotext in autotexts:
        autotext.set_color('white')

    plt.axis('equal')
    plt.gca().set_facecolor('#252e3f')

    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png', transparent=True)
    img_stream.seek(0)
    img_data = img_stream.getvalue()
    img_data_base64 = base64.b64encode(img_data).decode('utf-8')
    img_html = f'<img src="data:image/png;base64,{img_data_base64}" alt="Pie Chart">'
    plt.close()

    sns.set_style("whitegrid", {'axes.edgecolor': '#4e576a', 'axes.facecolor': '#252e3f', 'grid.color': '#4e576a', 'grid.linestyle': '--'})
    bar_data = filtered_data.groupby('categorie_flotteur')['operation_id'].nunique().reset_index()
    bar_data = bar_data.sort_values('operation_id', ascending=False)

    plt.figure(figsize=(10, 6))
    bar_plot = sns.barplot(x='categorie_flotteur', y='operation_id', data=bar_data, palette='viridis')
    plt.xticks(ha='right', color='white')
    plt.yticks(color='white')
    plt.title('Nombre d\'opérations par type de flotteur', color='white', fontsize=16)
    plt.xlabel('Catégorie de Flotteur', color='white', fontsize=14)
    plt.ylabel('Nombre d\'Opérations', color='white', fontsize=14)
    plt.gca().set_facecolor('#252e3f')

    for index, value in enumerate(bar_data['operation_id']):
        plt.text(index, value + 0.005 * max(bar_data['operation_id']), f'{value} opérations', ha='center', va='bottom', color='white', fontsize=10)

    bar_img_stream = io.BytesIO()
    plt.savefig(bar_img_stream, format='png', bbox_inches='tight', transparent=True)
    bar_img_stream.seek(0)
    bar_img_data = bar_img_stream.getvalue()
    bar_img_data_base64 = base64.b64encode(bar_img_data).decode('utf-8')
    bar_chart_html = f'<img src="data:image/png;base64,{bar_img_data_base64}" alt="Bar Chart" style="max-width: 100%; height: auto; background-color: #252e3f;">'
    plt.close()

    return render_template('template.html', user=user, avatar_path='static/static/image/' + user.avatar,
                           df_final=df_final, type_operation=type_operation, departement=departement,
                           evenement=evenement, saison=saison, pavillon=pavillon,
                           date_reception_alerte=date_reception_alerte, date_fin_operation=date_fin_operation,
                           zone_responsabilite=zone_responsabilite, autorite=autorite,operation_id=operation_id,
                           categorie_evenement=categorie_evenement, cross=cross,
                           nombre_personnes_tous_deces=nombre_personnes_tous_deces,
                           nombre_personnes_tous_deces_ou_disparues=nombre_personnes_tous_deces_ou_disparues,
                           resultat_humain=resultat_humain, categorie_personne=categorie_personne,
                           map_html=map_html, img_html=img_html, bar_chart=bar_chart_html,
                           total_operations=total_operations, total_deces=total_deces,
                           total_deces_ou_disparus=total_deces_disparus, total_evenements=total_evenements)

# Route pour afficher la page 1
@app.route('/page1', methods=['GET', 'POST'])
def page1():
    global df_final
    
    user = None
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user and not hasattr(user, 'avatar'):
            user.avatar = 'default-avatar.png'  

    type_operation = request.form.get('type_operation', 'Tous')
    if type_operation == 'inconnue':
        type_operation = 'Tous' 
        
    departement = request.form.get('departement', 'Tous')
    evenement = request.form.get('evenement', 'Tous')
    saison = request.form.get('saison', 'Tous')
    pavillon = request.form.get('pavillon', 'Tous')
    date_reception_alerte, date_fin_operation = get_date_range(page='page1')
    zone_responsabilite = request.form.get('zone_responsabilite', 'Tous')
    autorite = request.form.get('autorite', 'Tous')
    categorie_evenement = request.form.get('categorie_evenement', 'Tous')
    cross = request.form.get('cross', 'Tous')

    filtered_data = df_final.copy()
    filters = {
        'type_operation': type_operation,
        'departement': departement,
        'evenement': evenement,
        'saison': saison,
        'pavillon': pavillon,
        'zone_responsabilite': zone_responsabilite,
        'autorite': autorite,
        'categorie_evenement': categorie_evenement,
        'cross': cross,
        'date_reception_alerte': (datetime.strptime(date_reception_alerte, '%m/%d/%Y').astimezone(), datetime.strptime(date_fin_operation, '%m/%d/%Y').astimezone()) if date_reception_alerte and date_fin_operation else None
    }

    for key, value in filters.items():
        if value and value != 'Tous':
            if key == 'date_reception_alerte':
                filtered_data = filtered_data[
                    (filtered_data['date_heure_reception_alerte'] >= value[0]) & 
                    (filtered_data['date_heure_reception_alerte'] <= value[1])
                ]
            else:
                filtered_data = filtered_data[filtered_data[key] == value]

    numeric_columns = [
        'nombre_personnes_retrouvees', 'nombre_personnes_secourues', 'nombre_personnes_tirees_daffaire_seule',
        'nombre_personnes_tous_deces', 'nombre_personnes_tous_deces_ou_disparues', 'nombre_personnes_impliquees',
        'nombre_personnes_blessees_sans_clandestins', 'nombre_personnes_assistees_sans_clandestins',
        'nombre_personnes_decedees_sans_clandestins', 'nombre_personnes_decedees_accidentellement_sans_clandestins',
        'nombre_personnes_decedees_naturellement_sans_clandestins', 'nombre_personnes_disparues_sans_clandestins',
        'nombre_personnes_retrouvees_sans_clandestins', 'nombre_personnes_secourues_sans_clandestins',
        'nombre_personnes_tirees_daffaire_seule_sans_clandestins', 'nombre_personnes_tous_deces_sans_clandestins',
        'nombre_personnes_tous_deces_ou_disparues_sans_clandestins', 'nombre_personnes_impliquees_sans_clandestins'
    ]
    filtered_data[numeric_columns] = filtered_data[numeric_columns].fillna(0).astype(int)

    table_data = filtered_data.to_dict('records')

    types_operation = df_final['type_operation'].unique().tolist()
    departements = df_final['departement'].unique().tolist()
    evenements = df_final['evenement'].unique().tolist()
    pavillons = df_final['pavillon'].unique().tolist()

    if not filtered_data.empty:
        evolution_data = generate_graph_evolution_personnes_impliquees(filtered_data)
        evolution_deces_img = generate_graph_evolution_deces(filtered_data)
    else:
        evolution_data = None
        evolution_deces_img = None

    return render_template('page1.html', user=user, table_data=table_data, type_operation=type_operation, 
                           departement=departement, evenement=evenement, saison=saison, pavillon=pavillon,
                           date_reception_alerte=date_reception_alerte, date_fin_operation=date_fin_operation,
                           zone_responsabilite=zone_responsabilite, autorite=autorite, categorie_evenement=categorie_evenement, 
                           cross=cross, types_operation=[op for op in types_operation if op != 'inconnue'], departements=departements, 
                           evenements=evenements, pavillons=pavillons, evolution_data=evolution_data, evolution_deces_img=evolution_deces_img)

# Route pour afficher la page 2
@app.route('/page2', methods=['GET', 'POST'])
def page2():
    global df_final
    
    user = None
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user and not hasattr(user, 'avatar'):
            user.avatar = 'default-avatar.png'  
            
    date_reception_alerte, date_fin_operation = get_date_range(page='page2')
    periode = request.form.get('periode', 'mois')
    type_operation = request.form.get('type_operation', 'Tous')
    if type_operation == 'inconnue':
        type_operation = 'Tous' 
        
    departement = request.form.get('departement', 'Tous')
    evenement = request.form.get('evenement', 'Tous')
    saison = request.form.get('saison', 'Tous')
    pavillon = request.form.get('pavillon', 'Tous')

    filtered_data = df_final.copy()
    if date_reception_alerte and date_fin_operation:
        start_date = datetime.strptime(date_reception_alerte, '%m/%d/%Y').astimezone()
        end_date = datetime.strptime(date_fin_operation, '%m/%d/%Y').astimezone()
        filtered_data = filtered_data[
            (filtered_data['date_heure_reception_alerte'] >= start_date) & 
            (filtered_data['date_heure_reception_alerte'] <= end_date)
        ]

    if type_operation != 'Tous':
        filtered_data = filtered_data[filtered_data['type_operation'] == type_operation]
    
    if departement != 'Tous':
        filtered_data = filtered_data[filtered_data['departement'] == departement]
    
    if evenement != 'Tous':
        filtered_data = filtered_data[filtered_data['evenement'] == evenement]
    
    if saison != 'Tous':
        filtered_data = filtered_data[filtered_data['saison'] == saison]
    
    if pavillon != 'Tous':
        filtered_data = filtered_data[filtered_data['pavillon'] == pavillon]

    if not filtered_data.empty:
        generate_graph_evolution_operations(filtered_data, periode)
        generate_graph_operations_par_saison(filtered_data)
        generate_graph_operations_par_zone(filtered_data)
        generate_graph_top5_operation(filtered_data)
        generate_graph_operations_by_phase_of_day(filtered_data)

    types_operation = df_final['type_operation'].unique()
    departements = df_final['departement'].unique()
    evenements = df_final['evenement'].unique()
    saisons = df_final['saison'].unique()
    pavillons = df_final['pavillon'].unique()

    return render_template(
        'page2.html', user=user,
        date_reception_alerte=date_reception_alerte, 
        date_fin_operation=date_fin_operation, 
        periode=periode, 
        type_operation=type_operation, 
        departement=departement, 
        evenement=evenement, 
        saison=saison, 
        pavillon=pavillon,
        types_operation=[op for op in types_operation if op != 'inconnue'],
        departements=departements,
        evenements=evenements,
        saisons=saisons,
        pavillons=pavillons
    )

# Route pour afficher la page 3
@app.route('/page3', methods=['GET', 'POST'])
def page3():
    global df_final
    
    user = None
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user and not hasattr(user, 'avatar'):
            user.avatar = 'default-avatar.png'  

    type_operation = request.form.get('type_operation', 'Tous')
    if type_operation == 'inconnue':
        type_operation = 'Tous' 

    departement = request.form.get('departement', 'Tous')
    evenement = request.form.get('evenement', 'Tous')
    saison = request.form.get('saison', 'Tous')
    pavillon = request.form.get('pavillon', 'Tous')
    date_debut, date_fin = get_date_range(page='page3')
    type_flotteur = request.form.get('type_flotteur', 'Tous')

    filtered_data = df_final.copy()
    if date_debut and date_fin:
        start_date = datetime.strptime(date_debut, '%m/%d/%Y').astimezone()
        end_date = datetime.strptime(date_fin, '%m/%d/%Y').astimezone()
        filtered_data = filtered_data[
            (filtered_data['date_heure_reception_alerte'] >= start_date) & 
            (filtered_data['date_heure_reception_alerte'] <= end_date)
        ]

    if type_operation != 'Tous':
        filtered_data = filtered_data[filtered_data['type_operation'] == type_operation]
    
    if departement != 'Tous':
        filtered_data = filtered_data[filtered_data['departement'] == departement]
    
    if evenement != 'Tous':
        filtered_data = filtered_data[filtered_data['evenement'] == evenement]
    
    if saison != 'Tous':
        filtered_data = filtered_data[filtered_data['saison'] == saison]
    
    if pavillon != 'Tous':
        filtered_data = filtered_data[filtered_data['pavillon'] == pavillon]
    
    if type_flotteur != 'Tous':
        filtered_data = filtered_data[filtered_data['type_flotteur'] == type_flotteur]

    filtered_data = filtered_data.dropna(subset=['latitude', 'longitude'])

    numeric_columns = ['nombre_flotteurs_commerce_impliques', 'nombre_flotteurs_peche_impliques', 'nombre_flotteurs_plaisance_impliques', 
                       'nombre_flotteurs_loisirs_nautiques_impliques', 'nombre_aeronefs_impliques', 'nombre_flotteurs_autre_impliques', 
                       'nombre_flotteurs_annexe_impliques', 'nombre_flotteurs_autre_loisir_nautique_impliques', 'nombre_flotteurs_canoe_kayak_aviron_impliques', 
                       'nombre_flotteurs_engin_de_plage_impliques', 'nombre_flotteurs_kitesurf_impliques', 'nombre_flotteurs_plaisance_voile_legere_impliques', 
                       'nombre_flotteurs_plaisance_a_moteur_impliques', 'nombre_flotteurs_plaisance_a_moteur_moins_8m_impliques', 
                       'nombre_flotteurs_plaisance_a_moteur_plus_8m_impliques', 'nombre_flotteurs_plaisance_a_voile_impliques', 'nombre_flotteurs_planche_a_voile_impliques', 
                       'nombre_flotteurs_ski_nautique_impliques', 'nombre_flotteurs_surf_impliques', 'nombre_flotteurs_vehicule_nautique_a_moteur_impliques', 
                       'sans_flotteur_implique', 'nombre_personnes_tous_deces', 'nombre_personnes_tous_deces_ou_disparues']

    for column in numeric_columns:
        if column in filtered_data.columns:
            filtered_data[column] = pd.to_numeric(filtered_data[column], errors='coerce')

    total_flotteurs_impliques = int(filtered_data[numeric_columns[:-2]].sum().sum())
    flotteurs_plaisance_impliques = int(filtered_data['nombre_flotteurs_plaisance_impliques'].sum()) if 'nombre_flotteurs_plaisance_impliques' in filtered_data.columns else 0
    flotteurs_commerce_impliques = int(filtered_data['nombre_flotteurs_commerce_impliques'].sum()) if 'nombre_flotteurs_commerce_impliques' in filtered_data.columns else 0
    flotteurs_loisir_nautique_impliques = int(filtered_data['nombre_flotteurs_loisirs_nautiques_impliques'].sum()) if 'nombre_flotteurs_loisirs_nautiques_impliques' in filtered_data.columns else 0

    if not filtered_data.empty:
        generate_graph_evolution_flotteurs(filtered_data)
        generate_graph_operations_par_type_flotteur(filtered_data)
        generate_graph_evolution_operations_par_type_flotteur(filtered_data)
        generate_graph_top5_categories_decedees_disparues(filtered_data)
        generate_graph_operations_par_categorie_flotteur_et_departement(filtered_data)
        generate_graph_operations_par_categorie_flotteur_et_phase_journee(filtered_data)

    return render_template('page3.html',user=user,
                           type_operation=type_operation,
                           departement=departement,
                           evenement=evenement,
                           saison=saison,
                           pavillon=pavillon,
                           date_debut=date_debut,
                           date_fin=date_fin,
                           type_flotteur=type_flotteur,
                           total_flotteurs_impliques=total_flotteurs_impliques,
                           flotteurs_plaisance_impliques=flotteurs_plaisance_impliques,
                           flotteurs_commerce_impliques=flotteurs_commerce_impliques,
                           flotteurs_loisir_nautique_impliques=flotteurs_loisir_nautique_impliques,
                           unique_type_operations=sorted(op for op in df_final['type_operation'].dropna().unique() if op != 'inconnue'),
                           unique_departements=sorted(df_final['departement'].dropna().unique()),
                           unique_evenements=sorted(df_final['evenement'].dropna().unique()),
                           unique_saisons=sorted(df_final['saison'].dropna().unique()),
                           unique_pavillons=sorted(df_final['pavillon'].dropna().unique()),
                           unique_types_flotteur=sorted(df_final['type_flotteur'].dropna().unique()))

# Route pour afficher la page 4
@app.route('/page4', methods=['GET', 'POST'])
def page4():
    global df_final
    
    user = None
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if user and not hasattr(user, 'avatar'):
            user.avatar = 'default-avatar.png'  

    categorie_personne = request.form.get('categorie_personne', 'Tous')
    categorie_qui_alerte = request.form.get('categorie_qui_alerte', 'Tous')
    categorie_evenement = request.form.get('categorie_evenement', 'Tous')
    autorite = request.form.get('autorite', 'Tous')
    zone_responsabilite = request.form.get('zone_responsabilite', 'Tous')
    pavillon = request.form.get('pavillon', 'Tous')
    categorie_flotteur = request.form.get('categorie_flotteur', 'Tous')
    numero_immatriculation = request.form.get('numero_immatriculation', '')
    est_jour_ferie = request.form.get('est_jour_ferie', 'Tous')
    est_vacances_scolaires = request.form.get('est_vacances_scolaires', 'Tous')
    phase_journee = request.form.get('phase_journee', 'Tous')
    concerne_plongee = request.form.get('concerne_plongee', 'Tous')
    avec_clandestins = request.form.get('avec_clandestins', 'Tous')
    date_debut = request.form.get('page4_date_start', session.get('page4_date_start', '01/01/2021'))
    date_fin = request.form.get('page4_date_end', session.get('page4_date_end', '12/31/2021'))

    session['page4_date_start'] = date_debut
    session['page4_date_end'] = date_fin

    filtered_data = df_final.copy()

    filters = {
        'categorie_personne': categorie_personne,
        'categorie_qui_alerte': categorie_qui_alerte,
        'categorie_evenement': categorie_evenement,
        'autorite': autorite,
        'zone_responsabilite': zone_responsabilite,
        'pavillon': pavillon,
        'categorie_flotteur': categorie_flotteur,
        'est_jour_ferie': est_jour_ferie,
        'est_vacances_scolaires': est_vacances_scolaires,
        'phase_journee': phase_journee,
        'concerne_plongee': concerne_plongee,
        'avec_clandestins': avec_clandestins
    }

    for key, value in filters.items():
        if value and value != 'Tous':
            if key in ['est_jour_ferie', 'est_vacances_scolaires', 'concerne_plongee', 'avec_clandestins']:
                filtered_data = filtered_data[filtered_data[key] == (value == 'True')]
            else:
                filtered_data = filtered_data[filtered_data[key] == value]

    if numero_immatriculation:
        filtered_data = filtered_data[filtered_data['numero_immatriculation'].str.contains(numero_immatriculation, na=False)]

    if date_debut and date_fin:
        date_debut = datetime.strptime(date_debut, '%m/%d/%Y').astimezone()
        date_fin = datetime.strptime(date_fin, '%m/%d/%Y').astimezone()
        filtered_data = filtered_data[
            (filtered_data['date_heure_reception_alerte'] >= date_debut) & 
            (filtered_data['date_heure_fin_operation'] <= date_fin)
        ]

    generate_graph_operations_par_categorie_qui_alerte(filtered_data)
    generate_donut_chart_operations_par_pavillon(filtered_data)
    generate_bar_chart_operations_par_zone_responsabilite(filtered_data)
    generate_bar_chart_operations_par_categorie_personne(filtered_data)

    return render_template('page4.html', user=user,
                           categorie_personne=categorie_personne,
                           categorie_qui_alerte=categorie_qui_alerte,
                           categorie_evenement=categorie_evenement,
                           autorite=autorite,
                           zone_responsabilite=zone_responsabilite,
                           pavillon=pavillon,
                           categorie_flotteur=categorie_flotteur,
                           numero_immatriculation=numero_immatriculation,
                           est_jour_ferie=est_jour_ferie,
                           est_vacances_scolaires=est_vacances_scolaires,
                           phase_journee=phase_journee,
                           concerne_plongee=concerne_plongee,
                           avec_clandestins=avec_clandestins,
                           date_debut=date_debut.strftime('%m/%d/%Y'),
                           date_fin=date_fin.strftime('%m/%d/%Y'),
                           unique_categories_personne=sorted(df_final['categorie_personne'].dropna().unique()),
                           unique_categories_qui_alerte=sorted(df_final['categorie_qui_alerte'].dropna().unique()),
                           unique_categories_evenement=sorted(df_final['categorie_evenement'].dropna().unique()),
                           unique_autorites=sorted(df_final['autorite'].dropna().unique()),
                           unique_zones_responsabilite=sorted(df_final['zone_responsabilite'].dropna().unique()),
                           unique_pavillons=sorted(df_final['pavillon'].dropna().unique()),
                           unique_categories_flotteur=sorted(df_final['categorie_flotteur'].dropna().unique()),
                           unique_phases_journee=sorted(df_final['phase_journee'].dropna().unique()))

if __name__ == '__main__':
    app.run(debug=True)
