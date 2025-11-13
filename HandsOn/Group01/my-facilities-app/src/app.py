import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from queries import (
    get_facilities_by_type,
    get_neighbourhoods,
    get_facilities_in_neighbourhood,
    get_districts,
    get_neighbourhoods_in_district,
    get_nearby_transport,
    FACILITY_CLASS_MAP,
    FACILITY_MAIN_TYPES,
    FACILITY_SUBTYPES_BY_MAIN,
    ALL_FACILITY_TYPES,
)

st.set_page_config(page_title="Smart City Facilities", layout="wide")
st.title("Smart City Facilities Explorer")

# --- Sidebar ---
mode = st.sidebar.radio("Modo de exploración", ["Por tipo de facility", "Por localizacion"])

if mode == "Por tipo de facility":
    # --- Primer selector: clase principal (opcional) ---
    main_choice = st.sidebar.selectbox(
        "Tipo principal de facility (opcional)",
        ["Ninguno"] + FACILITY_MAIN_TYPES,
        index=0,
    )

    # --- Segundo selector: tipo concreto ---
    if main_choice == "Ninguno":
        # No se filtra por clase principal: mostramos todas las clases posibles
        type_options = ALL_FACILITY_TYPES
    else:
        # Mostramos solo las subclases (y/o el tipo genérico) de esa clase principal
        type_options = FACILITY_SUBTYPES_BY_MAIN.get(main_choice, [])

    if not type_options:
        st.warning("No hay subtipos configurados para este tipo de facility.")
        st.stop()

    choice = st.sidebar.selectbox("Subtipo concreto de facility", type_options, index=0)

    st.subheader(f"Instalaciones – {choice}")

    # La consulta sigue igual, pero ahora siempre con el tipo concreto elegido
    data = get_facilities_by_type(choice)
    df = pd.DataFrame(data)
    st.caption(f"{len(df)} resultados")
    if not df.empty:
        # Tabla compacta
        st.dataframe(
            df[["name","class","neighbourhood","district","municipality","telephone","email","uri"]],
            use_container_width=True,
            hide_index=True,
        )

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
        if not df.empty:
            pick = st.selectbox("Selecciona una facility", df["name"].tolist())
            if pick:
                sel = df[df["name"] == pick].iloc[0]
                st.markdown(f"**URI:** {sel['uri']}")
                st.markdown(f"**Tipo:** {sel['class']}")
                st.markdown(f"**Distrito/Municipio:** {sel.get('district','-')} / {sel.get('municipality','-')}")
                st.markdown(f"**Tel:** {sel.get('telephone','-')}  |  **Email:** {sel.get('email','-')}")

                # Obtener los transportes cercanos
                tr = get_nearby_transport(sel["uri"])

                # Mostrar transporte en columnas
                cols = st.columns(3)
                cols[0].markdown("**Metro:**<br>" + ("<br>".join(tr["Subway"]) or "—"), unsafe_allow_html=True)
                cols[1].markdown("**Bus:**<br>" + ("<br>".join(tr["Bus"]) or "—"), unsafe_allow_html=True)
                cols[2].markdown("**Cercanías:**<br>" + ("<br>".join(tr["Train"]) or "—"), unsafe_allow_html=True)


else:
    st.subheader("Explorar por localización")

    # --- Filtro por distrito ---
    district_list = get_districts()  # Obtener lista de distritos
    district_names = [d for _,d in district_list]
    district_choice = st.sidebar.selectbox("Selecciona distrito (opcional)", ["Ninguno"] + district_names, index=0)

    # Si se selecciona un distrito, filtrar barrios dentro de ese distrito
    if district_choice != "Ninguno":
        # Obtener barrios dentro del distrito
        district_uri = [d[0] for d in district_list if d[1] == district_choice][0]

        nh_list = get_neighbourhoods_in_district(district_uri)
        neighbourhood_names = [n[1] for n in nh_list]
        neighbourhood_choice = st.sidebar.selectbox("Selecciona barrio", neighbourhood_names, index=0)
        nh_uri = [n[0] for n in nh_list if n[1] == neighbourhood_choice][0]
        st.caption(f"Seleccionado: {district_choice} - {neighbourhood_choice}")
    else:
        # Si no hay distrito, mostrar todos los barrios
        nh_list = get_neighbourhoods()
        neighbourhood_names = [n[1] for n in nh_list]
        neighbourhood_choice = st.sidebar.selectbox("Selecciona barrio", neighbourhood_names, index=0)
        nh_uri = [n[0] for n in nh_list if n[1] == neighbourhood_choice][0]

    # Obtener y mostrar facilities
    st.caption(f"Facilities en {neighbourhood_choice}")
    facilities = get_facilities_in_neighbourhood(nh_uri)
    df = pd.DataFrame(facilities)
    st.caption(f"{len(df)} facilities dentro de {neighbourhood_choice}")
    if not df.empty:
        st.dataframe(df[["name", "class", "district", "municipality", "telephone", "email", "uri"]],
                     use_container_width=True, hide_index=True)

        map_df = df.dropna(subset=["lat", "long"]).copy()
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
    st.subheader("Detalle y transporte cercano")
    if not df.empty:
        pick = st.selectbox("Selecciona una facility", df["name"].tolist())
        if pick:
            sel = df[df["name"] == pick].iloc[0]
            st.markdown(f"**URI:** {sel['uri']}")
            st.markdown(f"**Tipo:** {sel['class']}")
            st.markdown(f"**Distrito/Municipio:** {sel.get('district','-')} / {sel.get('municipality','-')}")
            st.markdown(f"**Tel:** {sel.get('telephone','-')}  |  **Email:** {sel.get('email','-')}")

            # Obtener los transportes cercanos
            tr = get_nearby_transport(sel["uri"])

            # Mostrar transporte en columnas
            cols = st.columns(3)
            cols[0].markdown("**Metro:**<br>" + ("<br>".join(tr["Subway"]) or "—"), unsafe_allow_html=True)
            cols[1].markdown("**Bus:**<br>" + ("<br>".join(tr["Bus"]) or "—"), unsafe_allow_html=True)
            cols[2].markdown("**Cercanías:**<br>" + ("<br>".join(tr["Train"]) or "—"), unsafe_allow_html=True)
