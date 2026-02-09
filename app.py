import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# --- CONFIGURATION ---
try:
    st.set_page_config(page_title="Beet-Hoven", page_icon="logo.png", layout="wide")
except:
    st.set_page_config(page_title="Beet-Hoven", page_icon="🎹", layout="wide")

# --- FICHIERS ---
FILES = {
    "users": "users.csv",
    "reviews": "reviews.csv",
    "listenlist": "listenlist.csv",
    "follows": "follows.csv",
    "favorites": "favorites.csv"
}

# --- INITIALISATION BDD ---
def init_db():
    if not os.path.exists(FILES["users"]):
        pd.DataFrame(columns=["username", "password"]).to_csv(FILES["users"], index=False)
    if not os.path.exists(FILES["reviews"]):
        pd.DataFrame(columns=["username", "date", "artist", "track", "image", "rating", "review", "likes", "liked_by"]).to_csv(FILES["reviews"], index=False)
    if not os.path.exists(FILES["listenlist"]):
        pd.DataFrame(columns=["username", "artist", "track", "image", "added_date"]).to_csv(FILES["listenlist"], index=False)
    if not os.path.exists(FILES["follows"]):
        pd.DataFrame(columns=["follower", "following"]).to_csv(FILES["follows"], index=False)
    if not os.path.exists(FILES["favorites"]):
        pd.DataFrame(columns=["username", "art1_name", "art1_img", "art2_name", "art2_img", "art3_name", "art3_img"]).to_csv(FILES["favorites"], index=False)

init_db()

# --- FONCTIONS DATA ---
def load_data(key): return pd.read_csv(FILES[key])
def save_data(key, df): df.to_csv(FILES[key], index=False)

# --- FONCTIONS DEEZER (RECHERCHE AVANCÉE) ---
def search_deezer_live(query):
    """Retourne une liste de résultats (Top 10) pour une recherche"""
    if not query: return []
    try:
        url = f"https://api.deezer.com/search?q={query}"
        r = requests.get(url).json()
        return r.get('data', [])[:10] # On garde les 10 premiers
    except: return []

def search_deezer_artist(name):
    """Pour le Top 3 Artistes"""
    try:
        url = f"https://api.deezer.com/search/artist?q={name}"
        r = requests.get(url).json()
        if r.get('data'): return r['data'][0]['name'], r['data'][0]['picture_medium']
    except: pass
    return name, "https://via.placeholder.com/150?text=?"

# --- SESSION STATES ---
if 'user' not in st.session_state: st.session_state.user = None
if 'view_profile' not in st.session_state: st.session_state.view_profile = None
# Variables pour stocker les résultats de recherche temporaires
if 'search_results_review' not in st.session_state: st.session_state.search_results_review = []
if 'search_results_listen' not in st.session_state: st.session_state.search_results_listen = []

# ==========================================
# 🔐 LOGIN
# ==========================================
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", width=200)
        else: st.title("🎹")
        st.title("Beet-Hoven")
        
        t1, t2 = st.tabs(["Connexion", "Inscription"])
        with t1:
            with st.form("log"):
                u = st.text_input("Pseudo")
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Se connecter"):
                    users = load_data("users")
                    if not users[(users['username'] == u) & (users['password'] == p)].empty:
                        st.session_state.user = u
                        st.rerun()
                    else: st.error("Erreur.")
        with t2:
            with st.form("sign"):
                nu = st.text_input("Nouveau Pseudo")
                np = st.text_input("Nouveau MDP", type="password")
                if st.form_submit_button("Créer"):
                    users = load_data("users")
                    if nu not in users['username'].values and nu and np:
                        save_data("users", pd.concat([users, pd.DataFrame([[nu, np]], columns=users.columns)]))
                        st.success("C'est bon !")
                    else: st.error("Erreur.")

# ==========================================
# 🎵 APP
# ==========================================
else:
    current_user = st.session_state.user
    
    # --- SIDEBAR ---
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", width=100)
        st.title(f"👤 {current_user}")
        
        if st.button("🏠 Flux d'actu"): st.session_state.view_profile = None; st.rerun()
        if st.button("👤 Mon Profil"): st.session_state.view_profile = current_user; st.rerun()
        if st.button("✍️ Noter une musique"): st.session_state.view_profile = "LOGGING"; st.rerun()
        if st.button("🎧 ListenList"): st.session_state.view_profile = "LISTENLIST"; st.rerun()
        
        st.divider()
        su = st.text_input("🔍 Profil...")
        if su:
            users = load_data("users")
            if su in users['username'].values:
                if st.button(f"Voir {su}"): st.session_state.view_profile = su; st.rerun()
        
        st.divider()
        if st.button("Déconnexion"): st.session_state.user = None; st.rerun()

    # --- PAGES ---

    # 1. PAGE PROFIL
    if st.session_state.view_profile and st.session_state.view_profile not in ["LOGGING", "LISTENLIST"]:
        target = st.session_state.view_profile
        
        c_back, c_tit, c_act = st.columns([1, 3, 2])
        with c_back: 
            if st.button("⬅️"): st.session_state.view_profile = None; st.rerun()
        with c_tit: st.header(f"Profil de {target}")
        with c_act:
            if target != current_user:
                fl = load_data("follows")
                is_sub = not fl[(fl['follower'] == current_user) & (fl['following'] == target)].empty
                if is_sub:
                    if st.button("Se désabonner ❌"):
                        fl = fl.drop(fl[(fl['follower'] == current_user) & (fl['following'] == target)].index)
                        save_data("follows", fl)
                        st.rerun()
                else:
                    if st.button("S'abonner ✅"):
                        save_data("follows", pd.concat([fl, pd.DataFrame([[current_user, target]], columns=fl.columns)]))
                        st.rerun()

        # TOP 3
        st.subheader("🏆 Top 3 Artistes")
        favs = load_data("favorites")
        u_fav = favs[favs['username'] == target]
        
        if target == current_user:
            with st.expander("Modifier mon Top 3"):
                with st.form("f"):
                    a1 = st.text_input("Artiste 1")
                    a2 = st.text_input("Artiste 2")
                    a3 = st.text_input("Artiste 3")
                    if st.form_submit_button("Sauvegarder"):
                        n1, i1 = search_deezer_artist(a1)
                        n2, i2 = search_deezer_artist(a2)
                        n3, i3 = search_deezer_artist(a3)
                        favs = favs[favs['username'] != current_user]
                        new_fav = pd.DataFrame([[current_user, n1, i1, n2, i2, n3, i3]], columns=favs.columns)
                        save_data("favorites", pd.concat([favs, new_fav]))
                        st.rerun()

        if not u_fav.empty:
            r = u_fav.iloc[0]
            c1, c2, c3 = st.columns(3)
            with c1: 
                if pd.notna(r['art1_img']): st.image(r['art1_img'], width=120)
                st.write(f"**{r['art1_name']}**")
            with c2: 
                if pd.notna(r['art2_img']): st.image(r['art2_img'], width=120)
                st.write(f"**{r['art2_name']}**")
            with c3: 
                if pd.notna(r['art3_img']): st.image(r['art3_img'], width=120)
                st.write(f"**{r['art3_name']}**")

        st.divider()
        
        # STATS
        revs = load_data("reviews")
        urevs = revs[revs['username'] == target]
        ll = load_data("listenlist")
        ull = ll[ll['username'] == target]
        flw = load_data("follows")
        subs = len(flw[flw['following'] == target])
        
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Abonnés", subs)
        s2.metric("Notes", len(urevs))
        s3.metric("Moyenne", round(urevs['rating'].mean(), 2) if not urevs.empty else 0)
        s4.metric("ListenList", len(ull))
        
        st.subheader("🌟 Dernières notes")
        if not urevs.empty:
            for idx, row in urevs.iloc[::-1].head(5).iterrows():
                with st.container(border=True):
                    ci, ct = st.columns([1, 5])
                    with ci:
                        if pd.notna(row['image']) and str(row['image']).startswith("http"): st.image(row['image'])
                        else: st.write("💿")
                    with ct:
                        st.markdown(f"**{row['track']}** - {row['artist']}")
                        st.caption(f"Note : {row['rating']}/5")
                        st.write(f"_{row['review']}_")
        else: st.caption("Rien.")

    # 2. PAGE LISTENLIST (AVEC RECHERCHE DEEZER)
    elif st.session_state.view_profile == "LISTENLIST":
        st.header("🎧 Ma ListenList")
        
        # BARRE DE RECHERCHE
        st.subheader("➕ Ajouter une musique")
        col_search, col_btn = st.columns([4, 1])
        search_query = col_search.text_input("Chercher sur Deezer (Artiste, Titre...)", key="search_ll")
        if col_btn.button("🔎"):
            st.session_state.search_results_listen = search_deezer_live(search_query)
            
        # RESULTATS RECHERCHE
        if st.session_state.search_results_listen:
            st.write("Résultats :")
            # On crée une liste formatée pour le selectbox
            options = {f"{t['artist']['name']} - {t['title']}": t for t in st.session_state.search_results_listen}
            selected_key = st.selectbox("Choisir la musique :", options.keys(), key="sel_ll")
            
            if selected_key:
                track_data = options[selected_key]
                # Aperçu
                c1, c2 = st.columns([1, 5])
                with c1: st.image(track_data['album']['cover_medium'])
                with c2: 
                    st.write(f"**{track_data['title']}**")
                    st.write(f"Par {track_data['artist']['name']}")
                    if st.button("Ajouter à ma liste ✅"):
                        ll = load_data("listenlist")
                        new_l = pd.DataFrame([[current_user, track_data['artist']['name'], track_data['title'], track_data['album']['cover_medium'], str(datetime.now().date())]], columns=ll.columns)
                        save_data("listenlist", pd.concat([ll, new_l]))
                        st.success("Ajouté !")
                        st.session_state.search_results_listen = [] # Reset
                        st.rerun()
        
        st.divider()
        st.subheader("📋 Ma Liste")
        ll = load_data("listenlist")
        mll = ll[ll['username'] == current_user]
        if not mll.empty:
            for idx, row in mll.iterrows():
                with st.container(border=True):
                    c_img, c_txt, c_act = st.columns([1, 4, 1])
                    with c_img:
                        if pd.notna(row['image']) and str(row['image']).startswith("http"): st.image(row['image'])
                    with c_txt:
                        st.markdown(f"**{row['track']}**")
                        st.text(f"{row['artist']}")
                    with c_act:
                        if st.button("🗑️", key=f"dll_{idx}"):
                            ll = ll.drop(idx)
                            save_data("listenlist", ll)
                            st.rerun()
        else: st.info("Vide.")

    # 3. PAGE NOTER (AVEC RECHERCHE DEEZER)
    elif st.session_state.view_profile == "LOGGING":
        st.header("✍️ Noter une musique")
        
        # BARRE DE RECHERCHE
        col_s, col_b = st.columns([4, 1])
        q = col_s.text_input("Chercher la musique sur Deezer...", key="search_rev")
        if col_b.button("🔎"):
            st.session_state.search_results_review = search_deezer_live(q)
            
        # FORMULAIRE
        with st.form("review_form"):
            # Si on a des résultats, on propose une liste, sinon champs texte classiques
            selected_track = None
            if st.session_state.search_results_review:
                opts = {f"{t['artist']['name']} - {t['title']}": t for t in st.session_state.search_results_review}
                sel = st.selectbox("Sélectionner le résultat :", opts.keys())
                selected_track = opts[sel]
                
                # Affichage visuel du choix
                st.info(f"Tu notes : {selected_track['title']} de {selected_track['artist']['name']}")
                st.image(selected_track['album']['cover_medium'], width=100)
            
            # Champs de notation
            rating = st.slider("Note", 0.0, 5.0, 2.5, 0.5)
            review = st.text_area("Ton avis")
            
            if st.form_submit_button("Publier l'avis"):
                revs = load_data("reviews")
                
                if selected_track:
                    # On utilise les données Deezer
                    art = selected_track['artist']['name']
                    trk = selected_track['title']
                    img = selected_track['album']['cover_medium']
                else:
                    # Fallback manuel (si pas de recherche faite)
                    st.warning("Utilise la recherche pour avoir la pochette !")
                    st.stop()

                new_r = pd.DataFrame([[
                    current_user, str(datetime.now().date()), art, trk, img, rating, review, 0, "[]"
                ]], columns=revs.columns)
                save_data("reviews", pd.concat([revs, new_r]))
                st.success("Publié !")
                st.session_state.search_results_review = [] # Reset
                st.rerun()

    # 4. FLUX D'ACTUALITÉ
    else:
        st.title("🌍 Fil d'actualité")
        f1, f2 = st.columns([1, 2])
        mode = f1.radio("Filtre :", ["Tout le monde", "Mes abonnements"])
        
        revs = load_data("reviews")
        flw = load_data("follows")
        
        # Masquer mes posts
        feed = revs[revs['username'] != current_user]
        
        if mode == "Mes abonnements":
            subs = flw[flw['follower'] == current_user]['following'].tolist()
            feed = feed[feed['username'].isin(subs)]
        
        if not feed.empty:
            for idx, row in feed.iloc[::-1].iterrows():
                with st.container(border=True):
                    c_img, c_cnt, c_act = st.columns([1, 4, 1])
                    with c_img:
                        if pd.notna(row['image']) and str(row['image']).startswith("http"): st.image(row['image'], use_container_width=True)
                        else: st.write("💿")
                    
                    with c_cnt:
                        st.subheader(row['track'])
                        st.write(f"👤 **{row['artist']}**")
                        if st.button(f"@{row['username']}", key=f"pf_{idx}"):
                            st.session_state.view_profile = row['username']
                            st.rerun()
                        st.caption(f"{row['date']} | {row['rating']}/5")
                        st.info(f"💬 {row['review']}")
                    
                    with c_act:
                        lks = int(row['likes'])
                        try: lkrs = eval(row['liked_by']) if isinstance(row['liked_by'], str) else []
                        except: lkrs = []
                        is_lk = current_user in lkrs
                        if st.button(f"{'❤️' if is_lk else '🤍'} {lks}", key=f"lk_{idx}"):
                            if is_lk: lkrs.remove(current_user); lks -= 1
                            else: lkrs.append(current_user); lks += 1
                            revs.at[idx, 'likes'] = lks
                            revs.at[idx, 'liked_by'] = str(lkrs)
                            save_data("reviews", revs)
                            st.rerun()
        else: st.info("Aucune activité.")