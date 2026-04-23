import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="EpiNote", layout="centered")

st.title("📊 EpiNote - Gerador de Nota Epidemiológica")
st.write("Envie um arquivo CSV do TabNet (DATASUS) para análise automática.")

# =========================
# UPLOAD
# =========================
arquivo = st.file_uploader("📂 Upload do CSV do TabNet", type=["csv"])


# =========================
# FUNÇÃO ROBUSTA TABNET
# =========================
def ler_tabnet(uploaded_file):
    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    dados_limpos = []

    for linha in linhas:
        linha = linha.strip()

        if not linha:
            continue
        if "Total" in linha or "Fonte" in linha or "Nota" in linha:
            continue

        partes = linha.split()

        if len(partes) >= 2:
            ano = partes[0]
            casos = partes[-1]

            # limpar possíveis vírgulas
            casos = casos.replace(",", ".")
            
            try:
                ano = int(ano)
                casos = float(casos)

                dados_limpos.append([ano, casos])

            except:
                continue

    if not dados_limpos:
        st.error("❌ Não foi possível extrair dados válidos do CSV.")
        st.write("🔍 Conteúdo inicial do arquivo:")
        st.text(content[:500])
        return None

    df = pd.DataFrame(dados_limpos, columns=["Ano", "Casos"])

    return df


# =========================
# EXTRAIR TÍTULO
# =========================
def extrair_titulo(uploaded_file):
    content = uploaded_file.getvalue().decode("latin1")
    return content.splitlines()[0]


# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:

    titulo = extrair_titulo(arquivo)
    df = ler_tabnet(arquivo)

    if df is None or df.empty:
        st.error("❌ Não foi possível processar o CSV do TabNet.")
        st.stop()

    st.subheader("📄 Fonte dos dados")
    st.write(titulo)

    st.subheader("📊 Dados processados")
    st.write(df)

    # =========================
    # GRÁFICO
    # =========================
    st.subheader("📈 Tendência Temporal")

    fig, ax = plt.subplots()
    sns.lineplot(data=df, x="Ano", y="Casos", marker="o", ax=ax)

    ax.set_ylabel("Casos")
    ax.set_xlabel("Ano")

    st.pyplot(fig)

    # =========================
    # ANÁLISE
    # =========================
    tendencia = "estável"

    if df["Casos"].iloc[-1] > df["Casos"].iloc[0]:
        tendencia = "crescente"
    elif df["Casos"].iloc[-1] < df["Casos"].iloc[0]:
        tendencia = "decrescente"

    pico = df.loc[df["Casos"].idxmax()]
    minimo = df.loc[df["Casos"].idxmin()]

    variacao = ((df["Casos"].iloc[-1] - df["Casos"].iloc[0]) / df["Casos"].iloc[0]) * 100

    # =========================
    # NOTA
    # =========================
    st.subheader("📝 Nota Epidemiológica")

    texto = f"""
Observa-se comportamento **{tendencia}** no número de casos ao longo do período analisado.

O maior número de registros ocorreu em {int(pico['Ano'])}, com {int(pico['Casos'])} casos, enquanto o menor foi observado em {int(minimo['Ano'])}, com {int(minimo['Casos'])} casos.

A variação percentual no período foi de aproximadamente {variacao:.1f}%.

Os achados sugerem possível influência de fatores ambientais, sociais e operacionais da vigilância em saúde.

Recomenda-se fortalecimento das ações de vigilância epidemiológica, diagnóstico oportuno e medidas de prevenção direcionadas à população de risco.
"""

    st.write(texto)

else:
    st.info("⬆️ Envie um arquivo CSV do TabNet para iniciar a análise.")
