import logging as log
from time import perf_counter
import cv2
from openvino.runtime import Core,get_version
from landmarks_detector import LandmarksDetector
from face_detector import FaceDetector
from faces_database import FacesDatabase
from face_identifier import FaceIdentifier
from model_api.performance_metrics import PerformanceMetrics
import psycopg2
source = "videos/we.mp4"
device ="CPU"
from datetime import date

faceDETECT = "model_2022_3/face-detection-retail-0005.xml" 
faceLANDMARK = "model_2022_3/landmarks-regression-retail-0009.xml"
FaceIDENTIFY = "model_2022_3/face-reidentification-retail-0095.xml"
#FaceIDENTIFY = "model_2022_3/facenet.xml" 
git_face_detect = "intel/face-detection-adas-0001/FP16/face-detection-adas-0001.xml"
git_face_identity = "public/facenet-20180408-102900/FP16/facenet-20180408-102900.xml"

class FrameProcessor:
    QUEUE_SIZE = 16
    def __init__(self):
        log.info("OpenVINO Runtime")
        log.info("\tbuild: {}".format(get_version()))
        core = Core()
        self.face_detector = FaceDetector(core,faceDETECT,input_size=(0,0),confidence_threshold=0.7)
        self.landmarks_detector = LandmarksDetector(core,faceLANDMARK)
        self.face_identifier = FaceIdentifier(core,FaceIDENTIFY,match_threshold=0.5,match_algo="HUNGARIAN")
        
        
        self.face_detector.deploy(device)
        self.landmarks_detector.deploy(device,self.QUEUE_SIZE)
        self.face_identifier.deploy(device,self.QUEUE_SIZE)
        
        
        self.faces_database = FacesDatabase("../dataset",self.face_identifier, self.landmarks_detector,)
        self.face_identifier.set_faces_database(self.faces_database)
        log.info("Database is built, registered {} identites".format(len(self.faces_database)))
    def face_process(self,frame):
        rois = self.face_detector.infer((frame,))
        if self.QUEUE_SIZE>len(rois):
            rois = rois[:self.QUEUE_SIZE]
        landmarks = self.landmarks_detector.infer((frame,rois))
        face_identities,unknowns = self.face_identifier.infer((frame,rois,landmarks))
        return [rois,landmarks,face_identities]

def draw_face_detection(frame,frame_processor,detections):
    size = frame.shape[:2]
    for roi,landmarks,identity in zip(*detections):
        text = frame_processor.face_identifier.get_identity_label(identity.id)
        xmin = max(int(roi.position[0]),0)
        ymin = max(int(roi.position[1]),0)
        xmax = min(int(roi.position[0] + roi.size[0]), frame.shape[1])
        ymax = min(int(roi.position[1] + roi.size[1]), frame.shape[0])
        cv2.rectangle(frame,(xmin,ymin),(xmax,ymax),(0,220,0),1)
        face_point = xmin,ymin
        for point in landmarks:
            x = int(xmin + roi.size[0]*point[0])
            y = int(ymin + roi.size[1]*point[1])
            cv2.circle(frame,(x,y),1,(0,255,255),2)
        text = image_recognizer(frame,text,identity,face_point,0.7)
    return frame,text
def image_recognizer(frame,text,identity,face_point,threshold):
    xmin ,ymin = face_point
    if identity.id!=FaceIdentifier.UNKNOWN_ID:
        if(1-identity.distance)>threshold:
            textsize = cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX,0.7,1)[0]
            cv2.rectangle(frame, (xmin, ymin), (xmin+textsize[0], ymin+textsize[1]), (255,255,255), cv2.FILLED)
            cv2.putText(frame,f"{text}>{threshold}",(xmin,ymin),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),1)
        else:
            text = 'unknown'
            textsize = cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX,0.7,1)[0]
            
            cv2.rectangle(frame, (xmin, ymin), (xmin+textsize[0], ymin+textsize[1]), (255,255,255), cv2.FILLED)
            cv2.putText(frame,f"Unknown<{threshold}",(xmin,ymin),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),1)      
    return text
def update_total_present_by_id(id):
    # Replace these with your actual credentials
    DATABASE_URL = 'postgresql://postgres:2*aA2*eFec-bB3AfF14B-ad4G*gAb*dD@monorail.proxy.rlwy.net:39199/railway'

    # Create a connection to the database
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    except psycopg2.Error as e:
        
        return

    # Create a cursor object
    cur = conn.cursor()

    try:
        # Fetch the date from the database for the given ID
        cur.execute("SELECT date FROM student_table WHERE sid = %s", (id,))
        result = cur.fetchone()
        if result:
            stored_date = result[0]
            stored_date = str(stored_date)
            today_date = date.today().strftime("%Y-%m-%d")
            today_date = today_date
            if stored_date != today_date:
                # If the dates are different, update total_present
                cur.execute("UPDATE student_table SET total_present = total_present + 1, date = %s WHERE sid = %s", (today_date, id))
                conn.commit()  # Don't forget to commit the changes
                
            else:
                pass
        else:
            pass
    except psycopg2.Error as e:
        pass
    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()
        
def db():
    DATABASE_URL = 'postgresql://postgres:2*aA2*eFec-bB3AfF14B-ad4G*gAb*dD@monorail.proxy.rlwy.net:39199/railway'

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    except psycopg2.Error as e:
        
        return
    cur = conn.cursor()

    # Update the value in the database
    sid_value = 2  # Student ID to update
    new_present_days = 1  # New value for total_present

    update_query = f"UPDATE student_table SET total_present = {new_present_days} WHERE sid = {sid_value};"

    cur.execute(update_query)

    # Commit the changes
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()




cap = cv2.VideoCapture(0)
frame_processor = FrameProcessor()
metrics = PerformanceMetrics()
count = 0
prev_id = None
id_list = set()
while True:
    start_time = perf_counter()
    ret, frame = cap.read()
    detections = frame_processor.face_process(frame)
    frame, text = draw_face_detection(frame, frame_processor, detections)
    try:
        id = int(text[-1])
        if id == prev_id:
            count += 1
            if count == 5:
                if id not in id_list:
                    id_list.add(id)
                    update_total_present_by_id(id)
                count = 0  # Reset count after updating
        else:
            count = 0  # Reset count if IDs are different
        prev_id = id  # Update prev_id for the next iteration
    except ValueError:
        continue
    metrics.update(start_time, frame)
    cv2.imshow("face", frame)
    key = cv2.waitKey(1)
    if key in {ord('q'), ord('Q'), 27}:
        cap.release()
        cv2.destroyAllWindows()
        break