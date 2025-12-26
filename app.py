import streamlit as st
import numpy as np
import cv2
from PIL import Image
import analyze_image
import solver
import hashlib

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

def pad_block_to_5x5(block):
    """Pads a block matrix to 5x5 for easier editing in the UI."""
    target_size = 5
    h = len(block)
    w = len(block[0])

    padded = np.zeros((target_size, target_size), dtype=int)

    for r in range(min(h, target_size)):
        for c in range(min(w, target_size)):
            padded[r][c] = block[r][c]

    return padded.tolist()

def trim_block(block):
    """Trims empty rows and cols from a block matrix."""
    arr = np.array(block)
    if not np.any(arr):
        return [[0]] # Minimal empty block

    rows = np.any(arr, axis=1)
    cols = np.any(arr, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    return arr[rmin:rmax+1, cmin:cmax+1].tolist()

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
if 'board_grid' not in st.session_state:
    st.session_state.board_grid = None
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'current_file_hash' not in st.session_state:
    st.session_state.current_file_hash = None

st.title("🧩 Block Blast Solver")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    instant_solve = st.checkbox("⚡ Instant Solve Mode", value=False, help="Skip manual verification and solve immediately after upload.")

    st.divider()
    st.markdown("### 💡 Tips")
    st.markdown("- **Paste Image:** Click 'Browse files' then press `Ctrl+V` (on PC).")
    st.markdown("- **Mobile:** Use camera to capture the screen.")

# --- File Uploader ---
uploaded_file = st.file_uploader("Upload Screenshot", type=["png", "jpg", "jpeg"], help="You can paste images here!")

def perform_analysis(img):
    board, blocks, board_info = analyze_image.get_game_state(image_array=img)
    return board, blocks, board_info

def perform_solve(board, blocks, strategy):
    s = solver.BlockBlastSolver()
    strat = "score" if strategy == "Maximize Score" else "survival"
    return s.solve(board, blocks, strategy=strat)

if uploaded_file is not None:
    # Convert uploaded file to opencv image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    original_img = cv2.imdecode(file_bytes, 1)

    # Calculate hash to detect file change
    file_hash = hashlib.md5(file_bytes).hexdigest()

    if st.session_state.current_file_hash != file_hash:
        # New file detected! Reset state
        st.session_state.current_file_hash = file_hash
        st.session_state.processed_image = original_img
        st.session_state.analysis_done = False
        st.session_state.solution = None
        st.session_state.board_grid = None
        st.session_state.blocks = None
        st.session_state.step_index = 0

        # If we have a widget key state for editors, we might need to handle that,
        # but Streamlit usually resets widgets on rerun if key is dynamic or not in session state explicitly.
        # Rerun to clear old UI components
        st.rerun()

    col_img, col_actions = st.columns([1, 1])

    with col_img:
        st.subheader("Original Image")
        img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        st.image(img_rgb, use_container_width=True)

    with col_actions:
        st.subheader("Configuration")

        # Strategy Selector
        strategy = st.selectbox(
            "Select Strategy",
            ("Maximize Score", "Survival Mode (Clear Space)"),
            index=0
        )

        # Determine if we should auto-analyze/solve
        # Check if analysis is NOT done yet.
        should_run_instant = instant_solve and not st.session_state.analysis_done

        if st.button("🔍 Analyze Image", type="primary") or should_run_instant:
            with st.spinner("Analyzing board..."):
                try:
                    board, blocks, board_info = perform_analysis(original_img)

                    if board is None:
                        st.error("❌ Could not detect board.")
                    else:
                        st.session_state.board_info = board_info
                        st.session_state.blocks = blocks
                        st.session_state.board_grid = board
                        st.session_state.analysis_done = True
                        st.session_state.solution = None # Reset solution

                        if instant_solve:
                            # Immediate solve
                             with st.spinner("Solving instantly..."):
                                sol = perform_solve(board, blocks, strategy)
                                st.session_state.solution = sol if sol else []
                                if not sol:
                                    st.warning("⚠️ No valid moves found.")
                                else:
                                    st.success("✅ Solution Found!")
                                st.rerun()
                        else:
                            st.rerun() # Go to edit mode

                except Exception as e:
                    st.error(f"Error: {e}")
                    import traceback
                    traceback.print_exc()

    # --- Manual Edit Step ---
    if st.session_state.analysis_done:
        expander_title = "🛠️ Verify & Edit Board State"
        expanded_default = True

        # Collapse if instant solve worked
        if instant_solve and st.session_state.solution is not None:
            expanded_default = False

        with st.expander(expander_title, expanded=expanded_default):
            st.info("Correct the board or blocks below if detection failed.")

            # Board Editor
            col_board, col_blocks = st.columns([1, 1])

            with col_board:
                st.markdown("#### Board Grid")
                edited_board = st.data_editor(
                    st.session_state.board_grid,
                    column_config={
                        f"{i}": st.column_config.CheckboxColumn(
                            f"C{i}", width="small", default=False
                        ) for i in range(8)
                    },
                    hide_index=True,
                    use_container_width=False,
                    key="board_editor"
                )

            with col_blocks:
                st.markdown("#### Detected Blocks")
                new_blocks = []
                for idx, blk in enumerate(st.session_state.blocks):
                    st.caption(f"Block {idx}")

                    # Pad to 5x5 for editing
                    padded = pad_block_to_5x5(blk)

                    # Ensure key is unique per block AND per file upload session (implicit by rerun reset?)
                    # If we reload, keys might conflict if we don't reset.
                    # But since we rerun on new file, it should be fine.
                    edited_blk = st.data_editor(
                        padded,
                        column_config={
                             f"{i}": st.column_config.CheckboxColumn(width="small", default=False)
                             for i in range(5)
                        },
                        hide_index=True,
                        key=f"block_editor_{idx}",
                        height=150
                    )

                    # Trim back
                    trimmed = trim_block(edited_blk)
                    new_blocks.append(trimmed)

            if st.button("🚀 Confirm & Re-Solve", type="primary"):
                # Update state
                final_board = [[int(cell) for cell in row] for row in edited_board]
                st.session_state.board_grid = final_board
                st.session_state.blocks = new_blocks

                with st.spinner("Solving..."):
                    sol = perform_solve(final_board, new_blocks, strategy)
                    st.session_state.solution = sol if sol else []

                    if not sol:
                        st.warning("⚠️ No valid moves found.")
                    else:
                        st.session_state.step_index = 0
                        st.success("✅ Solution Found!")
                        st.rerun()

    # --- Solution Navigation ---
    if st.session_state.solution:
        st.divider()
        st.header("🎯 Solution Walkthrough")

        solution = st.session_state.solution
        total_steps = len(solution)

        if total_steps == 0:
            st.warning("No moves available.")
        else:
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
            if st.session_state.step_index >= len(solution):
                st.session_state.step_index = 0

            current_step = solution[st.session_state.step_index]
            block_idx = current_step['block_idx']
            r, c = current_step['r'], current_step['c']
            score = current_step.get('score_gain', 0)

            # Prepare content columns
            step_col1, step_col2 = st.columns([1, 2])

            with step_col1:
                st.info(f"**Action:** Place **Block {block_idx}** at (Row {r}, Col {c})")
                st.metric("Score Gain", score)

                current_block = st.session_state.blocks[block_idx]
                block_preview_img = draw_block_preview(current_block)
                st.image(block_preview_img, caption=f"Block {block_idx}", width=150)

            with step_col2:
                viz_img = draw_solution_step(
                    st.session_state.processed_image,
                    st.session_state.board_info,
                    st.session_state.blocks[block_idx],
                    r, c,
                    st.session_state.step_index + 1
                )
                viz_img_rgb = cv2.cvtColor(viz_img, cv2.COLOR_BGR2RGB)
                st.image(viz_img_rgb, caption=f"Visualization for Step {st.session_state.step_index + 1}", use_container_width=True)
