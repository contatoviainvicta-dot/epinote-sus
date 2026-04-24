import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress


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
    # 📊 TAXA POR 100 MIL
    # =========================
    st.subheader("📊 Taxa por 100 mil habitantes")

    pop_padrao = st.number_input("População estimada", value=3000000)

    df_final["Taxa_100k"] = (df_final["Casos"] / pop_padrao) * 100000

    st.write(df_final[["Ano", "Doenca", "Casos", "Taxa_100k"]])

    # =========================
    # 📈 TENDÊNCIA ESTATÍSTICA
    # =========================
    st.subheader("📈 Tendência Estatística")

    for doenca in df_final["Doenca"].unique():
        df_temp = df_final[df_final["Doenca"] == doenca].copy()

    # 🔥 GARANTIR DADOS LIMPOS
        df_temp["Ano"] = pd.to_numeric(df_temp["Ano"], errors="coerce")
        df_temp["Casos"] = pd.to_numeric(df_temp["Casos"], errors="coerce")
        df_temp = df_temp.dropna()

    # 🔥 PRECISA DE PELO MENOS 3 PONTOS
        if len(df_temp) < 3:
            st.info(f"{doenca}: dados insuficientes para regressão")
            continue

        try:
            x = df_temp["Ano"]
            y = df_temp["Casos"]

            slope, intercept, r_value, p_value, std_err = linregress(x, y)

            if p_value < 0.05:
                if slope > 0:
                    interpretacao = "tendência crescente significativa"
                else:
                    interpretacao = "tendência decrescente significativa"
            else:
                interpretacao = "sem tendência estatisticamente significativa"

            st.write(f"**{doenca}**: {interpretacao} (p={p_value:.3f})")

        except Exception as e:
            st.error(f"Erro na análise de {doenca}: {e}")

    # =========================
    # 🚨 ALERTAS (Z-SCORE)
    # =========================
    st.subheader("🚨 Alertas Epidemiológicos (Z-score)")

    alertas = []

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
            alertas.append((doenca, z))

    if alertas:
        for doenca, z in alertas:
            st.error(f"🚨 Surto possível em {doenca} (Z={z:.2f})")
    else:
        st.success("✅ Nenhum surto detectado")
    st.subheader("📊 Canal Endêmico Mensal")

    for doenca in df_final["Doenca"].unique():
        df_temp = df_final[df_final["Doenca"] == doenca].copy()

    # =========================
    # PREPARAÇÃO DOS DADOS
    # =========================
        df_temp["Ano"] = pd.to_numeric(df_temp["Ano"], errors="coerce")
        df_temp["Mes"] = pd.to_numeric(df_temp["Mes"], errors="coerce")
        df_temp["Casos"] = pd.to_numeric(df_temp["Casos"], errors="coerce")

        df_temp = df_temp.dropna()

        if df_temp.empty:
            continue

    # =========================
    # CALCULAR CANAL POR MÊS
    # =========================
            canal = df_temp.groupby("Mes")["Casos"].agg(["mean", "std"]).reset_index()

            canal["limite_inferior"] = canal["mean"] - canal["std"]
            canal["limite_superior"] = canal["mean"] + canal["std"]
            canal["limite_epidemia"] = canal["mean"] + 2 * canal["std"]

    # =========================
    # DADOS DO ANO MAIS RECENTE
    # =========================
            ano_recente = df_temp["Ano"].max()
            df_recente = df_temp[df_temp["Ano"] == ano_recente]

            df_plot = canal.merge(df_recente, on="Mes", how="left")

    # =========================
    # CLASSIFICAÇÃO
    # =========================
            status_mes = []

            for _, row in df_plot.iterrows():
                if pd.isna(row["Casos"]):
                    status_mes.append("Sem dado")
            elif row["Casos"] > row["limite_epidemia"]:
                    status_mes.append("🔴 Epidemia")
            elif row["Casos"] > row["limite_superior"]:
                    status_mes.append("🟡 Acima do esperado")
            elif row["Casos"] < row["limite_inferior"]:
                    status_mes.append("🔵 Abaixo do esperado")
            else:
                status_mes.append("🟢 Normal")

        df_plot["Status"] = status_mes

    # =========================
    # EXIBIÇÃO
    # =========================
        st.markdown(f"### {doenca} - {int(ano_recente)}")

        st.write(df_plot[["Mes", "Casos", "Status"]])

    # =========================
    # GRÁFICO
    # =========================
        fig, ax = plt.subplots()

        ax.plot(df_plot["Mes"], df_plot["mean"], label="Média")
        ax.plot(df_plot["Mes"], df_plot["limite_superior"], linestyle="--", label="+1 DP")
        ax.plot(df_plot["Mes"], df_plot["limite_epidemia"], linestyle="--", label="+2 DP")

        ax.plot(df_plot["Mes"], df_plot["Casos"], marker="o", label="Ano atual")

        ax.fill_between(
            df_plot["Mes"],
            df_plot["limite_inferior"],
            df_plot["limite_superior"],
            alpha=0.1,
            label="Faixa esperada"
        )

        ax.set_title(f"Canal Endêmico Mensal - {doenca}")
        ax.set_xlabel("Mês")
        ax.set_ylabel("Casos")
        ax.legend()
        ax.grid()

        st.pyplot(fig)
else:
    st.info("⬆️ Envie múltiplos arquivos CSV para comparação.")
