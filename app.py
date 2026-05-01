import streamlit as st
import pandas as pd
import random
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

st.set_page_config(page_title="Music Bingo Card Generator", layout="centered")

st.title("🎵 Music Bingo Card Generator")

# ====================== BINGO TITLE ======================
st.subheader("Bingo Event Details")
bingo_title = st.text_input(
    "Enter Bingo Title", 
    value="Battledress 1 May Bingo",
    placeholder="e.g. 80s Night Bingo - May 2026"
)

# ====================== SONG INPUT METHOD ======================
st.subheader("Add Your Songs")
input_method = st.radio(
    "How do you want to add songs?",
    options=["Upload Excel File", "Paste Songs Manually"],
    horizontal=True
)

songs = []

if input_method == "Upload Excel File":
    uploaded_file = st.file_uploader("Upload Excel file with song titles", 
                                     type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            song_column = st.selectbox("Select column with song titles", 
                                       options=df.columns.tolist())
            songs = df[song_column].dropna().astype(str).str.strip().tolist()
            st.success(f"✅ Loaded {len(songs)} songs from Excel")
        except Exception as e:
            st.error(f"Error reading Excel: {e}")

else:  # Paste Songs Manually
    st.info("Paste one song title per line below")
    manual_input = st.text_area(
        "Paste your song titles here (one per line)",
        height=300,
        placeholder="Billie Jean\nThriller\nTake On Me\n..."
    )
    
    if manual_input:
        songs = [line.strip() for line in manual_input.splitlines() if line.strip()]
        if songs:
            st.success(f"✅ Loaded {len(songs)} songs manually")

# ====================== SETTINGS ======================
st.sidebar.header("Settings")
num_cards = st.sidebar.slider("Number of boards to generate", 
                              min_value=50, max_value=100, 
                              value=75, step=5)

# ====================== STYLES ======================
styles = getSampleStyleSheet()

song_style = ParagraphStyle(
    'SongStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9.5,
    leading=11,
    alignment=1,
    wordWrap='CJK',
)

free_style = ParagraphStyle(
    'FreeStyle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=11,
    leading=13,
    alignment=1,
    textColor=colors.darkblue,
)

def generate_bingo_card(songs_list: list) -> list:
    pool = songs_list[:]
    random.shuffle(pool)
    items = pool[:24]
    
    card = []
    idx = 0
    for i in range(5):
        row = []
        for j in range(5):
            if i == 2 and j == 2:
                row.append(Paragraph("<b>FREE</b>", free_style))
            else:
                row.append(Paragraph(items[idx], song_style))
                idx += 1
        card.append(row)
    return card


def generate_bingo_pdf(songs_list: list, num_cards: int, bingo_title: str) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    card_width = (width - 40 * mm) / 2
    card_height = (height - 65 * mm) / 2
    margin_x = 20 * mm
    margin_y = 25 * mm

    cards_generated = 0

    while cards_generated < num_cards:
        for row_idx in range(2):
            for col_idx in range(2):
                if cards_generated >= num_cards:
                    break

                x = margin_x + col_idx * (card_width + 12 * mm)
                y = height - margin_y - (row_idx + 1) * (card_height + 15 * mm)

                card_data = generate_bingo_card(songs_list)

                # Title
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(x + card_width/2, y + card_height - 8*mm, bingo_title)

                c.setFont("Helvetica", 11)
                c.drawCentredString(x + card_width/2, y + card_height - 18*mm, 
                                  f"Card #{cards_generated + 1}")

                # Table
                t = Table(card_data, 
                         colWidths=[card_width/5.05]*5, 
                         rowHeights=[card_height/5.75]*5)

                style = TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BACKGROUND', (2, 2), (2, 2), colors.lightgrey),
                ])
                t.setStyle(style)

                t.wrapOn(c, card_width, card_height)
                t.drawOn(c, x, y + 5*mm)

                cards_generated += 1

            if cards_generated >= num_cards:
                break
        if cards_generated < num_cards:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ====================== GENERATE BUTTON ======================
if songs and len(songs) >= 20:
    if st.button("🚀 Generate Printable PDF", type="primary", use_container_width=True):
        with st.spinner(f"Generating {num_cards} bingo cards..."):
            pdf_bytes = generate_bingo_pdf(songs, num_cards, bingo_title)

        st.success(f"✅ Successfully generated {num_cards} Music Bingo cards!")
        
        st.download_button(
            label="📥 Download A4 Printable PDF",
            data=pdf_bytes,
            file_name=f"music_bingo_{num_cards}_cards.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        st.caption("Print at 100% scale. Each A4 page contains 4 cards.")

elif songs:
    st.warning("Please add at least 20 songs for good variety.")
else:
    st.info("Please upload an Excel file or paste songs manually to continue.")

# Sample Preview
if songs and st.checkbox("Show sample bingo card preview"):
    st.subheader("Sample Card Preview")
    sample = generate_bingo_card(songs)
    simple_sample = [[p.text if hasattr(p, 'text') else str(p) for p in row] for row in sample]
    st.table(simple_sample)
