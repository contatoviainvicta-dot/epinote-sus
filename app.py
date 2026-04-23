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

        if len(partes) < 2:
            continue

        try:
            ano = int(partes[0])
            valor = float(partes[-1].replace(",", "."))
            dados.append([ano, valor])
        except:
            continue

    if not dados:
        return None

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

    sns.lineplot(
        data=df_final,
        x="Ano",
        y="Casos",
        hue="Doenca",
        marker="o",
        ax=ax
    )

    ax.set_xlabel("Ano")
    ax.set_ylabel("Casos")
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
    # 🚨 ALERTAS EPIDEMIOLÓGICOS
    # =========================
    st.subheader("🚨 Alertas Epidemiológicos")

    alertas = []

    for doenca in df_final["Doenca"].unique():
        df_temp = df_final[df_final["Doenca"] == doenca]

        if len(df_temp) < 3:
            continue

        media = df_temp["Casos"].mean()
        ultimo = df_temp["Casos"].iloc[-1]

        if media == 0:
            continue

        aumento = (ultimo - media) / media

        if aumento > 0.5:
            alertas.append((doenca, aumento))

    if alertas:
        for doenca, aumento in alertas:
            st.error(f"🚨 Alerta: aumento de {aumento*100:.1f}% em {doenca}")
    else:
        st.success("✅ Nenhum alerta epidemiológico identificado")

else:
    st.info("⬆️ Envie múltiplos arquivos CSV para comparação.")
