import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt

# Lista inicial de reagentes para cada equipamento
reagents_dict = {
    "Illumina": ["P1 300", "P1 600", "P2 200", "P2 300", "P2 600", "P3 200", "P3 300", "P4 200", "P4 300", "Next500"],
    "PacBio": ["SMRT Cell 8M", "Sequel Binding Kit", "Sequencing Primer", "Clean-up Beads", "MagBeads", "DNA Prep Kit"]
}

# Inicializando o estado para cada equipamento
if "stocks" not in st.session_state:
    st.session_state.stocks = {
        "Illumina": pd.DataFrame({"Kit": reagents_dict["Illumina"], "Quantidade": [0] * len(reagents_dict["Illumina"])}),
        "PacBio": pd.DataFrame({"Kit": reagents_dict["PacBio"], "Quantidade": [0] * len(reagents_dict["PacBio"])})
    }

st.title("Controle de Reagentes por Sequenciador")

# Seleção do equipamento
selected_equipment = st.selectbox("Selecione o Equipamento", ["Illumina", "PacBio"])

# Mostrar o estoque atual para o equipamento selecionado
st.subheader(f"Estoque Atual - {selected_equipment}")
st.dataframe(st.session_state.stocks[selected_equipment])

# Formulário para dar baixa nos reagentes
st.subheader(f"Dar Baixa em Reagentes - {selected_equipment}")
selected_kit = st.selectbox("Selecione o kit", st.session_state.stocks[selected_equipment]["Kit"].tolist())
amount_to_deduct = st.number_input("Quantidade a dar baixa", min_value=1, step=1)

if st.button("Dar Baixa"):
    index = st.session_state.stocks[selected_equipment][st.session_state.stocks[selected_equipment]["Kit"] == selected_kit].index[0]
    if st.session_state.stocks[selected_equipment].loc[index, "Quantidade"] >= amount_to_deduct:
        st.session_state.stocks[selected_equipment].loc[index, "Quantidade"] -= amount_to_deduct
        st.success(f"{amount_to_deduct} unidades removidas do kit {selected_kit}.")
    else:
        st.error(f"Quantidade insuficiente no kit {selected_kit}.")

# Mostrar o total de reagentes para o equipamento selecionado
st.subheader("Total de Reagentes")
total_reagents = st.session_state.stocks[selected_equipment]["Quantidade"].sum()
st.write(f"Quantidade total de reagentes para {selected_equipment}: {total_reagents}")

# Permitir adicionar unidades manualmente
st.subheader(f"Adicionar Unidades - {selected_equipment}")
selected_kit_update = st.selectbox("Selecione o kit para adicionar unidades", st.session_state.stocks[selected_equipment]["Kit"].tolist(), key="update")
units_to_add = st.number_input("Quantidade a adicionar", min_value=1, step=1, key="add")

if st.button("Adicionar Unidades"):
    index_update = st.session_state.stocks[selected_equipment][st.session_state.stocks[selected_equipment]["Kit"] == selected_kit_update].index[0]
    st.session_state.stocks[selected_equipment].loc[index_update, "Quantidade"] += units_to_add
    st.success(f"{units_to_add} unidades adicionadas ao kit {selected_kit_update}.")

# Gráfico de barras para visualização
st.subheader(f"Gráfico de Quantidade por Kit - {selected_equipment}")
fig, ax = plt.subplots()
ax.bar(st.session_state.stocks[selected_equipment]["Kit"], st.session_state.stocks[selected_equipment]["Quantidade"], color='skyblue')
ax.set_title(f"Quantidade de Reagentes por Kit - {selected_equipment}")
ax.set_xlabel("Kit")
ax.set_ylabel("Quantidade")
plt.xticks(rotation=45)
st.pyplot(fig)

# Exportar tabela e gráfico para PDF
st.subheader("Exportar Relatório em PDF")

def generate_pdf(dataframe, equipment_name, fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(0, 0, 128)
    pdf.cell(200, 10, txt=f"Relatório de Reagentes - {equipment_name}", ln=True, align="C")
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(90, 10, "Kit", 1, 0, "C", True)
    pdf.cell(40, 10, "Quantidade", 1, 1, "C", True)
    
    pdf.set_font("Arial", size=12)
    colors = [(255, 230, 230), (230, 255, 230), (230, 230, 255), (255, 255, 200)]
    
    for i in range(len(dataframe)):
        kit = dataframe.loc[i, "Kit"]
        quantidade = dataframe.loc[i, "Quantidade"]
        color = colors[i % len(colors)]
        pdf.set_fill_color(*color)
        pdf.cell(90, 10, kit, 1, 0, "L", True)
        pdf.cell(40, 10, str(quantidade), 1, 1, "C", True)
    
    # Salvar o gráfico como imagem e inserir no PDF
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    pdf.image(img_buffer, x=10, y=pdf.get_y() + 10, w=190)
    
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

if st.button("Baixar PDF"):
    pdf_data = generate_pdf(st.session_state.stocks[selected_equipment], selected_equipment, fig)
    st.download_button(
        "Clique para baixar o PDF", data=pdf_data, file_name=f"controle_reagentes_{selected_equipment}.pdf", mime="application/pdf"
    )

