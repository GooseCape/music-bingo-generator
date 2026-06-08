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

bingo_title = st.text_input("Enter Bingo Title", value="Battledress 1 May Bingo")

# Song Input
st.subheader("Add Your Songs")
input_method = st.radio("How do you want to add songs?", 
                       ["Upload Excel File", "Paste Songs Manually"], horizontal=True)

songs = []

if input_method == "Upload Excel File":
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        col = st.selectbox("Song column", df.columns.tolist())
        songs = df[col].dropna().astype(str).str.strip().tolist()
        st.success(f"Loaded {len(songs)} songs")
else:
    manual = st.text_area("Paste songs (one per line)", height=300, 
                         placeholder="True Colors\nWest End Girls\n...")
    if manual:
        songs = [line.strip() for line in manual.splitlines() if line.strip()]
        st.success(f"Loaded {len(songs)} songs")

# Settings
st.sidebar.header("Settings")
num_cards = st.sidebar.slider("Number of boards", 50, 100, 75, 5)

# ==================== IMPROVED STYLE ====================
styles = getSampleStyleSheet()

song_style = ParagraphStyle(
    'SongStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8.5,           # Smaller font
    leading=10,
    alignment=1,            # Center
    wordWrap='CJK',
    hyphenationLang='en',
    splitLongWords=True,
    spaceShrinkage=0.1,     # Allow tighter spacing
    allowWidows=0,
    allowOrphans=0
)

free_style = ParagraphStyle(
    'FreeStyle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=11,
    leading=13,
    alignment=1,
    textColor=colors.darkblue
)

def generate_bingo_card(songs_list):
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

def generate_bingo_pdf(songs_list, num_cards, bingo_title):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    card_width = (width - 40 * mm) / 2
    card_height = (height - 65 * mm) / 2

    cards_generated = 0
    while cards_generated < num_cards:
        for r in range(2):
            for col in range(2):
                if cards_generated >= num_cards:
                    break
                x = 20*mm + col * (card_width + 12*mm)
                y = height - 25*mm - (r + 1) * (card_height + 15*mm)

                card_data = generate_bingo_card(songs_list)

                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(x + card_width/2, y + card_height - 8*mm, bingo_title)
                c.setFont("Helvetica", 11)
                c.drawCentredString(x + card_width/2, y + card_height - 18*mm, f"Card #{cards_generated + 1}")

                t = Table(card_data, 
                         colWidths=[card_width/5.1]*5, 
                         rowHeights=[card_height/5.6]*5)   # Tighter rows

                t.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 1.5, colors.black),
                    ('BACKGROUND', (0,0), (-1,-1), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BACKGROUND', (2,2), (2,2), colors.lightgrey),
                ]))
                t.wrapOn(c, card_width, card_height)
                t.drawOn(c, x, y + 4*mm)

                cards_generated += 1
            if cards_generated >= num_cards: break
        if cards_generated < num_cards:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# Generate Button
if len(songs) >= 20:
    if st.button("🚀 Generate Printable PDF", type="primary", use_container_width=True):
        with st.spinner("Generating cards..."):
            pdf_bytes = generate_bingo_pdf(songs, num_cards, bingo_title)
        st.success("Done!")
        st.download_button("📥 Download PDF", pdf_bytes, 
                          f"music_bingo_{num_cards}_cards.pdf", 
                          "application/pdf", use_container_width=True)
else:
    st.info("Add at least 20 songs")

# Preview
if songs and st.checkbox("Show sample preview"):
    sample = generate_bingo_card(songs)
    simple = [[p.text if hasattr(p,'text') else str(p) for p in row] for row in sample]
    st.table(simple)
