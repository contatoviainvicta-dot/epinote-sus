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
# FUNÇÃO PARA LIMPAR TABNET
# =========================
def ler_tabnet(uploaded_file):
    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    # Detectar cabeçalho real
    inicio = None
    for i, linha in enumerate(linhas):
        if "Ano" in linha and "Casos" in linha:
            inicio = i
            break

    if inicio is None:
        return None

    dados = "\n".join(linhas[inicio:])

    # Testar separadores
    for sep in [";", ",", "\t", r"\s+"]:
        try:
            df = pd.read_csv(io.StringIO(dados), sep=sep, engine="python")
            if df.shape[1] >= 2:
                break
        except:
            continue

    # Padronizar colunas
    # Detectar colunas automaticamente
    colunas = df.columns.tolist()

# Encontrar coluna de ano
    col_ano = None
    for c in colunas:
        if "Ano" in str(c):
            col_ano = c
        break

# Encontrar coluna de casos
col_casos = None
for c in colunas:
    if "caso" in str(c).lower():
        col_casos = c
        break

if col_ano is None or col_casos is None:
    st.error("❌ Não foi possível identificar colunas de Ano e Casos")
    return None

df = df[[col_ano, col_casos]]
df.columns = ["Ano", "Casos"]

    # Limpeza
    df = df[df["Ano"] != "Total"]
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df["Casos"] = pd.to_numeric(df["Casos"], errors="coerce")
    df.dropna(inplace=True)

    return df


# =========================
# EXTRAIR NOME DA DOENÇA
# =========================
def extrair_titulo(uploaded_file):
    content = uploaded_file.getvalue().decode("latin1")
    primeira_linha = content.splitlines()[0]
    return primeira_linha


# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:

    titulo = extrair_titulo(arquivo)
    df = ler_tabnet(arquivo)

    if df is None or df.empty:
        st.error("❌ Não foi possível processar o CSV. Verifique o formato do TabNet.")
        st.stop()

    # =========================
    # EXIBIR INFORMAÇÕES
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

    st.pyplot(fig)

    # =========================
    # ANÁLISE AUTOMÁTICA
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
