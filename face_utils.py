import cv2
import time
import uuid
from PIL import Image
from deepface import DeepFace


REGISTER_PICTURE_COUNT = 30
REGISTER_PICTURE_INTERVAL = .33
model = DeepFace.build_model("Facenet")
detector_backend = "retinaface"


def register_face():
    cap = cv2.VideoCapture(0)
    assert cap.isOpened(),"Camera Not Available."
    ret, frame = cap.read()

    for i in range(REGISTER_PICTURE_COUNT):
        ret, frame = cap.read()
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        img_name = str(uuid.uuid4())
        image.save("./database/_{}.jpg".format(img_name))
        print("Picture Token: _{}.jpg".format(img_name))

        time.sleep(REGISTER_PICTURE_INTERVAL)

    cap.release()
    print("Registered.")


def check_face(path):
    result = DeepFace.find(img_path=path,
                           db_path="./database/", 
                           model_name = "Facenet",
                           enforce_detection=False,
                           distance_metric="cosine",
                           detector_backend=detector_backend)
    if len(result[0]) > 0:
        print("found")
        #print("匹配图像路径：", result[0].iloc[0]['identity'])
        #print("距离（越小越像）：", result[0].iloc[0]['distance'])
    else:
        print("Nah")


def check_face_camera():
    cap = cv2.VideoCapture(0)
    assert cap.isOpened(),"Camera Not Available."
    ret, frame = cap.read()

    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img_name = "test"
    image.save("./{}.jpg".format(img_name))
    print("Picture Token: {}.jpg".format(img_name))
    cap.release()
    check_face("./test.jpg")
