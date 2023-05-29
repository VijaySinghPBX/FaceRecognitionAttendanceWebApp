import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import db
import os
cred = credentials.Certificate("DatabaseAccessKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://bca2023-37329-default-rtdb.firebaseio.com/",
    'storageBucket': "bca2023-37329.appspot.com"
})

ref = db.reference('Students')
data = {
    "20001311062":
        {
            "name": "Vijay Singh",
            "course": "BCA",
            "semester": 6,
            "session": "2020-23",
            "total_attendances": 0,
            "last_attendance_time": "2023-4-4 00:11:56",
            "standing": "G"
        },
    "20001321063":
        {
            "name": "Yudhisthir",
            "course": "Physics",
            "semester": 6,
            "session": "2020-23",
            "total_attendances": 0,
            "last_attendance_time": "2023-4-4 00:11:56",
            "standing": "G"
        },
    "20001002005":
        {
            "name": "Sahil",
            "course": "Civil Engg",
            "semester": 6,
            "session": "2020-23",
            "total_attendances": 0,
            "last_attendance_time": "2023-4-4 00:11:56",
            "standing": "G"
        },
    "20001002050":
        {
            "name": "Surender",
            "course": "Civil Engg",
            "semester": 6,
            "session": "2020-23",
            "total_attendances": 0,
            "last_attendance_time": "2023-4-4 00:11:56",
            "standing": "G"
        }
}

for key, value in data.items():
    ref.child(key).set(value)

imagePathFolder = 'Images'
imagePathList = os.listdir(imagePathFolder)
imageList = []
for path in imagePathList:
    image = f"{imagePathFolder}/{path}"
    bucket = storage.bucket()
    blob = bucket.blob(image)
    blob.upload_from_filename(image)
