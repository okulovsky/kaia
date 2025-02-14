import cv2
from frame import Frame
from settings import AnalysisSettings
from cv2 import cvtColor, COLOR_BGR2GRAY, Laplacian, CV_64F
from PIL import Image

def layer_capture(settings: AnalysisSettings):
    cap = cv2.VideoCapture('/resources/input/'+settings.source_file_name)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total amount of frames {total_frames}")
    total_frames_digits = len(str(total_frames))

    print("Starting cap")
    cap_count = 0

    while cap.isOpened():
        ret, src_frame = cap.read()

        if not ret:
            break

        pil_image = Image.fromarray(cv2.cvtColor(src_frame, cv2.COLOR_BGR2RGB))
        frame = Frame(src_frame, pil_image)
        frame.index = cap_count
        frame.timestamp_in_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
        frame.filename = str(cap_count).zfill(total_frames_digits) + '.png'
        frame.laplacian = Laplacian(frame.frame, CV_64F).var()
        yield frame

        cap_count += 1
        print(f"{int(100 * cap_count / total_frames)}% done")


    cap.release()