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
# LEITURA ROBUSTA DO TABNET
# =========================
def ler_tabnet(uploaded_file):
    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    dados = []

    for linha in linhas:
        linha = linha.strip()

        if not linha:
            continue

        # remover aspas
        linha = linha.replace('"', '')

        # ignorar textos desnecessários
        if "Total" in linha or "Fonte" in linha or "Nota" in linha:
            continue

        # separar por ; ou espaço
        if ";" in linha:
            partes = linha.split(";")
        else:
            partes = linha.split()

        if len(partes) < 2:
            continue

        ano = partes[0].strip()
        valor = partes[-1].strip()

        try:
            ano = int(ano)
            valor = float(valor)
            dados.append([ano, valor])
        except:
            continue

    if not dados:
        st.error("❌ Não foi possível extrair dados válidos do CSV")
        st.text(content[:500])
        return None

    df = pd.DataFrame(dados, columns=["Ano", "Casos"])
    df = df.sort_values("Ano")

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

    # =========================
    # EXIBIÇÃO
    # =========================
    st.subheader("📄 Fonte dos dados")
    st.write(titulo)

    st.subheader("📊 Dados processados")
    st.write(df)

    # =========================
    # ALERTA SÉRIE CURTA
    # =========================
    if len(df) < 3:
        st.warning("⚠️ Série temporal muito curta — interpretação limitada")

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

    valor_inicial = df["Casos"].iloc[0]

    if valor_inicial == 0:
        variacao = 0
    else:
        variacao = ((df["Casos"].iloc[-1] - valor_inicial) / valor_inicial) * 100

    # interpretação inteligente
    if tendencia == "crescente":
        interpretacao = "indica possível aumento da transmissão ou melhoria na detecção dos casos."
    elif tendencia == "decrescente":
        interpretacao = "sugere redução da transmissão ou impacto de medidas de controle."
    else:
        interpretacao = "indica estabilidade na ocorrência dos casos ao longo do período."

    # =========================
    # NOTA EPIDEMIOLÓGICA
    # =========================
    st.subheader("📝 Nota Epidemiológica")

    texto = f"""
Observa-se comportamento **{tendencia}** no número de casos ao longo do período analisado.

O maior número de registros ocorreu em {int(pico['Ano'])}, com {int(pico['Casos'])} casos, enquanto o menor foi observado em {int(minimo['Ano'])}, com {int(minimo['Casos'])} casos.

A variação percentual no período foi de aproximadamente {variacao:.1f}%.

Os achados {interpretacao}

Recomenda-se fortalecimento das ações de vigilância epidemiológica, diagnóstico oportuno e medidas de prevenção direcionadas à população de risco.
"""

    st.write(texto)

else:
    st.info("⬆️ Envie um arquivo CSV do TabNet para iniciar a análise.")
