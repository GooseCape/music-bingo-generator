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
base_styles = getSampleStyleSheet()


def build_styles(scale=1.0):
    """Build Paragraph styles, scaled up for larger board layouts (e.g. 2-per-page)."""
    song_style = ParagraphStyle(
        'SongStyle',
        parent=base_styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2 * scale,
        leading=10 * scale,
        alignment=1,                     # Center
        wordWrap='CJK',
        splitLongWords=False,
        hyphenationLang=None,
        spaceShrinkage=0.08,
    )

    number_style = ParagraphStyle(
        'NumberStyle',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16 * scale,
        leading=18 * scale,
        alignment=1,
    )

    free_style = ParagraphStyle(
        'FreeStyle',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11 * scale,
        leading=13 * scale,
        alignment=1,
        textColor=colors.darkblue
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=base_styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16 * scale,
        leading=18 * scale,
        alignment=1,
        textColor=colors.white,
    )

    return {
        "song": song_style,
        "number": number_style,
        "free": free_style,
        "header": header_style,
    }


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

layout_choice = st.sidebar.radio(
    "Boards per A4 page",
    ["4 per page (2x2, compact)", "2 per page (larger, easier to read)"],
    horizontal=False,
)
boards_per_page = 4 if layout_choice.startswith("4") else 2
rows_per_page = 2
cols_per_page = 2 if boards_per_page == 4 else 1

if is_music_mode:
    use_free_space = st.sidebar.checkbox("Include FREE center space", value=True)
else:
    use_free_space = st.sidebar.checkbox("Include FREE center space (standard)", value=True)
    show_bingo_header = st.sidebar.checkbox("Show B-I-N-G-O header row", value=True)

# ==================== CARD GENERATION ====================
def generate_music_bingo_card(songs_list, use_free=True, styles=None):
    styles = styles or build_styles(1.0)
    pool = songs_list[:]
    random.shuffle(pool)
    center_index = 12  # middle of 5x5 grid
    needed = 24 if use_free else 25
    if len(pool) < needed:
        raise ValueError(
            f"Not enough songs to fill a board: need at least {needed}, "
            f"but only {len(pool)} were provided."
        )
    items = pool[:needed]
    card = []
    idx = 0
    for i in range(5):
        row = []
        for j in range(5):
            flat_pos = i * 5 + j
            if use_free and flat_pos == center_index:
                row.append(Paragraph("<b>FREE</b>", styles["free"]))
            else:
                row.append(Paragraph(items[idx], styles["song"]))
                idx += 1
        card.append(row)
    return card


def generate_number_bingo_card(use_free=True, styles=None):
    """Generates a standard 75-ball bingo card: 5 unique numbers per B-I-N-G-O column."""
    styles = styles or build_styles(1.0)
    columns = {}
    for letter in BINGO_LETTERS:
        low, high = BINGO_RANGES[letter]
        columns[letter] = random.sample(range(low, high + 1), 5)

    card = []
    for row_idx in range(5):
        row = []
        for col_idx, letter in enumerate(BINGO_LETTERS):
            if use_free and row_idx == 2 and col_idx == 2:
                row.append(Paragraph("<b>FREE</b>", styles["free"]))
            else:
                value = columns[letter][row_idx]
                row.append(Paragraph(str(value), styles["number"]))
        card.append(row)
    return card


# ==================== PDF GENERATION ====================
def generate_bingo_pdf(
    num_cards,
    bingo_title,
    is_music,
    songs_list=None,
    use_free=True,
    show_header=True,
    rows_per_page=2,
    cols_per_page=2,
):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    side_margin = 20 * mm
    col_gap = 12 * mm
    top_margin = 25 * mm
    bottom_margin = 25 * mm
    row_gap = 15 * mm

    card_width = (width - 2 * side_margin - (cols_per_page - 1) * col_gap) / cols_per_page
    card_height = (height - top_margin - bottom_margin - (rows_per_page - 1) * row_gap) / rows_per_page

    # Boards get noticeably bigger with fewer per page, so scale text up to match.
    # 1 column per page (2-per-page layout) -> wider cards -> bigger font.
    font_scale = 1.4 if cols_per_page == 1 else 1.0
    card_styles = build_styles(font_scale)
    title_font_size = 14 * font_scale
    label_font_size = 11 * font_scale

    cards_generated = 0
    while cards_generated < num_cards:
        for r in range(rows_per_page):
            for col in range(cols_per_page):
                if cards_generated >= num_cards:
                    break
                x = side_margin + col * (card_width + col_gap)
                y = height - top_margin - (r + 1) * (card_height + row_gap) + row_gap

                if is_music:
                    card_data = generate_music_bingo_card(songs_list, use_free=use_free, styles=card_styles)
                else:
                    card_data = generate_number_bingo_card(use_free=use_free, styles=card_styles)

                c.setFont("Helvetica-Bold", title_font_size)
                c.drawCentredString(x + card_width / 2, y + card_height - 2 * mm, bingo_title)
                c.setFont("Helvetica", label_font_size)
                c.drawCentredString(x + card_width / 2, y - 6 * mm, f"Card #{cards_generated + 1}")

                table_rows = card_data
                row_heights = [card_height / 5.55] * 5

                if (not is_music) and show_header:
                    header_row = [Paragraph(f"<b>{letter}</b>", card_styles["header"]) for letter in BINGO_LETTERS]
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
required_songs = (24 if use_free_space else 25) if is_music_mode else 0
ready_to_generate = (not is_music_mode) or (is_music_mode and len(songs) >= required_songs)

if is_music_mode and len(songs) < required_songs:
    space_note = "24 (with a FREE center space)" if use_free_space else "25 (no FREE space)"
    st.info(f"Please add at least {space_note} songs — a 5x5 board needs that many to fill every cell.")

if ready_to_generate:
    if st.button("🚀 Generate Printable PDF", type="primary", use_container_width=True):
        with st.spinner("Generating cards..."):
            try:
                pdf_bytes = generate_bingo_pdf(
                    num_cards,
                    bingo_title,
                    is_music_mode,
                    songs_list=songs if is_music_mode else None,
                    use_free=use_free_space,
                    show_header=show_bingo_header if not is_music_mode else False,
                    rows_per_page=rows_per_page,
                    cols_per_page=cols_per_page,
                )
            except ValueError as e:
                st.error(f"⚠️ {e}")
                pdf_bytes = None
        if pdf_bytes:
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
