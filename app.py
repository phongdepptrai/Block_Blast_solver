import streamlit as st
import numpy as np
import cv2
from PIL import Image
import analyze_image
import solver

def draw_solution_step(base_img, board_info, block, r, c, step_idx):
    """
    Draws the block at the specified position on the board.
    """
    img = base_img.copy()

    bx = board_info['x']
    by = board_info['y']
    cw = board_info['cell_w']
    ch = board_info['cell_h']

    # Define colors for different steps to distinguish them?
    # Or just a standard color (e.g., Green for placement)
    color = (0, 255, 0) # Green

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

                # Draw rectangle with some padding
                padding = 5
                cv2.rectangle(overlay, (px + padding, py + padding), (px + cw - padding, py + ch - padding), color, -1)

                # Add text?
                # cv2.putText(overlay, str(step_idx), (px + cw//2 - 10, py + ch//2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

    # Blend
    alpha = 0.6
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    return img

st.title("Block Blast Solver")

uploaded_file = st.file_uploader("Upload Game Screenshot", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Convert uploaded file to opencv image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)

    # Convert from BGR to RGB for Streamlit display
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    st.image(img_rgb, caption='Uploaded Image', use_column_width=True)

    if st.button("Solve"):
        with st.spinner("Analyzing image..."):
            try:
                board, blocks, board_info = analyze_image.get_game_state(image_array=img)

                if board is None:
                    st.error("Could not detect board. Please ensure the full 8x8 grid is visible.")
                else:
                    st.success("Board and Blocks detected!")

                    # Visualize Board
                    with st.expander("Debug Details"):
                        st.subheader("Detected Board State")
                        st.text(str(np.array(board)))

                        st.subheader("Detected Blocks")
                        cols = st.columns(len(blocks))
                        for i, b in enumerate(blocks):
                            with cols[i]:
                                st.write(f"Block {i}")
                                st.text(str(np.array(b)))

                    # Solve
                    with st.spinner("Calculating best moves..."):
                        s = solver.BlockBlastSolver()
                        solution = s.solve(board, blocks)

                        if not solution:
                            st.warning("No valid moves found!")
                        else:
                            st.subheader("Solution")

                            # Keep track of board state for successive visualizations?
                            # The user probably wants to see where to place blocks on the ORIGINAL image.
                            # But if lines clear, the board changes.
                            # However, showing the placement on the static board is usually enough for the user to execute the move.
                            # Let's show the placement on the ORIGINAL image for each step,
                            # or update the image cumulatively?
                            # Updating cumulatively is hard because we need to simulate the "look" of the board updating.
                            # Let's just show the placement on the base image (or the image state as we know it, but we can't easily re-render the cleared lines visually).
                            # So, for each step, we show: "Place this block HERE".

                            for step_idx, step in enumerate(solution):
                                b_idx = step['block_idx']
                                r = step['r']
                                c = step['c']
                                score = step['score_gain']

                                st.markdown(f"**Step {step_idx + 1}:** Place **Block {b_idx}** at Row **{r}**, Column **{c}** (Score: {score})")

                                # Draw
                                viz_img = draw_solution_step(img, board_info, blocks[b_idx], r, c, step_idx + 1)
                                viz_img_rgb = cv2.cvtColor(viz_img, cv2.COLOR_BGR2RGB)

                                st.image(viz_img_rgb, caption=f"Placement for Step {step_idx + 1}", use_column_width=True)

            except Exception as e:
                st.error(f"An error occurred: {e}")
                import traceback
                st.text(traceback.format_exc())
