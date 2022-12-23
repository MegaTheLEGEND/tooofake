import json
import uuid
import requests
import os
import io
from flask import Flask, request
import models.instant
from parse import Parse
from urllib.parse import quote_plus
import pendulum
from PIL import Image

app = Flask(__name__)

api_url="https://mobile.bereal.com/api"
google_api_key="AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA"

head = {
    "x-firebase-client": "apple-platform/ios apple-sdk/19F64 appstore/true deploy/cocoapods device/iPhone9,1 fire-abt/8.15.0 fire-analytics/8.15.0 fire-auth/8.15.0 fire-db/8.15.0 fire-dl/8.15.0 fire-fcm/8.15.0 fire-fiam/8.15.0 fire-fst/8.15.0 fire-fun/8.15.0 fire-install/8.15.0 fire-ios/8.15.0 fire-perf/8.15.0 fire-rc/8.15.0 fire-str/8.15.0 firebase-crashlytics/8.15.0 os-version/14.7.1 xcode/13F100",
    "user-agent":"FirebaseAuth.iOS/8.15.0 AlexisBarreyat.BeReal/0.22.4 iPhone/14.7.1 hw/iPhone9_1",
    "x-ios-bundle-identifier": "AlexisBarreyat.BeReal",
    "x-firebase-client-log-type": "0",
    "x-client-version": "iOS/FirebaseSDK/8.15.0/FirebaseCore-iOS",
}

@app.route("/")
def slash():
    return "<p>/</p>"

@app.route("/sendotp/<phone>")
def send_otp(phone: str):
    print(phone)
    res = requests.post(
        url="https://www.googleapis.com/identitytoolkit/v3/relyingparty/sendVerificationCode",
        params={"key":google_api_key},
        data={
                "phoneNumber": phone,
                "iosReceipt": "AEFDNu9QZBdycrEZ8bM_2-Ei5kn6XNrxHplCLx2HYOoJAWx-uSYzMldf66-gI1vOzqxfuT4uJeMXdreGJP5V1pNen_IKJVED3EdKl0ldUyYJflW5rDVjaQiXpN0Zu2BNc1c",
                "iosSecret": "KKwuB8YqwuM3ku0z",
            },
        headers=head
    ).json()
    print(res)
    return res

@app.route("/verifyotp/<otp>/<session>")
def verify_otp(otp: str, session: str):
    if session is None:
        raise Exception("No open otp session.")
    res = requests.post(
        url="https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPhoneNumber",
        params={"key": google_api_key},
        data={
            "sessionInfo": session,
            "code": otp,
            "operation": "SIGN_UP_OR_IN",
        },
    ).json()
    print(res)
    return res

@app.route("/refresh/<token>")
def refresh(token: str):
    res = requests.post(
        url="https://securetoken.googleapis.com/v1/token",
        params={"key": google_api_key},
        data={
            "refresh_token": token,
            "grant_type": "refresh_token"
        }
    ).json()
    print(res)
    return res

@app.route("/instants/<token>")
def instants(token: str):
    print('token', token)
    res = requests.get(
        url=api_url+'/feeds/friends',
        headers={"authorization": token},
    ).json()
    print(res)
    ret = Parse.instant(res)
    print(ret)
    return json.dumps(ret)

@app.route("/uploadinstant/<token>/<uid>", methods=["POST"])
def uploadinstant(token:str, uid:str):
    p = request.files['primary'] 
    print(type(p))
    primary = Image.open(io.BytesIO(p.read()))
    prim_data = io.BytesIO()
    primary.save(prim_data, format="JPEG", quality=90)
    prim_data = prim_data.getvalue()
    primarysize = str(len(prim_data))
    print('--------------')
    print(type(prim_data))
    print(len(prim_data))
    print(prim_data)
    print(primary)
    with open('test.jpg', 'wb') as f:
        f.write(prim_data)
    print('--------------')

    name = f"Photos/{uid}/bereal/{uuid.uuid4()}-{int(pendulum.now().timestamp())}{'-secondary' if False else ''}.jpg"
    print(name)
    json_data = {
            "cacheControl": "public,max-age=172800",
            "contentType": "image/webp",
            "metadata": {"type": "bereal"},
            "name": name,
        }
    headers = {
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-command": "start",
            "x-firebase-storage-version": "ios/9.4.0",
            "x-goog-upload-content-type": "image/webp",
            "Authorization": f"Firebase {token}",
            "x-goog-upload-content-length": str(133400),#""" primarysize """, #str(len(primary)),
            "content-type": "application/json",
            "x-firebase-gmpid": "1:405768487586:ios:28c4df089ca92b89",
        }
    params = {
            "uploadType": "resumable",
            "name": name,
        }
    uri = f"https://firebasestorage.googleapis.com/v0/b/storage.bere.al/o/{quote_plus(name)}"
    print("URI: ", uri)
    init_res = requests.post(
            uri, headers=headers, params=params, data=json.dumps(json_data)
    )
    print("INITIAL RESULT: ", init_res)
    if init_res.status_code != 200:
        raise Exception(f"Error initiating upload: {init_res.status_code}")
    upload_url = init_res.headers["x-goog-upload-url"]
    headers2 = {
        "x-goog-upload-command": "upload, finalize",
        "x-goog-upload-protocol": "resumable",
        "x-goog-upload-offset": "0",
        "content-type": "image/jpeg",
    }
    # upload the image
    print("UPLOAD URL", upload_url)
    u""" pload_res = requests.put(url=upload_url, headers=headers2, data=prim_data)
    if upload_res.status_code != 200:
        print("ISSUE!!!!")
        print(upload_res)
        raise Exception(f"Error uploading image: {upload_res.status_code}, {upload_res.text}")
    res_data = upload_res.json() """
    return ''

@app.route("/postinstant/<token>")
def postinstant(token: str):
    json_data = {
        "isPublic": False,
        "caption": 'test',
        "takenAt": 1610000000,
        "isLate": False,
        "location": { 'latitude': "37.2297175", 'longitude': "-115.7911082" },
        "retakeCounter": 0,
        "backCamera": {
            "bucket": "storage.bere.al",
            "height": 2000,
            "width": 1500,
            "path": 'https://www.tutlane.com/images/python/python_string_replace_method.png',
        },
        "frontCamera": {
            "bucket": "storage.bere.al",
            "height": 2000,
            "width": 1500,
            "path": 'https://www.tutlane.com/images/python/python_string_replace_method.png',
        },
    }
    res = requests.post(
        url=api_url+'/content/post',
        json=json_data,
        headers={"authorization": token},
    )
    print(res)
    print(res.json())
    return res.json()

if __name__ == '__main__':
    #app.run(port=5100, debug=True)
    app.run(debug=True, port=os.getenv("PORT", default=5100))
    print('online')

    