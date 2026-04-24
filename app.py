import pandas as pd
import matplotlib.pyplot as plt

# Criar dados manualmente (mais seguro que CSV bagunçado)
dados = {
    "Ano": [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024],
    "Casos": [203,220,283,388,298,291,355,399,320,146]
}

df = pd.DataFrame(dados)

# Gráfico
plt.figure()
plt.plot(df["Ano"], df["Casos"], marker='o')
plt.title("Sífilis Congênita - Distrito Federal")
plt.xlabel("Ano")
plt.ylabel("Casos")
plt.grid()
plt.show()
