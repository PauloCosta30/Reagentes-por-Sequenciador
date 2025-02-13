import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt
import os

# Função para carregar os dados do CSV ou criar um novo
def load_data(equipment):
    file_name = f"{equipment}_reagents.csv"
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    else:
        return pd.DataFrame({"Kit": reagents_dict[equipment], "Quantidade": [0] * len(reagents_dict[equipment])})

# Função para salvar os dados no CSV
def save_data(equipment, dataframe):
    file_name = f"{equipment}_reagents.csv"
    dataframe.to_csv(file_name, index=False)

# Lista inicial de reagentes para cada equipamento
reagents_dict = {
    "Illumina": ["P1 300", "P1 600", "P2 200", "P2 300", "P2 600", "P3 200", "P3 300", "P4 200", "P4 300", "Next500"],
    "PacBio": ["SMRT Cell 8M", "Sequel Binding Kit", "Sequencing Primer", "Clean-up Beads", "MagBeads", "DNA Prep Kit"]
}

st.title("📊 Controle de Reagentes por Equipamento")

# Seleção do equipamento
selected_equipment = st.selectbox("Selecione o Equipamento", ["Illumina", "PacBio"])

# Carregar os dados do equipamento selecionado
stocks = load_data(selected_equipment)

# Mostrar o estoque atual
st.subheader(f"📦 Estoque Atual - {selected_equipment}")
st.dataframe(stocks, height=300)

# Formulário para dar baixa nos reagentes
st.subheader(f"➖ Dar Baixa em Reagentes - {selected_equipment}")
selected_kit = st.selectbox("Selecione o kit", stocks["Kit"].tolist())
amount_to_deduct = st.number_input("Quantidade a dar baixa", min_value=1, step=1)

if st.button("Dar Baixa"):
    index = stocks[stocks["Kit"] == selected_kit].index[0]
    if stocks.loc[index, "Quantidade"] >= amount_to_deduct:
        stocks.loc[index, "Quantidade"] -= amount_to_deduct
        save_data(selected_equipment, stocks)
        st.success(f"{amount_to_deduct} unidades removidas do kit {selected_kit}.")
    else:
        st.error(f"Quantidade insuficiente no kit {selected_kit}.")
    stocks = load_data(selected_equipment)  # Atualiza a tabela imediatamente

# Mostrar o total de reagentes
st.subheader("📊 Total de Reagentes")
total_reagents = stocks["Quantidade"].sum()
st.metric(label=f"Quantidade total de reagentes para {selected_equipment}", value=total_reagents)

# Permitir adicionar unidades manualmente
st.subheader(f"➕ Adicionar Unidades - {selected_equipment}")
selected_kit_update = st.selectbox("Selecione o kit para adicionar unidades", stocks["Kit"].tolist(), key="update")
units_to_add = st.number_input("Quantidade a adicionar", min_value=1, step=1, key="add")

if st.button("Adicionar Unidades"):
    index_update = stocks[stocks["Kit"] == selected_kit_update].index[0]
    stocks.loc[index_update, "Quantidade"] += units_to_add
    save_data(selected_equipment, stocks)
    st.success(f"{units_to_add} unidades adicionadas ao kit {selected_kit_update}.")
    stocks = load_data(selected_equipment)  # Atualiza a tabela imediatamente

# Gráfico de barras para visualização
st.subheader(f"📈 Gráfico de Quantidade por Kit - {selected_equipment}")
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(stocks["Kit"], stocks["Quantidade"], color='skyblue')
ax.set_title(f"Quantidade de Reagentes por Kit - {selected_equipment}")
ax.set_xlabel("Kit")
ax.set_ylabel("Quantidade")
plt.xticks(rotation=45)
st.pyplot(fig)

# Exportar tabela e gráfico para PDF (layout simples)
st.subheader("📄 Exportar Relatório em PDF")

def generate_pdf(dataframe, equipment_name, fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=f"Relatório de Reagentes - {equipment_name}", ln=True, align="C")
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(90, 10, "Kit", 1, 0, "C")
    pdf.cell(40, 10, "Quantidade", 1, 1, "C")
    
    pdf.set_font("Arial", size=12)
    for i in range(len(dataframe)):
        kit = dataframe.loc[i, "Kit"]
        quantidade = dataframe.loc[i, "Quantidade"]
        pdf.cell(90, 10, kit, 1, 0, "L")
        pdf.cell(40, 10, str(quantidade), 1, 1, "C")
    
    pdf.ln(10)
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    pdf.image(img_buffer, x=10, y=pdf.get_y() + 10, w=190)
    
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

if st.button("Baixar PDF"):
    pdf_data = generate_pdf(stocks, selected_equipment, fig)
    st.download_button(
        "📥 Clique para baixar o PDF", data=pdf_data, file_name=f"controle_reagentes_{selected_equipment}.pdf", mime="application/pdf"
    )


