# -*- coding:utf-8 -*-
import requests

try:

    TARGET_URL = 'https://notify-api.line.me/api/notify'
    TOKEN = 'kfFPqRFVZu5LVRajbPHp2gWhWLn6LohzPwUiD8ZI4H0'

    response = requests.post(
        TARGET_URL,
        headers={
            'Authorization': 'Bearer ' + TOKEN
        },
        data={
            'message': "코인봇이 정상 작동중입니다."
        }
    )

except Exception as ex:
    print(ex)
