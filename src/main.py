import os
import streamlit as st
import youtube_utils
import gemini_utils
from fpdf import FPDF
import tempfile

def load_css(file_name):
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Arquivo CSS '{file_name}' não encontrado")


def create_pdf(content, title="Transcript"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, txt=line)
        pdf.ln(2)
    return pdf

def save_text(content, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

# Configuração da página
st.set_page_config(page_title="Hashira da Transcrição", page_icon="🌊")
load_css("style.css")

# Sidebar
try:
    st.sidebar.image("./tomioka.jpg", width=150)
except FileNotFoundError:
    st.sidebar.warning("Imagem 'tomioka.jpg' não encontrada")

st.sidebar.markdown("## Menu")
idioma_escolhido = st.sidebar.radio("Idioma da transcrição:", ("Português", "Inglês"), index=0)
gerar_resumo = st.sidebar.button("Gerar Resumo")
st.sidebar.markdown("### Exportar")

export_options = {
    "resumo_txt": st.sidebar.checkbox("Resumo (TXT)"),
    "resumo_pdf": st.sidebar.checkbox("Resumo (PDF)"),
    "transcricao_txt": st.sidebar.checkbox("Transcrição (TXT)"),
    "transcricao_pdf": st.sidebar.checkbox("Transcrição (PDF)"),
    "ambas_transcricoes": st.sidebar.checkbox("Ambas as Transcrições (TXT)")
}

# Corpo
st.markdown("<div class='header'><div class='header-title'><h1>Hashira da Transcrição</h1><h3>Transcreva vídeos com a calma de Tomioka</h3></div></div>", unsafe_allow_html=True)

def main():
    st.subheader("Transcrição de Vídeos do YouTube com Resumo por IA")
    video_url = st.text_input("URL do vídeo:", "https://youtu.be/aKq8bkY5eTU?si=KxKMEIFG8i-12Dnj")

    if not video_url:
        st.warning("Por favor, insira uma URL válida.")
        return

    try:
        clean_url = youtube_utils.clean_youtube_url(video_url)
        video_id = youtube_utils.extract_video_id(clean_url)
        video_title = youtube_utils.get_video_title(clean_url)
        transcript_data = youtube_utils.get_transcript(video_id)

        if not transcript_data:
            st.error("Não foi possível obter a transcrição.")
            return

        if video_title:
            st.markdown(f"<h3>🎥 Título do Vídeo: {video_title}</h3>", unsafe_allow_html=True)

        transcript_to_use = (
            transcript_data.get('portuguese') if idioma_escolhido == "Português"
            else transcript_data.get('english')
        )

        if transcript_to_use:
            st.markdown(f"<h4>📝 Transcrição em {idioma_escolhido}:</h4>", unsafe_allow_html=True)
            st.markdown("<div class='transcript-box'>", unsafe_allow_html=True)
            st.write(transcript_to_use)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning(f"Transcrição em {idioma_escolhido} não disponível.")
            return

        summary = None
        if gerar_resumo:
            with st.spinner("Gerando resumo com Gemini..."):
                gemini_utils.configure_gemini()
                summary = gemini_utils.generate_summary(transcript_to_use)

            if summary:
                st.markdown("<h4>📄 Resumo:</h4>", unsafe_allow_html=True)
                st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
                st.write(summary)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.error("Erro ao gerar resumo.")

        if any(export_options.values()):
            st.subheader("Exportações")

            if export_options["resumo_txt"] and summary:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    save_text(summary, tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.download_button("Baixar Resumo (TXT)", data=f, file_name=f"resumo_{video_id}.txt", mime="text/plain")
                os.unlink(tmp.name)

            if export_options["resumo_pdf"] and summary:
                pdf = create_pdf(summary, f"Resumo: {video_title}")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.download_button("Baixar Resumo (PDF)", data=f, file_name=f"resumo_{video_id}.pdf", mime="application/pdf")
                os.unlink(tmp.name)

            if export_options["transcricao_txt"] and transcript_to_use:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    save_text(transcript_to_use, tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.download_button("Baixar Transcrição (TXT)", data=f, file_name=f"transcricao_{video_id}.txt", mime="text/plain")
                os.unlink(tmp.name)

            if export_options["transcricao_pdf"] and transcript_to_use:
                pdf = create_pdf(transcript_to_use, f"Transcrição ({idioma_escolhido}): {video_title}")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.download_button("Baixar Transcrição (PDF)", data=f, file_name=f"transcricao_{video_id}.pdf", mime="application/pdf")
                os.unlink(tmp.name)

            if export_options["ambas_transcricoes"] and transcript_data.get('english') and transcript_data.get('portuguese'):
                content = f"=== INGLÊS ===\n{transcript_data['english']}\n\n=== PORTUGUÊS ===\n{transcript_data['portuguese']}"
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    save_text(content, tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.download_button("Baixar Ambas as Transcrições", data=f, file_name=f"transcricoes_{video_id}.txt", mime="text/plain")
                os.unlink(tmp.name)

    except Exception as e:
        st.error(f"Erro: {str(e)}")

if __name__ == "__main__":
    main()
