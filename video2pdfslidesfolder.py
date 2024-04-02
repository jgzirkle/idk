import os
import time
import cv2
import imutils
import shutil
import img2pdf
import glob
import argparse

# Define constants
OUTPUT_SLIDES_DIR = "./output"
FRAME_RATE = 5  # Frames per second to be processed
WARMUP = FRAME_RATE  # Initial number of frames to be skipped
FGBG_HISTORY = FRAME_RATE * 6  # Number of frames in background object
VAR_THRESHOLD = 16  # Threshold on the squared Mahalanobis distance
DETECT_SHADOWS = False  # If true, the algorithm will detect shadows
MIN_PERCENT = 0.2  # Min % of diff to detect motion stop
MAX_PERCENT = 0.6  # Max % of diff for motion

def sanitize_filename(filename):
    """Sanitize the filename by removing or replacing characters not allowed in Windows paths."""
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '[', ']']
    for ch in invalid_chars:
        filename = filename.replace(ch, '')
    return filename

def get_frames(video_path):
    vs = cv2.VideoCapture(video_path)
    if not vs.isOpened():
        raise Exception(f'Unable to open file {video_path}')
    total_frames = vs.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_time = 0
    frame_count = 0
    print("Total frames:", total_frames)
    print("FRAME_RATE:", FRAME_RATE)
    while True:
        vs.set(cv2.CAP_PROP_POS_MSEC, frame_time * 1000)
        frame_time += 1 / FRAME_RATE
        ret, frame = vs.read()
        if not ret:
            break
        frame_count += 1
        yield frame_count, frame_time, frame
    vs.release()

def detect_unique_screenshots(video_path, output_folder_screenshot_path):
    fgbg = cv2.createBackgroundSubtractorMOG2(history=FGBG_HISTORY, varThreshold=VAR_THRESHOLD, detectShadows=DETECT_SHADOWS)
    captured = False
    start_time = time.time()
    W, H = None, None
    screenshots_count = 0
    for frame_count, frame_time, frame in get_frames(video_path):
        orig = frame.copy()
        frame = imutils.resize(frame, width=600)
        mask = fgbg.apply(frame)
        if W is None or H is None:
            H, W = mask.shape[:2]
        p_diff = (cv2.countNonZero(mask) / float(W * H)) * 100
        if p_diff < MIN_PERCENT and not captured and frame_count > WARMUP:
            captured = True
            filename = f"{screenshots_count:03}_{round(frame_time / 60, 2)}.png"
            path = os.path.join(output_folder_screenshot_path, filename)
            print("Saving:", path)
            cv2.imwrite(path, orig)
            screenshots_count += 1
        elif captured and p_diff >= MAX_PERCENT:
            captured = False
    print(f'{screenshots_count} screenshots captured in {time.time() - start_time}s.')

def initialize_output_folder(video_path):
    folder_name = os.path.splitext(os.path.basename(video_path))[0]
    sanitized_folder_name = sanitize_filename(folder_name)
    output_folder_screenshot_path = os.path.join(OUTPUT_SLIDES_DIR, sanitized_folder_name)
    if os.path.exists(output_folder_screenshot_path):
        shutil.rmtree(output_folder_screenshot_path)
    os.makedirs(output_folder_screenshot_path, exist_ok=True)
    print('Initialized output folder:', output_folder_screenshot_path)
    return output_folder_screenshot_path

def convert_screenshots_to_pdf(output_folder_screenshot_path, video_path):
    images = sorted(glob.glob(os.path.join(output_folder_screenshot_path, "*.png")))
    if images:
        output_pdf_path = f"{output_folder_screenshot_path}.pdf"
        print('Converting images to PDF:', output_pdf_path)
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(images))
        print('PDF created at:', output_pdf_path)
    else:
        print(f"No PNG files found in {output_folder_screenshot_path}. PDF not created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert video files in a directory to PDF slides")
    parser.add_argument("dir_path", help="Directory path containing video files", type=str)
    args = parser.parse_args()
    directory_path = args.dir_path

    for video_file in os.listdir(directory_path):
        video_path = os.path.join(directory_path, video_file)
        if os.path.isfile(video_path) and video_path.endswith(('.mp4', '.avi', '.mov', '.webm')):
            print('Processing video:', video_path)
            output_folder_screenshot_path = initialize_output_folder(video_path)
            detect_unique_screenshots(video_path, output_folder_screenshot_path)
            convert_screenshots_to_pdf(output_folder_screenshot_path, video_path)
