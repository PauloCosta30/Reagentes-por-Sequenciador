import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
import tempfile

# Lista inicial de reagentes para cada equipamento
reagents_dict = {
    "Illumina": ["P1 300", "P1 600", "P2 200", "P2 300", "P2 600", "P3 200", "P3 300", "P4 200", "P4 300", "Next500"],
    "PacBio": ["SMRT Cell 8M", "Sequel Binding Kit", "Sequencing Primer", "Clean-up Beads", "MagBeads", "DNA Prep Kit"]
}

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
    try:
        index = stocks[stocks["Kit"] == selected_kit].index[0]
        if stocks.loc[index, "Quantidade"] >= amount_to_deduct:
            stocks.loc[index, "Quantidade"] -= amount_to_deduct
            save_data(selected_equipment, stocks)
            st.success(f"{amount_to_deduct} unidades removidas do kit {selected_kit}.")
        else:
            st.error(f"Quantidade insuficiente no kit {selected_kit}.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao dar baixa: {e}")
    # Recarregar os dados após modificação
    stocks = load_data(selected_equipment)

# Mostrar o total de reagentes
st.subheader("📊 Total de Reagentes")
total_reagents = stocks["Quantidade"].sum()
st.metric(label=f"Quantidade total de reagentes para {selected_equipment}", value=total_reagents)

# Permitir adicionar unidades manualmente
st.subheader(f"➕ Adicionar Unidades - {selected_equipment}")
selected_kit_update = st.selectbox("Selecione o kit para adicionar unidades", stocks["Kit"].tolist(), key="update")
units_to_add = st.number_input("Quantidade a adicionar", min_value=1, step=1, key="add")

if st.button("Adicionar Unidades"):
    try:
        index_update = stocks[stocks["Kit"] == selected_kit_update].index[0]
        stocks.loc[index_update, "Quantidade"] += units_to_add
        save_data(selected_equipment, stocks)
        st.success(f"{units_to_add} unidades adicionadas ao kit {selected_kit_update}.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao adicionar unidades: {e}")
    # Recarregar os dados após modificação
    stocks = load_data(selected_equipment)

# Gráfico de barras para visualização
st.subheader(f"📈 Gráfico de Quantidade por Kit - {selected_equipment}")
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(stocks["Kit"], stocks["Quantidade"], color='skyblue')
ax.set_title(f"Quantidade de Reagentes por Kit - {selected_equipment}")
ax.set_xlabel("Kit")
ax.set_ylabel("Quantidade")
plt.xticks(rotation=45)
st.pyplot(fig)

# Função para gerar o PDF com cores de fundo diferentes para cada kit
def generate_pdf(dataframe, equipment_name, fig):
    try:
        # Criar o PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt=f"Relatório de Reagentes - {equipment_name}", ln=True, align="C")
        
        # Definir cores diferentes para cada kit
        colors = {
            "P1 300": [255, 230, 230],  # Vermelho claro
            "P1 600": [230, 255, 230],  # Verde claro
            "P2 200": [230, 230, 255],  # Azul claro
            "P2 300": [255, 255, 230],  # Amarelo claro
            "P2 600": [255, 230, 255],  # Rosa claro
            "P3 200": [230, 255, 255],  # Ciano claro
            "P3 300": [255, 255, 255],  # Branco
            "P4 200": [240, 240, 240],  # Cinza claro
            "P4 300": [255, 240, 240],  # Vermelho rosado
            "Next500": [240, 255, 240], # Verde limão
            "SMRT Cell 8M": [200, 255, 255],  # Azul suave
            "Sequel Binding Kit": [255, 255, 200], # Amarelo suave
            "Sequencing Primer": [255, 220, 220], # Coral claro
            "Clean-up Beads": [220, 220, 255], # Lavanda
            "MagBeads": [200, 255, 200],  # Verde claro
            "DNA Prep Kit": [255, 255, 255],  # Branco
        }

        # Adicionar a tabela com cores de fundo
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(90, 10, "Kit", 1, 0, "C")
        pdf.cell(40, 10, "Quantidade", 1, 1, "C")
        
        pdf.set_font("Arial", size=12)
        for i in range(len(dataframe)):
            kit = dataframe.loc[i, "Kit"]
            quantidade = dataframe.loc[i, "Quantidade"]
            color = colors.get(kit, [255, 255, 255])  # Cor padrão se o kit não estiver no dicionário
            pdf.set_fill_color(*color)
            pdf.cell(90, 10, kit, 1, 0, "L", fill=True)
            pdf.cell(40, 10, str(quantidade), 1, 1, "C", fill=True)
        
        # Salvar gráfico em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            fig.savefig(temp_file, format="png")
            temp_file.close()  # Fecha o arquivo para garantir que o FPDF possa usá-lo
        
            # Adicionar imagem do gráfico ao PDF
            pdf.ln(10)
            pdf.image(temp_file.name, x=10, y=pdf.get_y() + 10, w=190)
        
        # Gerar o buffer de saída do PDF
        pdf_output = pdf.output(dest='S').encode('latin1')  # Gera o PDF no formato de bytes
        
        # Remover arquivo temporário
        os.remove(temp_file.name)
        
        return BytesIO(pdf_output)
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o PDF: {e}")
        return None

if st.button("Baixar PDF"):
    pdf_data = generate_pdf(stocks, selected_equipment, fig)
    if pdf_data:
        st.download_button(
            "📥 Clique para baixar o PDF", data=pdf_data, file_name=f"controle_reagentes_{selected_equipment}.pdf", mime="application/pdf"
        )

