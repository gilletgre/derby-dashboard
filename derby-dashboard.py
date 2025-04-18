import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Derby Dashboard", layout="wide")
st.title("📊 Tableau de bord Derby - Visualisation intelligente des abonnements")

# --- Upload du fichier ---
st.sidebar.header("📁 Importer un fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisir un fichier .xlsx", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=None)
        sheet_names = list(df.keys())
        default_sheet = sheet_names[0] if "Address_Checker_Details_Excel" not in sheet_names else "Address_Checker_Details_Excel"
        selected_sheet = st.sidebar.selectbox("Sélectionner l'onglet à afficher", sheet_names, index=sheet_names.index(default_sheet))

        df = df[selected_sheet]

        # Normalisation des noms de colonnes
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("__", "_")

        # Conversion explicite de pay_agreement_num en chaîne (évite les formats float mal interprétés)
        if 'pay_agreement_num' in df.columns:
            df['pay_agreement_num'] = df['pay_agreement_num'].astype(str).str.replace('.0', '', regex=False)

        # Vérification des colonnes clés
        required_cols = ['installation_address', 'subscriber_number', 'product_description']
        if not all(col in df.columns for col in required_cols):
            st.error("❌ Le fichier ne contient pas toutes les colonnes clés requises : installation_address, subscriber_number, product_description")
            st.stop()

        st.success("✅ Données chargées avec succès")

        # Filtres dynamiques
        st.sidebar.header("🔎 Filtres")
        address_filter = st.sidebar.multiselect("Installation Address", sorted(df['installation_address'].dropna().unique()))
        pay_agreement_name_filter = st.sidebar.multiselect("Pay Agreement Name", sorted(df['pay_agreement_name'].dropna().unique()) if 'pay_agreement_name' in df else [])
        pay_agreement_num_filter = st.sidebar.multiselect("Pay Agreement Num", sorted(df['pay_agreement_num'].dropna().unique()) if 'pay_agreement_num' in df else [])
        product_filter = st.sidebar.multiselect("Product Description", sorted(df['product_description'].dropna().unique()))

        filtered_df = df.copy()
        if address_filter:
            filtered_df = filtered_df[filtered_df['installation_address'].isin(address_filter)]
        if pay_agreement_name_filter:
            filtered_df = filtered_df[filtered_df['pay_agreement_name'].isin(pay_agreement_name_filter)]
        if pay_agreement_num_filter:
            filtered_df = filtered_df[filtered_df['pay_agreement_num'].isin(pay_agreement_num_filter)]
        if product_filter:
            filtered_df = filtered_df[filtered_df['product_description'].isin(product_filter)]

        # KPIs
        st.subheader("🔢 Statistiques clés")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Lignes totales", len(filtered_df))
        col2.metric("Adresses uniques", filtered_df['installation_address'].nunique())
        col3.metric("Abonnés uniques", filtered_df['subscriber_number'].nunique())
        col4.metric("Produits différents", filtered_df['product_description'].nunique())

        # Vue par Subscriber Number
        st.subheader("📞 Vue par ligne d'abonné")
        for subscriber, group in filtered_df.groupby('subscriber_number'):
            with st.expander(f"Ligne : {subscriber}"):
                address = group['installation_address'].iloc[0]
                regime = group['regime_name'].iloc[0] if 'regime_name' in group else ""
                contract = group['contract_name'].iloc[0] if 'contract_name' in group else ""
                pay_agreement = group['pay_agreement_name'].iloc[0] if 'pay_agreement_name' in group else ""
                pay_agreement_num = group['pay_agreement_num'].iloc[0] if 'pay_agreement_num' in group else ""
                billing_start = group['billing_start_date'].min() if 'billing_start_date' in group else ""
                contract_end = group['contract_end_date'].max() if 'contract_end_date' in group else ""

                st.markdown(f"**Adresse :** {address}")
                st.markdown(f"**Contrat :** {contract} (fin : {contract_end})")
                st.markdown(f"**Régime :** {regime}")
                st.markdown(f"**Pay Agreement :** {pay_agreement} (#{pay_agreement_num})")
                st.markdown(f"**Début de facturation :** {billing_start}")

                products = group['product_description'].dropna().unique()
                st.markdown("**Produits :**")
                st.markdown("<ul>" + "".join([f"<li>{p}</li>" for p in products]) + "</ul>", unsafe_allow_html=True)

        # Visualisation
        st.subheader("📈 Répartition des produits")
        fig = px.histogram(filtered_df, x='product_description')
        st.plotly_chart(fig, use_container_width=True)

        if 'billing_start_date' in filtered_df:
            st.subheader("📅 Timeline de facturation")
            fig2 = px.histogram(filtered_df, x='billing_start_date')
            st.plotly_chart(fig2, use_container_width=True)

        # Tableau final formaté pour la lecture
        st.subheader("📋 Tableau complet formaté")
        display_cols = ['installation_address', 'subscriber_number', 'product_description', 'contract_name', 'contract_end_date', 'billing_start_date', 'pay_agreement_num', 'pay_agreement_name', 'regime_name']
        display_cols = [col for col in display_cols if col in filtered_df.columns]
        table = filtered_df[display_cols].drop_duplicates().sort_values(by=['installation_address', 'subscriber_number'])
        st.dataframe(table, use_container_width=True)

        # Export CSV
        st.download_button("📥 Télécharger les données filtrées (CSV)", data=table.to_csv(index=False).encode('utf-8'), file_name="export_derby.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")
else:
    st.info("Veuillez importer un fichier Excel .xlsx contenant vos données Derby.")
