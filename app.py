import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

st.set_page_config(page_title="EpiNote", layout="centered")

st.title("📊 EpiNote - Nota Epidemiológica Automática")

# =========================
# INPUTS
# =========================
doenca = st.text_input("🦠 Doença", "Leptospirose")
local = st.text_input("📍 Local", "Distrito Federal")

arquivo = st.file_uploader("📂 Envie o CSV do TabNet", type=["csv"])

# =========================
# FUNÇÃO INTELIGENTE TABNET
# =========================
def ler_tabnet(uploaded_file):
    content = uploaded_file.read().decode("latin1")
    linhas = content.splitlines()

    # Encontrar linha do cabeçalho real
    inicio = None
    for i, linha in enumerate(linhas):
        if "Ano" in linha and "Casos" in linha:
            inicio = i
            break

    if inicio is None:
        st.error("❌ Não foi possível identificar a tabela no CSV")
        return None

    dados = "\n".join(linhas[inicio:])

    # Tentar diferentes separadores
    for sep in [";", ",", "\t", r"\s+"]:
        try:
            df = pd.read_csv(
                io.StringIO(dados),
                sep=sep,
                engine="python"
            )

            if df.shape[1] >= 2:
                break
        except:
            continue

    # Ajustar colunas
    df = df.iloc[:, :2]
    df.columns = ["Ano", "Casos"]

    # Remover lixo
    df = df[df["Ano"] != "Total"]
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce")
    df["Casos"] = pd.to_numeric(df["Casos"], errors="coerce")
    df.dropna(inplace=True)

    return df

# =========================
# EXECUÇÃO
# =========================
if arquivo is not None:

    df = ler_tabnet(arquivo)

    if df is not None:

        st.subheader("📄 Dados processados")
        st.write(df)

        # =========================
        # GRÁFICO
        # =========================
        st.subheader("📈 Tendência Temporal")

        fig, ax = plt.subplots()
        sns.lineplot(data=df, x="Ano", y="Casos", marker="o", ax=ax)

        ax.set_title(f"{doenca} - {local}")
        ax.set_ylabel("Casos")

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

        # =========================
        # TEXTO AUTOMÁTICO
        # =========================
        st.subheader("📝 Nota Epidemiológica")

        texto = f"""
Observa-se comportamento **{tendencia}** dos casos de {doenca} no {local} no período analisado.

O maior número de casos ocorreu em {int(pico['Ano'])}, com {int(pico['Casos'])} registros, enquanto o menor foi observado em {int(minimo['Ano'])}, com {int(minimo['Casos'])} casos.

Os achados sugerem possível influência de fatores ambientais, sociais e condições de saneamento, especialmente no contexto de doenças como a leptospirose, associadas a períodos chuvosos e exposição a água contaminada.

Recomenda-se intensificação das ações de vigilância epidemiológica, controle ambiental e educação em saúde.
"""

        st.write(texto)

else:
    st.info("⬆️ Faça upload do CSV do TabNet para gerar a análise")
