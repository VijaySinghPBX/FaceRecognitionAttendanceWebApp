import firebase_admin
from flask import Flask, render_template, request
import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
from firebase_admin import db, credentials, storage
from _datetime import datetime

app = Flask(__name__)
cred = credentials.Certificate("DatabaseAccessKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://bca2023-37329-default-rtdb.firebaseio.com/",
    'storageBucket': "bca2023-37329.appspot.com"
})
ref = db.reference('Students')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add', methods=['POST'])
def addStudent():
    name = request.form['name']
    course = request.form['course']
    semester = int(request.form['semester'])
    session = request.form['session']
    student_id = request.form['student_id']
    image = request.files['image']
    filename = student_id + '.' + image.filename.split('.')[-1]
    data = {
        student_id: {
            "name": name,
            "course": course,
            "semester": semester,
            "session": session,
            "total_attendances": 0,
            "last_attendance_time": "2023-4-4 00:11:56",
            "standing": "G"
        }
    }
    ref.update(data)

    imagePath = os.path.join('Images', filename)
    image.save(imagePath)

    imagePathFolder = 'Images'
    imagePathList = os.listdir(imagePathFolder)
    for path in imagePathList:
        image = f"{imagePathFolder}/{path}"
        bucket = storage.bucket()
        blob = bucket.blob(image)
        blob.upload_from_filename(image)

    encoding()
    return "Student Registered and Encoded Successfully"


@app.route('/encoding')
def encoding():
    folderPath = 'Images'
    pathList = os.listdir(folderPath)
    print(pathList)
    imgList = []
    studentIds = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        studentIds.append(os.path.splitext(path)[0])

    def findEncodings(imagesList):
        encodeList = []
        for img in imagesList:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faceLocations = face_recognition.face_locations(img)
            if len(faceLocations) == 0:
                encodeList.append(None)
                continue
            encode = face_recognition.face_encodings(img, faceLocations)[0]
            encodeList.append(encode)
        return list(filter(lambda x: x is not None, encodeList))

    print("Encoding Started ...")
    encodeListKnown = findEncodings(imgList)
    encodeListKnownWithIds = [encodeListKnown, studentIds]
    print("Encoding Complete")
    file = open("EncodeFile.p", 'wb')
    pickle.dump(encodeListKnownWithIds, file)
    file.close()
    print("File Saved")
    return "Encoding Complete"


@app.route('/start')
def start():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    imgBackground = cv2.imread('Resources/background.png')
    folderModePath = 'Resources/Modes'
    modePathList = os.listdir(folderModePath)
    imgModeList = []
    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

    file = open('EncodeFile.p', 'rb')
    encodedListWithId = pickle.load(file)
    file.close()
    encodedImgList, studentID = encodedListWithId

    bucket = storage.bucket()
    modeType = 0
    counter = 0
    imgResized = []
    while True:
        success, img = cap.read()

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if faceCurFrame:

            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                faceDis = face_recognition.face_distance(encodedImgList, encodeFace)
                matchIndex = np.argmin(faceDis)
                if matchIndex and faceDis[matchIndex] < 0.6:
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                    id = studentID[matchIndex]
                    if counter == 0:
                        counter = 1
                        modeType = 1
                else:
                    print("Not class student")

            if counter != 0:
                if counter == 1:
                    studentInfo = db.reference(f'Students/{id}').get()
                    print(id)
                    print(studentInfo)
                    blob = bucket.get_blob(f'Images/{id}.jpg')
                    imgArray = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(imgArray, cv2.COLOR_BGRA2BGR)
                    imgResized = cv2.resize(imgStudent, (216, 216))
                    ref = db.reference(f'Students/{id}')
                    dateTimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                                                       "%Y-%m-%d %H:%M:%S")
                    secondsElapse = (datetime.now() - dateTimeObject).total_seconds()
                    print(secondsElapse)
                    if secondsElapse > 20:
                        studentInfo['total_attendances'] += 1
                        ref.child('total_attendances').set(studentInfo['total_attendances'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if modeType != 3:
                    if 10 < counter < 20:
                        modeType = 2
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)
                        cv2.putText(imgBackground, str(studentInfo['total_attendances']), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                        imgBackground[175:175 + 216, 909:909 + 216] = imgResized
                        cv2.putText(imgBackground, str(studentInfo['course']), (1006, 550),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(studentInfo['semester']), (1025, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(studentInfo['session']), (1125, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(id), (1006, 493),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                    counter += 1

                if counter >= 20:
                    modeType = 0
                    counter = 0
                    studentInfo = []
                    imgResized = []
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        else:
            modeType = 0
            counter = 0
        cv2.imshow('Face Recognition', imgBackground)
        cv2.waitKey(1)


@app.route('/stop')
def stop():
    os.kill(os.getpid(), 9)
    return "Stopped"


if __name__ == '__main__':
    app.run(debug=True)
