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

# ====================== CUSTOM TITLE ======================
st.subheader("Bingo Event Details")
bingo_title = st.text_input(
    "Enter Bingo Title (appears on every card)", 
    value="Battledress 1 May Bingo",
    placeholder="e.g. 80s Night Bingo - May 2026"
)

# ====================== SETTINGS ======================
st.sidebar.header("Settings")
num_cards = st.sidebar.slider("Number of boards to generate", 
                              min_value=50, max_value=100, 
                              value=75, step=5)

uploaded_file = st.file_uploader("Upload Excel file with song titles", 
                                 type=["xlsx", "xls"])

# Improved styles
styles = getSampleStyleSheet()

song_style = ParagraphStyle(
    'SongStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9.5,
    leading=11,
    alignment=1,        # Center
    wordWrap='CJK',
)

free_style = ParagraphStyle(
    'FreeStyle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=13,
    leading=15,
    alignment=1,        # Center
    textColor=colors.darkblue,
    backColor=colors.lightgrey
)

def generate_bingo_card(songs: list) -> list:
    """Generate one 5x5 bingo card"""
    pool = songs[:]
    random.shuffle(pool)
    items = pool[:24]
    
    card = []
    idx = 0
    for i in range(5):
        row = []
        for j in range(5):
            if i == 2 and j == 2:
                # Clean and bold FREE space (no problematic emojis)
                row.append(Paragraph("<b>FREE</b><br/>SPACE", free_style))
            else:
                row.append(Paragraph(items[idx], song_style))
                idx += 1
        card.append(row)
    return card


def generate_bingo_pdf(songs: list, num_cards: int, bingo_title: str) -> bytes:
    """Generate printable A4 PDF"""
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

                card_data = generate_bingo_card(songs)

                # Main Title
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(x + card_width/2, y + card_height - 8*mm, bingo_title)

                # Card Number
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
                t.drawOn(c, x, y + 4*mm)

                cards_generated += 1

            if cards_generated >= num_cards:
                break
        if cards_generated < num_cards:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ====================== MAIN LOGIC ======================
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ Excel loaded — {len(df)} rows")

        song_column = st.selectbox("Select column with song titles", 
                                   options=df.columns.tolist())

        songs = df[song_column].dropna().astype(str).str.strip().tolist()

        if len(songs) < 25:
            st.error("❌ Please use at least 25 songs.")
        else:
            st.info(f"🎯 **{len(songs)} songs** loaded")

            if st.button("🚀 Generate Printable PDF", type="primary", use_container_width=True):
                with st.spinner(f"Generating {num_cards} bingo cards..."):
                    pdf_bytes = generate_bingo_pdf(songs, num_cards, bingo_title)

                st.success(f"✅ {num_cards} Music Bingo cards generated!")
                
                st.download_button(
                    label="📥 Download A4 Printable PDF",
                    data=pdf_bytes,
                    file_name=f"music_bingo_{num_cards}_cards.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"Error reading Excel: {e}")

# Sample Preview
if 'songs' in locals() and songs and st.checkbox("Show sample bingo card preview"):
    st.subheader("Sample Card Preview")
    sample = generate_bingo_card(songs)
    simple_sample = [[p.text if hasattr(p, 'text') else str(p) for p in row] for row in sample]
    st.table(simple_sample)