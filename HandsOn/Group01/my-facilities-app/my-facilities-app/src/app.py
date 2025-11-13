import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from queries import (
    get_facilities_by_type,
    get_neighbourhoods,
    get_facilities_in_neighbourhood,
    get_nearby_transport,
    FACILITY_CLASS_MAP,
)

st.set_page_config(page_title="Smart City Facilities", layout="wide")
st.title("Smart City Facilities Explorer")

# --- Sidebar ---
mode = st.sidebar.radio("Modo de exploración", ["Por tipo de facility", "Por barrio"])

if mode == "Por tipo de facility":
    readable = list(FACILITY_CLASS_MAP.keys())
    choice = st.sidebar.selectbox("Tipo de facility", readable, index=0)
    st.subheader(f"Instalaciones – {choice}")

    data = get_facilities_by_type(choice)
    df = pd.DataFrame(data)
    st.caption(f"{len(df)} resultados")
    if not df.empty:
        # Tabla compacta
        st.dataframe(df[["name","class","neighbourhood","district","municipality","telephone","email","uri"]],
                     use_container_width=True, hide_index=True)

        # --- Mapa ---
        map_df = df.dropna(subset=["lat","long"]).copy()
        if not map_df.empty:
            m = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="cartodbpositron")
            for _, row in map_df.iterrows():
                html = f"""
                <b>{row['name']}</b><br/>
                <i>{row['class']}</i><br/>
                Barrio: {row.get('neighbourhood','-')}<br/>
                Distrito: {row.get('district','-')}<br/>
                Municipio: {row.get('municipality','-')}<br/>
                Tel: {row.get('telephone','-')}<br/>
                Email: {row.get('email','-')}<br/>
                <small>{row['uri']}</small>
                """
                folium.Marker(
                    [row["lat"], row["long"]],
                    popup=folium.Popup(html, max_width=300),
                    tooltip=row["name"],
                    icon=folium.Icon(color="blue", icon="info-sign"),
                ).add_to(m)
            st_map = st_folium(m, height=520, width=None)

        # --- Detalle de una facility ---
        st.divider()
        st.subheader("Detalle y transporte cercano")
        pick = st.selectbox("Selecciona una facility", df["name"].tolist())
        if pick:
            sel = df[df["name"] == pick].iloc[0]
            st.markdown(f"**URI:** {sel['uri']}")
            st.markdown(f"**Tipo:** {sel['class']}")
            st.markdown(f"**Barrio/Distrito/Municipio:** {sel.get('neighbourhood','-')} / {sel.get('district','-')} / {sel.get('municipality','-')}")
            st.markdown(f"**Tel:** {sel.get('telephone','-')}  |  **Email:** {sel.get('email','-')}")
            tr = get_nearby_transport(sel["uri"])
            cols = st.columns(3)
            cols[0].markdown("**Metro:**<br>" + ("<br>".join(tr["Subway"]) or "—"), unsafe_allow_html=True)
            cols[1].markdown("**Bus:**<br>" + ("<br>".join(tr["Bus"]) or "—"), unsafe_allow_html=True)
            cols[2].markdown("**Cercanías:**<br>" + ("<br>".join(tr["SuburbanTrain"]) or "—"), unsafe_allow_html=True)

else:
    st.subheader("Explorar por barrio")
    nh_list = get_neighbourhoods()
    if not nh_list:
        st.info("No se han encontrado barrios en el grafo.")
    else:
        labels = [n for _, n in nh_list]
        choice = st.sidebar.selectbox("Barrio", labels, index=0)
        # nh_uri = dict(nh_list)[choice] if choice in dict((n,l) for n,l in nh_list).values() else None
        # el dict anterior es incómodo; más claro:
        nh_uri = None
        for uri, name in nh_list:
            if name == choice:
                nh_uri = uri
                break

        if nh_uri:
            st.caption(f"Barrio: {choice}")
            facilities = get_facilities_in_neighbourhood(nh_uri)
            df = pd.DataFrame(facilities)
            st.caption(f"{len(df)} facilities dentro del barrio")
            if not df.empty:
                st.dataframe(df[["name","class","district","municipality","telephone","email","uri"]],
                             use_container_width=True, hide_index=True)

                map_df = df.dropna(subset=["lat","long"]).copy()
                if not map_df.empty:
                    m = folium.Map(location=[40.4168, -3.7038], zoom_start=12, tiles="cartodbpositron")
                    for _, row in map_df.iterrows():
                        html = f"""
                        <b>{row['name']}</b><br/>
                        <i>{row.get('class','Facility')}</i><br/>
                        Distrito: {row.get('district','-')}<br/>
                        Municipio: {row.get('municipality','-')}<br/>
                        Tel: {row.get('telephone','-')}<br/>
                        Email: {row.get('email','-')}<br/>
                        <small>{row['uri']}</small>
                        """
                        folium.Marker(
                            [row["lat"], row["long"]],
                            popup=folium.Popup(html, max_width=300),
                            tooltip=row["name"],
                            icon=folium.Icon(color="green", icon="ok-sign"),
                        ).add_to(m)
                    st_folium(m, height=520, width=None)

            # Detalle + transporte
            st.divider()
            if not df.empty:
                pick = st.selectbox("Selecciona una facility del barrio", df["name"].tolist())
                if pick:
                    sel = df[df["name"] == pick].iloc[0]
                    st.markdown(f"**URI:** {sel['uri']}")
                    st.markdown(f"**Tipo:** {sel.get('class','Facility')}")
                    st.markdown(f"**Distrito/Municipio:** {sel.get('district','-')} / {sel.get('municipality','-')}")
                    st.markdown(f"**Tel:** {sel.get('telephone','-')}  |  **Email:** {sel.get('email','-')}")
                    tr = get_nearby_transport(sel["uri"])
                    cols = st.columns(3)
                    cols[0].markdown("**Metro:**<br>" + ("<br>".join(tr["Subway"]) or "—"), unsafe_allow_html=True)
                    cols[1].markdown("**Bus:**<br>" + ("<br>".join(tr["Bus"]) or "—"), unsafe_allow_html=True)
                    cols[2].markdown("**Cercanías:**<br>" + ("<br>".join(tr["SuburbanTrain"]) or "—"), unsafe_allow_html=True)