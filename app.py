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

st.set_page_config(page_title="Bingo Card Generator", layout="centered")

st.title("🎉 Bingo Card Generator")
st.caption("Create printable PDF cards for classic Number Bingo or Music Bingo.")

# ==================== MODE SELECTION ====================
mode = st.radio(
    "What type of bingo do you want to create?",
    ["🔢 Number Bingo (classic 75-ball)", "🎵 Music Bingo (songs)"],
    horizontal=False,
)

is_music_mode = mode.startswith("🎵")

bingo_title = st.text_input(
    "Enter Bingo Title",
    value="Music Bingo" if is_music_mode else "Number Bingo Night",
)

# ==================== STYLES ====================
styles = getSampleStyleSheet()

song_style = ParagraphStyle(
    'SongStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8.2,                    # Smaller but readable
    leading=10,
    alignment=1,                     # Center
    wordWrap='CJK',
    splitLongWords=False,
    hyphenationLang=None,
    spaceShrinkage=0.08,
)

number_style = ParagraphStyle(
    'NumberStyle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=16,
    leading=18,
    alignment=1,
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

header_style = ParagraphStyle(
    'HeaderStyle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=16,
    leading=18,
    alignment=1,
    textColor=colors.white,
)

# Standard 75-ball bingo column ranges
BINGO_LETTERS = ["B", "I", "N", "G", "O"]
BINGO_RANGES = {
    "B": (1, 15),
    "I": (16, 30),
    "N": (31, 45),
    "G": (46, 60),
    "O": (61, 75),
}

songs = []

# ==================== SONG INPUT (Music Bingo only) ====================
if is_music_mode:
    st.subheader("Add Your Songs")
    input_method = st.radio(
        "How do you want to add songs?",
        ["Upload Excel File", "Paste Songs Manually"],
        horizontal=True,
    )

    if input_method == "Upload Excel File":
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            col = st.selectbox("Song column", df.columns.tolist())
            songs = df[col].dropna().astype(str).str.strip().tolist()
            st.success(f"Loaded {len(songs)} songs")
    else:
        manual = st.text_area(
            "Paste songs (one per line)",
            height=300,
            placeholder="True Colors\nWest End Girls\n...",
        )
        if manual:
            songs = [line.strip() for line in manual.splitlines() if line.strip()]
            st.success(f"Loaded {len(songs)} songs")

# ==================== SIDEBAR SETTINGS ====================
st.sidebar.header("Settings")
num_cards = st.sidebar.slider("Number of boards", 50, 100, 75, 5)

if is_music_mode:
    use_free_space = st.sidebar.checkbox("Include FREE center space", value=True)
else:
    use_free_space = st.sidebar.checkbox("Include FREE center space (standard)", value=True)
    show_bingo_header = st.sidebar.checkbox("Show B-I-N-G-O header row", value=True)

# ==================== CARD GENERATION ====================
def generate_music_bingo_card(songs_list, use_free=True):
    pool = songs_list[:]
    random.shuffle(pool)
    center_index = 12  # middle of 5x5 grid
    needed = 24 if use_free else 25
    items = pool[:needed]
    card = []
    idx = 0
    for i in range(5):
        row = []
        for j in range(5):
            flat_pos = i * 5 + j
            if use_free and flat_pos == center_index:
                row.append(Paragraph("<b>FREE</b>", free_style))
            else:
                row.append(Paragraph(items[idx], song_style))
                idx += 1
        card.append(row)
    return card


def generate_number_bingo_card(use_free=True):
    """Generates a standard 75-ball bingo card: 5 unique numbers per B-I-N-G-O column."""
    columns = {}
    for letter in BINGO_LETTERS:
        low, high = BINGO_RANGES[letter]
        columns[letter] = random.sample(range(low, high + 1), 5)

    card = []
    for row_idx in range(5):
        row = []
        for col_idx, letter in enumerate(BINGO_LETTERS):
            if use_free and row_idx == 2 and col_idx == 2:
                row.append(Paragraph("<b>FREE</b>", free_style))
            else:
                value = columns[letter][row_idx]
                row.append(Paragraph(str(value), number_style))
        card.append(row)
    return card


# ==================== PDF GENERATION ====================
def generate_bingo_pdf(num_cards, bingo_title, is_music, songs_list=None, use_free=True, show_header=True):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    card_width = (width - 40 * mm) / 2
    card_height = (height - 68 * mm) / 2

    cards_generated = 0
    while cards_generated < num_cards:
        for r in range(2):
            for col in range(2):
                if cards_generated >= num_cards:
                    break
                x = 20 * mm + col * (card_width + 12 * mm)
                y = height - 25 * mm - (r + 1) * (card_height + 15 * mm)

                if is_music:
                    card_data = generate_music_bingo_card(songs_list, use_free=use_free)
                else:
                    card_data = generate_number_bingo_card(use_free=use_free)

                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(x + card_width / 2, y + card_height - 2 * mm, bingo_title)
                c.setFont("Helvetica", 11)
                c.drawCentredString(x + card_width / 2, y + card_height - 120 * mm, f"Card #{cards_generated + 1}")

                table_rows = card_data
                row_heights = [card_height / 5.55] * 5

                if (not is_music) and show_header:
                    header_row = [Paragraph(f"<b>{letter}</b>", header_style) for letter in BINGO_LETTERS]
                    table_rows = [header_row] + card_data
                    row_heights = [card_height / 8] + [card_height / 5.55] * 5

                t = Table(
                    table_rows,
                    colWidths=[card_width / 5.05] * 5,
                    rowHeights=row_heights,
                )

                style_commands = [
                    ('GRID', (0, 0 if not ((not is_music) and show_header) else 1), (-1, -1), 1.5, colors.black),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]

                if (not is_music) and show_header:
                    style_commands.append(('BACKGROUND', (0, 0), (-1, 0), colors.darkblue))
                    if use_free:
                        style_commands.append(('BACKGROUND', (2, 3), (2, 3), colors.lightgrey))
                else:
                    if use_free:
                        style_commands.append(('BACKGROUND', (2, 2), (2, 2), colors.lightgrey))

                t.setStyle(TableStyle(style_commands))
                t.wrapOn(c, card_width, card_height)
                t.drawOn(c, x, y + 4 * mm)

                cards_generated += 1
            if cards_generated >= num_cards:
                break
        if cards_generated < num_cards:
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ==================== GENERATE BUTTON ====================
ready_to_generate = (not is_music_mode) or (is_music_mode and len(songs) >= 20)

if is_music_mode and len(songs) < 20:
    st.info("Please add at least 20 songs")

if ready_to_generate:
    if st.button("🚀 Generate Printable PDF", type="primary", use_container_width=True):
        with st.spinner("Generating cards..."):
            pdf_bytes = generate_bingo_pdf(
                num_cards,
                bingo_title,
                is_music_mode,
                songs_list=songs if is_music_mode else None,
                use_free=use_free_space,
                show_header=show_bingo_header if not is_music_mode else False,
            )
        st.success("✅ Done!")
        file_prefix = "music_bingo" if is_music_mode else "number_bingo"
        st.download_button(
            "📥 Download PDF",
            pdf_bytes,
            f"{file_prefix}_{num_cards}_cards.pdf",
            "application/pdf",
            use_container_width=True,
        )

# ==================== PREVIEW ====================
show_preview = False
if is_music_mode and songs:
    show_preview = st.checkbox("Show sample preview")
elif not is_music_mode:
    show_preview = st.checkbox("Show sample preview")

if show_preview:
    if is_music_mode:
        sample = generate_music_bingo_card(songs, use_free=use_free_space)
    else:
        sample = generate_number_bingo_card(use_free=use_free_space)
    simple = [[p.text.replace("<b>", "").replace("</b>", "") if hasattr(p, 'text') else str(p) for p in row] for row in sample]
    if not is_music_mode and show_bingo_header:
        simple = [BINGO_LETTERS] + simple
    st.table(simple)
