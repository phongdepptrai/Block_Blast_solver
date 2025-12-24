import cv2
import numpy as np

def get_game_state(image_path=None, image_array=None):
    """
    Analyzes the image and returns the board grid, available blocks, and board metadata.
    Returns:
        board_grid (list of lists): 8x8 matrix
        detected_shapes (list of lists): List of block matrices
        board_info (dict): Metadata for visualization {'x': int, 'y': int, 'cell_w': int, 'cell_h': int}
    """
    if image_array is not None:
        img = image_array
    elif image_path:
        img = cv2.imread(image_path)
    else:
        raise ValueError("No image provided")

    if img is None:
        raise ValueError("Could not read image")

    # --- Board Detection ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    board_contour = None
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        if 0.9 < aspect_ratio < 1.1 and w > 100:
            board_contour = cnt
            break

    if board_contour is None:
        return None, None, None

    bx, by, bw, bh = cv2.boundingRect(board_contour)
    board_roi = img[by:by+bh, bx:bx+bw]

    cell_w = bw // 8
    cell_h = bh // 8

    board_info = {
        'x': bx,
        'y': by,
        'cell_w': cell_w,
        'cell_h': cell_h
    }

    board_grid = np.zeros((8, 8), dtype=int)

    for r in range(8):
        for c in range(8):
            cx = c * cell_w
            cy = r * cell_h
            margin = int(cell_w * 0.3)
            cell_roi = board_roi[cy+margin:cy+cell_h-margin, cx+margin:cx+cell_w-margin]

            hsv_cell = cv2.cvtColor(cell_roi, cv2.COLOR_BGR2HSV)
            mean_s = np.mean(hsv_cell[:,:,1])
            mean_v = np.mean(hsv_cell[:,:,2])

            if mean_v > 130:
                board_grid[r, c] = 1
            elif mean_s > 160:
                 board_grid[r, c] = 1
            else:
                 board_grid[r, c] = 0

    # --- Block Detection ---
    blocks_start_y = by + bh + 20
    blocks_roi = img[blocks_start_y:, :]

    detected_shapes = []

    if blocks_roi.shape[0] > 0:
        blocks_gray = cv2.cvtColor(blocks_roi, cv2.COLOR_BGR2GRAY)
        blocks_edges = cv2.Canny(blocks_gray, 50, 150)
        kernel = np.ones((5,5), np.uint8)
        dilated_edges = cv2.dilate(blocks_edges, kernel, iterations=3)

        block_contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        valid_blocks = []
        for cnt in block_contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 30 and h > 30:
                valid_blocks.append((x, y, w, h))

        # Sort blocks from left to right
        valid_blocks.sort(key=lambda b: b[0])

        # Expected unit size is half the board cell size
        target_unit = cell_w * 0.5

        for (x, y, w, h) in valid_blocks:
            cols = max(1, int(round(w / target_unit)))
            rows = max(1, int(round(h / target_unit)))

            shape_matrix = np.zeros((rows, cols), dtype=int)

            step_w = w / cols
            step_h = h / rows

            for r in range(rows):
                for c in range(cols):
                    sy = int((r + 0.5) * step_h)
                    sx = int((c + 0.5) * step_w)

                    if sy >= h or sx >= w: continue

                    sample_roi = blocks_roi[y+sy-2:y+sy+3, x+sx-2:x+sx+3]
                    if sample_roi.size == 0: continue

                    hsv_s = cv2.cvtColor(sample_roi, cv2.COLOR_BGR2HSV)
                    mean_h = np.mean(hsv_s[:,:,0])
                    mean_s = np.mean(hsv_s[:,:,1])
                    mean_v = np.mean(hsv_s[:,:,2])

                    bg_hsv = np.array([11, 138, 176])
                    pixel_hsv = np.array([mean_h, mean_s, mean_v])

                    dist = np.linalg.norm(pixel_hsv - bg_hsv)

                    if dist > 40:
                        shape_matrix[r, c] = 1
                    else:
                        shape_matrix[r, c] = 0

            detected_shapes.append(shape_matrix.tolist())

    return board_grid.tolist(), detected_shapes, board_info

if __name__ == "__main__":
    board, blocks, info = get_game_state("image.png")
    print("Board Info:", info)
