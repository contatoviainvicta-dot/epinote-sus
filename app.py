import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

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
    import io

    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    # Encontrar início da tabela
    inicio = None
    for i, linha in enumerate(linhas):
        if "Ano" in linha:
            inicio = i
            break

    if inicio is None:
        st.error("❌ Não foi possível encontrar a tabela no CSV")
        st.text(content[:500])
        return None

    dados = "\n".join(linhas[inicio:])

    try:
        df = pd.read_csv(
            io.StringIO(dados),
            sep=";",
            engine="python"
        )
    except:
        st.error("❌ Erro ao ler CSV")
        return None

    # Limpar nomes
    df.columns = df.columns.str.replace('"', '').str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # 🔥 CASO ESPECIAL: tudo veio em uma coluna só
    if df.shape[1] == 1:
        col = df.columns[0]

        # separar manualmente
        df = df[col].str.split(";", expand=True)

        if df.shape[1] < 2:
            st.error("❌ Não foi possível dividir os dados corretamente")
            st.write(df.head())
            return None

    # pegar só duas colunas
    df = df.iloc[:, :2]
    df.columns = ["Ano", "Casos"]

    # remover "Total"
    df = df[df["Ano"] != "Total"]

    # limpar aspas
    df["Ano"] = df["Ano"].astype(str).str.replace('"', '')
    df["Casos"] = df["Casos"].astype(str).str.replace('"', '')

    # converter
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df["Casos"] = pd.to_numeric(df["Casos"], errors="coerce")

    df = df.dropna()

    # ordenar
    df = df.sort_values("Ano")

    return df
# =========================
# EXTRAIR TÍTULO
# =========================
def extrair_titulo(uploaded_file):
    content = uploaded_file.getvalue().decode("latin1")
    return content.splitlines()[0]
def ler_tabnet(uploaded_file):
    import io

    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    # Encontrar cabeçalho (linha com "Ano")
    inicio = None
    for i, linha in enumerate(linhas):
        if "Ano" in linha:
            inicio = i
            break

    if inicio is None:
        st.error("❌ Não foi possível encontrar a tabela no CSV")
        st.text(content[:500])
        return None

    dados = "\n".join(linhas[inicio:])

    try:
        df = pd.read_csv(
            io.StringIO(dados),
            sep=";",
            engine="python"
        )
    except Exception as e:
        st.error("❌ Erro ao ler CSV")
        st.write(str(e))
        return None

    # Limpar colunas
    df.columns = df.columns.str.replace('"', '').str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # Garantir pelo menos 2 colunas
    if df.shape[1] < 2:
        st.error("❌ CSV não possui colunas suficientes")
        st.write(df.head())
        return None

    # Pegar as duas primeiras colunas SEM depender do nome
    df = df.iloc[:, :2]
    df.columns = ["Ano", "Casos"]

    # Remover linha Total
    df = df[df["Ano"] != "Total"]

    # Converter tipos
    df["Ano"] = pd

# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:

    titulo = extrair_titulo(arquivo)
    df = ler_tabnet(arquivo)

    if df is None or df.empty:
        st.error("❌ Não foi possível processar o CSV do TabNet.")
        st.stop()

    # =========================
    # EXIBIÇÃO
    # =========================
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
    ax.grid()

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
    # NOTA EPIDEMIOLÓGICA
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
