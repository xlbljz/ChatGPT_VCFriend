# from weworkapi_python_master.callback_json.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt
# from weworkapi_python_master.callback.WXBizMsgCrypt import WXBizMsgCrypt
import os
import datetime
import json
import httpx
import base64
import pickle

import xml.etree.cElementTree as ET

from flask import Flask, request, Response, jsonify

import openai
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from configparser import ConfigParser

from weworkapi_python_master.callback.WXBizMsgCrypt3 import WXBizMsgCrypt
from config import config

REQUEST_ID_HEADER = 'x-fc-request-id'

app = Flask(__name__)

sToken = config.sToken
sEncodingAESKey = config.sEncodingAESKey
sCorpID = config.sCorpID
corpsecret = config.corpsecret
MsgIdglo = ''


def steps(msg_list):
    """
    口语语伴主要步骤
    """
    msg_type = msg_list.msgtype

    if msg_type == 'voice':
        input_text = user_voice2_text(
            msg_list.voice.media_id)
    elif msg_type == 'text':
        input_text = msg_list.text.content

    output_text = communicate_with_chatgpt(input_text)

    output_voice_data = chatgpt_response2_voice(output_text)

    send2_wechat(output_voice_data, msg_list.external_userid,
                 msg_list.open_kfid)


config_file = ConfigParser()
config_file.read('setting.ini', encoding='utf-8')
config = config_file['Speechsdk']
speech_config = speechsdk.SpeechConfig(
    subscription=config['Key'], region=config['Region'])
email = config_file['ChatGPT']['Email']
password = config_file['ChatGPT']['Password']


def user_voice2_text(voice_Content):
    # # Find your key and resource region under the 'Keys and Endpoint' tab in your Speech resource in Azure Portal
    # # Remember to delete the brackets <> when pasting your key and region!
    # speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    # speech_config.speech_recognition_language = lang
    # audio_config = speechsdk.AudioConfig(use_default_microphone=True)
    audio_input = speechsdk.AudioConfig(use_default_microphone=False)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_input)

    # 开始连续语音识别
    speech_recognizer.start_continuous_recognition()

    # 循环读取音频数据并进行语音识别
    while True:
        data = voice_Content.read(3200)
        if not data:
            break
        speech_recognizer.push_audio_buffer(data)

    # 结束连续语音识别
    speech_recognizer.stop_continuous_recognition()

    # 保存语音文件
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    input_file_path = f"voice_cache/intput/{now}.wav"
    with open(input_file_path, "wb") as f:
        f.write(voice_Content)

    # 输出识别结果
    for result in speech_recognizer:
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized speech: {}".format(result.text))
            return result.text

        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized.")
            return 'No speech could be recognized.'
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech recognition canceled: {}".format(
                cancellation_details.reason))
            return 'Speech recognition canceled: {}".format(cancellation_details.reason)'


def communicate_with_chatgpt(input_text):
    openai.api_key = config.openaikey
    response = openai.Completion.create(
        model='text-curie-001',
        # model="text-curie-001",
        prompt=input_text,
        temperature=1,
        max_tokens=150,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=0.1,
        stop=["YOU:", "AI:"]
    )
    return response.choices[0].text


def chatgpt_response2_voice(text):
    # # Find your key and resource region under the 'Keys and Endpoint' tab in your Speech resource in Azure Portal
    # # Remember to delete the brackets <> when pasting your key and region!
    # speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    # speech_config.speech_synthesis_language = lang
    # In this sample we are using the default speaker
    # Learn how to customize your speaker using SSML in Azure Cognitive Services Speech documentation
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    global output_file_path
    output_file_path = f"voice_cache/output/{now}.wav"
    # audio_output = speechsdk.audio.AudioOutputConfig(filename=file_name)
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.AmrWb16000Hz)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()
    stream = speechsdk.AudioDataStream(result)
    stream.save_to_wav_file(output_file_path)
    return result


def send2_wechat(output_voice_data, user_id, servant_id):
    # 上传临时素材
    # 设置请求地址和参数
    upload_url = 'https://qyapi.weixin.qq.com/cgi-bin/media/upload'
    params = {
        'access_token': access_token,
        'type': 'voice'
    }
    boundary = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}

    # 构造 multipart/form-data 格式的请求体
    voice_base64 = base64.b64encode(
        output_voice_data.audio_data).decode('utf-8')
    duration = output_voice_data.audio_duration

    data = {
        'Content-Disposition': f'form-data; name="media"; filename={os.path.basename(output_file_path)};duration={duration}',
        'Content-Type': 'application/octet-stream',
        'form-data': (None, voice_base64, None)}
    response = httpx.post(upload_url, data=data,
                          params=params, headers=headers)

    # 处理API的响应结果
    if response.status_code == 200:
        media_id = response.json()["media_id"]
        print("上传成功，media_id为：", media_id)
    else:
        print("上传失败，错误码为：", response.status_code)

    # 调用客服接口向客户发送消息
    params = {'access_token': access_token}
    data = {
        'touser': user_id,
        'open_kfid': servant_id,
        'msgtype': 'voice',
        'voice': {
            'media_id': media_id
        }
    }
    string_textmsg = json.dumps(data)
    # HEADERS = {"Content-Type": "application/json ;charset=utf-8"}
    send_url = f'https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg'
    # wechaturl = config.wechaturl
    # res = httpx.post(wechaturl, data=string_textmsg, headers=HEADERS)
    res = httpx.post(send_url, data=string_textmsg, params=params)
    # 处理发送消息的响应结果
    if res.status_code == 200:
        print("发送成功")
    else:
        print("发送失败，错误码为：", res.status_code)


@app.route('/wx', methods=['GET', 'POST'])
def wechat_servant():
    print(request)
    if request.method == 'GET':
        # wxcpt = WXBizJsonMsgCrypt(sToken, sEncodingAESKey, sCorpID)
        wxcpt = WXBizMsgCrypt(sToken, sEncodingAESKey, sCorpID)
        sVerifyMsgSig = request.args.get('msg_signature')
        sVerifyTimeStamp = request.args.get('timestamp')
        sVerifyNonce = request.args.get('nonce')
        sVerifyEchoStr = request.args.get('echostr')
        # print(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)
        ret, sEchoStr = wxcpt.VerifyURL(
            sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)
        # print('===============')
        # print(ret,sEchoStr)
        # sEchoStr = int(sEchoStr)
        # print('===============')

        if (ret != 0):
            print("ERR: VerifyURL ret: " + str(ret))
        else:
            print("done VerifyURL")
        # return jsonify(sEchoStr)
        return sEchoStr

    if request.method == 'POST':
        try:
            print('OKOK')
            # return Response(status=200)
        finally:
            # 微信服务器发来的三个get参数
            # signature = request.args.get("signature")
            timestamp = request.args.get("timestamp")
            nonce = request.args.get("nonce")
            # 加进同一个列表里
            # list1 = [sToken, timestamp, nonce]
            encrypted_bytes = request.data
            # print(type(encrypted_bytes))
            if encrypted_bytes:            # 获取openid参数和msg_signature参数
                # openid = request.args.get("openid")
                msg_signature = request.args.get("msg_signature")
                # 用微信官方提供的SDK解密，附带一个错误码和生成明文
                keys = WXBizMsgCrypt(sToken, sEncodingAESKey, sCorpID)
                # print('-----')
                # print(encrypted_bytes, msg_signature, timestamp, nonce)
                # encrypted_bytes.encode()

                ierror, decrypted_bytes = keys.DecryptMsg(
                    encrypted_bytes, msg_signature, timestamp, nonce)
                # 若错误码为0则表示解密成功
                print(decrypted_bytes)

                if ierror == 0:
                    # 对XML进行解析
                    # print('00000')
                    # dom_data = parseString(decrypted_bytes).documentElement
                    xml_tree = ET.fromstring(decrypted_bytes)
                    print(xml_tree)
                    # content = xml_tree.find("Content").text
                    # user = xml_tree.find("FromUserName").text
                    # agentid = xml_tree.find("AgentID").text
                    # touse = xml_tree.find("ToUserName").text
                    # MsgId = xml_tree.find("MsgId").text
                    # creat = xml_tree.find("CreateTime").text
                    global xml_dict
                    xml_dict = {
                        elem.tag: elem.text for elem in xml_tree.iter()}

                    # 使用企业微信 API 接收消息
                    # 获取token
                    r = httpx.get(
                        f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={sCorpID}&corpsecret={corpsecret}').text
                    js = json.loads(r)
                    global access_token
                    access_token = js['access_token']

                    try:
                        with open('cursor.pickle', 'rb') as cursor_file:
                            cursor = pickle.load(cursor_file)['cursor']
                    except Exception:
                        cursor = None

                    # 下载消息内容
                    params = {
                        'access_token': access_token,
                        'cursor': cursor,
                        'token': xml_dict['token'],
                        "open_kfid": xml_dict['open_kfid']
                    }
                    # 持续下载数据直到下载完毕
                    while True:
                        download_response = httpx.get(
                            f"https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg", stream=True, params=params)
                        # 处理API的响应结果
                        if download_response.status_code == 200:
                            print("下载成功，消息如下：", download_response.msg_list)
                            if download_response.has_more == 0:
                                cursor = download_response.next_cursor
                                with open('cursor.pickle', 'wb') as cursor_file:
                                    pickle.dump(cursor, cursor_file)
                                break
                        else:
                            print("下载失败，错误码为：", download_response.status_code)
                    # 执行主要步骤
                    steps(download_response.msglist)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
