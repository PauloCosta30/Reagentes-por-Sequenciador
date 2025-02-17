import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
import tempfile

# Lista inicial de reagentes para cada equipamento
reagents_dict = {
    "Illumina": ["P1 300", "P1 600", "P2 200", "P2 300", "P2 600", "P3 200", "P3 300", "P4 200", "P4 300"],
    "PacBio": ["SMRT Cell 8M", "Sequel II Binding Kit 3.2", "Sequencing II Sequencing Kit 2.0", "Smrtbell Prep Kit 3.0"]
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

# Função para carregar o histórico de baixas
def load_usage_history(equipment):
    history_file = f"{equipment}_usage_history.csv"
    if os.path.exists(history_file):
        history_df = pd.read_csv(history_file)
        if "Kit" not in history_df.columns or "Frequencia" not in history_df.columns:
            history_df = pd.DataFrame({"Kit": [], "Frequencia": []})
    else:
        history_df = pd.DataFrame({"Kit": [], "Frequencia": []})
    return history_df

# Função para salvar o histórico de baixas
def save_usage_history(equipment, history_dataframe):
    history_file = f"{equipment}_usage_history.csv"
    history_dataframe.to_csv(history_file, index=False)

st.title("📊 Controle de Reagentes por Equipamento")

# Seleção do equipamento
selected_equipment = st.selectbox("Selecione o Equipamento", ["Illumina", "PacBio"])

# Carregar os dados do equipamento selecionado
stocks = load_data(selected_equipment)
usage_history = load_usage_history(selected_equipment)

# Mostrar o estoque atual
st.subheader(f"📦 Estoque Atual - {selected_equipment}")
st.dataframe(stocks, use_container_width=True, height=300)

# Formulário para dar baixa nos reagentes
st.subheader(f"➖ Dar Baixa em Reagentes - {selected_equipment}")
selected_kit = st.selectbox("Selecione o kit", stocks["Kit"].tolist())
amount_to_deduct = st.number_input("Quantidade a dar baixa", min_value=1, step=1)

if st.button("Dar Baixa"):
    try:
        index = stocks[stocks["Kit"] == selected_kit].index[0]
        if stocks.loc[index, "Quantidade"] >= amount_to_deduct:
            stocks.loc[index, "Quantidade"] -= amount_to_deduct

            # Atualizar o histórico de baixas
            if selected_kit in usage_history["Kit"].values:
                usage_history.loc[usage_history["Kit"] == selected_kit, "Frequencia"] += 1
            else:
                new_row = pd.DataFrame({"Kit": [selected_kit], "Frequencia": [1]})
                usage_history = pd.concat([usage_history, new_row], ignore_index=True)
            
            # Salvar as alterações
            save_data(selected_equipment, stocks)
            save_usage_history(selected_equipment, usage_history)

            st.success(f"{amount_to_deduct} unidades removidas do kit {selected_kit}.")
        else:
            st.error(f"Quantidade insuficiente no kit {selected_kit}.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao dar baixa: {e}")

# Mostrar o total de reagentes
st.subheader("📊 Total de Reagentes")
total_reagents = stocks["Quantidade"].sum()
st.metric(label=f"Quantidade total de reagentes para {selected_equipment}", value=total_reagents)

# Gráfico de barras para frequência de uso dos kits
st.subheader(f"📊 Gráfico de Frequência por Kit - {selected_equipment}")
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(usage_history["Kit"], usage_history["Frequencia"], color='cornflowerblue', edgecolor='black')
ax.set_title(f"Frequência de Uso dos Kits - {selected_equipment}")
ax.set_xlabel("Kit")
ax.set_ylabel("Frequência")
plt.xticks(rotation=45)
st.pyplot(fig)

# Função para gerar o PDF com cores refinadas
def generate_pdf(dataframe, equipment_name, fig):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt=f"Relatório de Reagentes - {equipment_name}", ln=True, align="C")
        
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(90, 10, "Kit", 1, 0, "C")
        pdf.cell(40, 10, "Quantidade", 1, 1, "C")
        
        pdf.set_font("Arial", size=12)
        colors = [(255, 193, 193), (255, 215, 0), (193, 255, 193), (135, 206, 250), (255, 160, 122), (147, 112, 219), (192, 192, 192)]
        
        for i in range(len(dataframe)):
            kit = dataframe.loc[i, "Kit"]
            quantidade = dataframe.loc[i, "Quantidade"]
            color = colors[i % len(colors)]
            
            pdf.set_fill_color(*color)
            pdf.cell(90, 10, kit, 1, 0, "L", fill=True)
            pdf.cell(40, 10, str(quantidade), 1, 1, "C", fill=True)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            fig.savefig(temp_file, format="png")
            temp_file.close()
            pdf.add_page()
            pdf.image(temp_file.name, x=10, y=20, w=190)
        
        pdf_output = pdf.output(dest='S').encode('latin1')
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
