import streamlit as st
import numpy as np
import cv2
from PIL import Image
import analyze_image
import solver

# Set page config for better mobile experience
st.set_page_config(
    page_title="Block Blast Solver",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better mobile/responsive UI
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-weight: bold;
    }
    .block-preview {
        border: 2px solid #ccc;
        border-radius: 5px;
        padding: 5px;
        margin: 5px;
        text-align: center;
    }
    .step-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def draw_solution_step(base_img, board_info, block, r, c, step_idx):
    """
    Draws the block at the specified position on the board.
    """
    img = base_img.copy()

    bx = board_info['x']
    by = board_info['y']
    cw = board_info['cell_w']
    ch = board_info['cell_h']

    # Color: Green for the block placement
    color = (0, 255, 0)
    border_color = (0, 100, 0)

    # Overlay logic
    overlay = img.copy()

    block_h = len(block)
    block_w = len(block[0])

    for br in range(block_h):
        for bc in range(block_w):
            if block[br][bc] == 1:
                # Calculate board cell coordinates
                target_r = r + br
                target_c = c + bc

                # Pixel coordinates
                px = bx + target_c * cw
                py = by + target_r * ch

                # Draw filled rectangle
                padding = 4
                cv2.rectangle(overlay, (px + padding, py + padding), (px + cw - padding, py + ch - padding), color, -1)

                # Draw border
                cv2.rectangle(img, (px + padding, py + padding), (px + cw - padding, py + ch - padding), border_color, 2)

    # Blend
    alpha = 0.5
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    # Add step number text on the board center (optional, might obscure vision)
    # cx = bx + (c + block_w/2) * cw
    # cy = by + (r + block_h/2) * ch
    # cv2.putText(img, str(step_idx), (int(cx), int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)

    return img

def draw_block_preview(block, cell_size=30):
    """Creates a small image preview of a block."""
    rows = len(block)
    cols = len(block[0])
    h = rows * cell_size
    w = cols * cell_size
    img = np.ones((h, w, 3), dtype=np.uint8) * 240 # Light gray background

    for r in range(rows):
        for c in range(cols):
            if block[r][c] == 1:
                cv2.rectangle(img,
                            (c * cell_size + 2, r * cell_size + 2),
                            ((c+1) * cell_size - 2, (r+1) * cell_size - 2),
                            (255, 165, 0), -1) # Orange color for block
    return img

# Initialize session state
if 'step_index' not in st.session_state:
    st.session_state.step_index = 0
if 'solution' not in st.session_state:
    st.session_state.solution = None
if 'processed_image' not in st.session_state:
    st.session_state.processed_image = None
if 'board_info' not in st.session_state:
    st.session_state.board_info = None
if 'blocks' not in st.session_state:
    st.session_state.blocks = None

st.title("🧩 Block Blast Solver")

# File Uploader
uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Reset state if new file is uploaded
    # Simple check: if we have a file, and it's different?
    # For now, just rely on the user to not be confused.
    # Or reset if solution exists but no file... standard Streamlit re-run handles this partially.

    # Convert uploaded file to opencv image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    original_img = cv2.imdecode(file_bytes, 1)

    # Main container
    main_col1, main_col2 = st.columns([1, 1])

    with main_col1:
        st.subheader("Original Image")
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        st.image(img_rgb, use_container_width=True)

    with main_col2:
        st.subheader("Actions")
        if st.button("🚀 Solve Puzzle", type="primary"):
             with st.spinner("Analyzing & Solving..."):
                try:
                    # Reset
                    st.session_state.step_index = 0
                    st.session_state.solution = None

                    # Analyze
                    board, blocks, board_info = analyze_image.get_game_state(image_array=original_img)

                    if board is None:
                        st.error("❌ Could not detect board. Make sure the screenshot is clear.")
                    else:
                        st.session_state.board_info = board_info
                        st.session_state.blocks = blocks
                        st.session_state.processed_image = original_img

                        # Solve
                        s = solver.BlockBlastSolver()
                        solution = s.solve(board, blocks)

                        if not solution:
                            st.warning("⚠️ No valid moves found for this state.")
                            st.session_state.solution = []
                        else:
                            st.session_state.solution = solution
                            st.success(f"✅ Found solution with {len(solution)} steps!")

                except Exception as e:
                    st.error(f"Error: {e}")

    # --- Solution Navigation ---
    if st.session_state.solution:
        st.divider()
        st.header("🎯 Solution Walkthrough")

        solution = st.session_state.solution
        total_steps = len(solution)

        # Navigation Controls
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅️ Previous") and st.session_state.step_index > 0:
                st.session_state.step_index -= 1

        with c2:
            st.markdown(f"<div class='step-info'>Step {st.session_state.step_index + 1} / {total_steps}</div>", unsafe_allow_html=True)

        with c3:
            if st.button("Next ➡️") and st.session_state.step_index < total_steps - 1:
                st.session_state.step_index += 1

        # Display Current Step
        current_step = solution[st.session_state.step_index]
        block_idx = current_step['block_idx']
        r, c = current_step['r'], current_step['c']
        score = current_step['score_gain']

        # Prepare content columns
        step_col1, step_col2 = st.columns([1, 2])

        with step_col1:
            st.info(f"**Action:** Place **Block {block_idx}** at (Row {r}, Col {c})")
            st.metric("Score Gain", score)

            # Show Block Preview
            current_block = st.session_state.blocks[block_idx]
            block_preview_img = draw_block_preview(current_block)
            st.image(block_preview_img, caption=f"Block {block_idx}", width=150)

        with step_col2:
            # Generate Visualization
            viz_img = draw_solution_step(
                st.session_state.processed_image,
                st.session_state.board_info,
                st.session_state.blocks[block_idx],
                r, c,
                st.session_state.step_index + 1
            )
            viz_img_rgb = cv2.cvtColor(viz_img, cv2.COLOR_BGR2RGB)
            st.image(viz_img_rgb, caption=f"Visualization for Step {st.session_state.step_index + 1}", use_container_width=True)
