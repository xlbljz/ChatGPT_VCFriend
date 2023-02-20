from weworkapi_python_master.callback_json.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt
from weworkapi_python_master.callback.WXBizMsgCrypt import WXBizMsgCrypt
import sys
from flask import Flask, request, Response, jsonify
import json

import xml.etree.cElementTree as ET

import requests
from config import config

REQUEST_ID_HEADER = 'x-fc-request-id'

app = Flask(__name__)

sToken = config.sToken
sEncodingAESKey = config.sEncodingAESKey
sCorpID = config.sCorpID
MsgIdglo = ''


@app.route('/wx', methods=['GET', 'POST'])
def wxpush():
    print(request)
    if request.method == 'GET':

        wxcpt = WXBizJsonMsgCrypt(sToken, sEncodingAESKey, sCorpID)
        sVerifyMsgSig = request.args.get('msg_signature')
        sVerifyTimeStamp = request.args.get('timestamp')
        sVerifyNonce = request.args.get('nonce')
        sVerifyEchoStr = request.args.get('echostr')
        # print(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)
        ret, sEchoStr = wxcpt.VerifyURL(
            sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)
        # print('===============')
        # print(ret,sEchoStr)
        aa = int(sEchoStr)
        # print('===============')

        if (ret != 0):
            print("ERR: VerifyURL ret: " + str(ret))

        else:
            print("done VerifyURL")

        return jsonify(aa)

    if request.method == 'POST':
        try:

            print('OKOK')
            # return Response(status=200)

        finally:

            # 微信服务器发来的三个get参数
            signature = request.args.get("signature")
            timestamp = request.args.get("timestamp")
            nonce = request.args.get("nonce")
            # 加进同一个列表里
            list1 = [sToken, timestamp, nonce]
            encrypted_bytes = request.data
            # print(type(encrypted_bytes))
            if encrypted_bytes:            # 获取openid参数和msg_signature参数
                openid = request.args.get("openid")
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
                    content = xml_tree.find("Content").text
                    user = xml_tree.find("FromUserName").text
                    agentid = xml_tree.find("AgentID").text
                    touse = xml_tree.find("ToUserName").text
                    MsgId = xml_tree.find("MsgId").text
                    creat = xml_tree.find("CreateTime").text

                    send(user, agentid, content, MsgId)


def send(touser, agen, content, MsgId):
    print("开始请求", content)
    openaikey = config.openaikey
    print(openaikey)

    MsgIdglo = MsgId
    print(MsgIdglo, MsgId, '开始')
    req = requests.post('https://api.openai.com/v1/completions', json={"prompt": content, "max_tokens": 2048, "model": "text-davinci-003"}, headers={
        'content-type': 'application/json', 'Authorization': 'Bearer '+openaikey})
    print(req)
    reqdic = json.loads(req.text)

    aa = reqdic['choices'][0]['text']
    print("aaaaaa", aa)

    data = {
        'touser': touser,
        'agen': agen,
        'mess': aa
    }
    String_textMsg = json.dumps(data)
    HEADERS = {"Content-Type": "application/json ;charset=utf-8"}
    # 获取token
    r = requests.get(
        f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={sCorpID}&corpsecret={corpsecret}').text
    js = json.loads(r)
    token = js['access_token']
    wechaturl = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}'
    # wechaturl = config.wechaturl
    res = requests.post(wechaturl, data=String_textMsg, headers=HEADERS)
    # return Response(res)
    print(res.text)
    return res.text


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
