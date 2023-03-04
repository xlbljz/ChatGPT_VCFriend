from flask import Flask, request, Response

from pywchat import Sender
from methods import *
from config import WECOM_COMID, APP_SECRET, WECOM_AGENTID

app = Flask(__name__)
if __name__ == '__main__':
    @app.route('/wx', methods=['GET', 'POST'])
    def wechat_servant():
        print(request)

        if request.method == 'GET':
            return verify_url(request)

        if request.method == 'POST':
            try:
                print('收到POST回调')
                return Response(status=200)

            finally:
                try:
                    xml_dict = xml_parse(request)

                    msg_type = find_key(xml_dict, 'MsgType')

                    if msg_type == 'voice':
                        input_file_path = msg_download(
                            find_key(xml_dict, 'MediaId'))
                        input_text = user_voice2_text(input_file_path)

                    elif msg_type == 'text':
                        input_text = find_key(xml_dict, 'Content')

                    elif msg_type == 'event':
                        print('收到事件类型消息')

                    elif msg_type == None:
                        raise Exception('返回的消息中没有消息类型')

                    else:
                        print('未添加处理的消息类型')

                    output_text = communicate_with_chatgpt(input_text)

                    output_file_path = chatgpt_response2_voice(output_text)

                    send_app = Sender(
                        WECOM_COMID, APP_SECRET, WECOM_AGENTID)
                    send_app.send_voice(output_file_path + '.amr', find_key(xml_dict, 'FromUserName'))
                except Exception as e:
                    print(e)

    app.run(host='0.0.0.0', port=80, debug=True)
