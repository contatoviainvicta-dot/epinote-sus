import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Painel Epidemiológico", layout="wide")

st.title("📊 Painel de Vigilância Epidemiológica")
st.write("Compare múltiplas doenças a partir de arquivos CSV do TabNet.")

# =========================
# UPLOAD
# =========================
arquivos = st.file_uploader(
    "📂 Upload de múltiplos CSVs",
    type=["csv"],
    accept_multiple_files=True
)

# =========================
# FUNÇÃO: LEITURA TABNET
# =========================
def ler_tabnet(uploaded_file):
    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    dados = []

    for linha in linhas:
        linha = linha.strip().replace('"', '')

        if not linha:
            continue
        if "Total" in linha or "Fonte" in linha or "Nota" in linha:
            continue

        if ";" in linha:
            partes = linha.split(";")
        else:
            partes = linha.split()

        # 🔥 FORMATO MENSAL (3 colunas)
        if len(partes) >= 3:
            try:
                ano = int(partes[0])
                mes = int(partes[1])
                valor = float(partes[-1].replace(",", "."))
                dados.append([ano, mes, valor])
            except:
                continue

        # 🔥 FORMATO ANUAL (2 colunas)
        elif len(partes) >= 2:
            try:
                ano = int(partes[0])
                valor = float(partes[-1].replace(",", "."))
                dados.append([ano, valor])
            except:
                continue

    if not dados:
        return None

    # =========================
    # DETECTAR FORMATO
    # =========================
    if len(dados[0]) == 3:
        df = pd.DataFrame(dados, columns=["Ano", "Mes", "Casos"])
        df = df.sort_values(["Ano", "Mes"])
    else:
        df = pd.DataFrame(dados, columns=["Ano", "Casos"])
        df = df.sort_values("Ano")

    return df
# =========================
# FUNÇÃO: NOME DA DOENÇA
# =========================
def extrair_nome_doenca(uploaded_file):
    content = uploaded_file.getvalue().decode("latin1")
    primeira_linha = content.splitlines()[0]

    nome = primeira_linha.split("-")[0].strip()
    nome = nome.replace("Vírus", "").strip()

    return nome

# =========================
# EXECUÇÃO PRINCIPAL
# =========================
if arquivos:

    lista_df = []

    for arquivo in arquivos:
        df = ler_tabnet(arquivo)

        if df is not None:
            nome = extrair_nome_doenca(arquivo)
            df["Doenca"] = nome
            lista_df.append(df)

    if not lista_df:
        st.error("❌ Nenhum arquivo válido.")
        st.stop()

    df_final = pd.concat(lista_df)

    # =========================
    # DADOS
    # =========================
    st.subheader("📊 Dados combinados")
    st.write(df_final)

    # =========================
    # GRÁFICO
    # =========================
    st.subheader("📈 Comparação entre doenças")

    fig, ax = plt.subplots()
    sns.lineplot(data=df_final, x="Ano", y="Casos", hue="Doenca", marker="o", ax=ax)
    ax.grid()
    st.pyplot(fig)

    # =========================
    # INDICADORES
    # =========================
    st.subheader("📊 Indicadores por doença")

    resumo = (
        df_final.groupby("Doenca")["Casos"]
        .agg(Total="sum", Média="mean", Máximo="max")
        .reset_index()
    )

    st.write(resumo)

    # =========================
    # TAXA
    # =========================
    st.subheader("📊 Taxa por 100 mil habitantes")

    pop_padrao = st.number_input("População estimada", value=3000000)
    df_final["Taxa_100k"] = (df_final["Casos"] / pop_padrao) * 100000

    st.write(df_final[["Ano", "Doenca", "Casos", "Taxa_100k"]])

    # =========================
    # TENDÊNCIA (HÍBRIDA)
    # =========================
    st.subheader("📈 Tendência Estatística")

    for doenca in df_final["Doenca"].unique():
        df_temp = df_final[df_final["Doenca"] == doenca].copy()

        df_temp["Ano"] = pd.to_numeric(df_temp["Ano"], errors="coerce")
        df_temp["Casos"] = pd.to_numeric(df_temp["Casos"], errors="coerce")
        df_temp = df_temp.dropna().sort_values("Ano")

        if len(df_temp) < 3:
            st.info(f"{doenca}: dados insuficientes")
            continue

        x = df_temp["Ano"]
        y = df_temp["Casos"]

        try:
            from scipy.stats import linregress
            slope, _, _, p_value, _ = linregress(x, y)

            if p_value < 0.05:
                interpretacao = "crescente" if slope > 0 else "decrescente"
            else:
                interpretacao = "sem tendência significativa"

            st.write(f"**{doenca}**: {interpretacao} (p={p_value:.3f})")

        except:
            slope = (y.iloc[-1] - y.iloc[0]) / (x.iloc[-1] - x.iloc[0])
            interpretacao = "crescente" if slope > 0 else "decrescente"
            st.warning(f"{doenca}: {interpretacao} (modo simples)")

    # =========================
    # ALERTAS
    # =========================
    st.subheader("🚨 Alertas Epidemiológicos")

    for doenca in df_final["Doenca"].unique():
        df_temp = df_final[df_final["Doenca"] == doenca]

        if len(df_temp) < 3:
            continue

        media = df_temp["Casos"].mean()
        std = df_temp["Casos"].std()
        ultimo = df_temp["Casos"].iloc[-1]

        if std == 0:
            continue

        z = (ultimo - media) / std

        if z > 2:
            st.error(f"🚨 Surto possível em {doenca} (Z={z:.2f})")

    # =========================
    # CANAL ENDÊMICO MENSAL
    # =========================
    st.subheader("📊 Canal Endêmico Mensal")

    if "Mes" not in df_final.columns:
        st.warning("⚠️ CSV não possui coluna 'Mes'")
    else:

        for doenca in df_final["Doenca"].unique():
            df_temp = df_final[df_final["Doenca"] == doenca].copy()

            df_temp["Mes"] = pd.to_numeric(df_temp["Mes"], errors="coerce")
            df_temp["Casos"] = pd.to_numeric(df_temp["Casos"], errors="coerce")
            df_temp = df_temp.dropna()

            if len(df_temp) < 6:
                continue

            canal = df_temp.groupby("Mes")["Casos"].agg(["mean", "std"]).reset_index()

            canal["lim_sup"] = canal["mean"] + canal["std"]
            canal["lim_epi"] = canal["mean"] + 2 * canal["std"]

            ano_recente = df_temp["Ano"].max()
            df_recente = df_temp[df_temp["Ano"] == ano_recente]

            df_plot = canal.merge(df_recente, on="Mes", how="left")

            st.markdown(f"### {doenca}")

            fig, ax = plt.subplots()

            ax.plot(df_plot["Mes"], df_plot["mean"], label="Média")
            ax.plot(df_plot["Mes"], df_plot["lim_sup"], "--", label="+1DP")
            ax.plot(df_plot["Mes"], df_plot["lim_epi"], "--", label="+2DP")
            ax.plot(df_plot["Mes"], df_plot["Casos"], marker="o", label="Atual")

            ax.legend()
            ax.grid()

            st.pyplot(fig)

else:
    st.info("⬆️ Envie arquivos CSV para iniciar.")
