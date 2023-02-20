# 里面放着相关的秘钥等信息
import os
globals().update(os.environ)
class config():
#openaikey
    openaikey = OPENAI_KEY
# 企业微信的接口回调token
    sToken = WECOM_TOKEN
# 企业微信的接口回调AESKEY
    sEncodingAESKey = WECOM_AESKEY
# 企业微信的企业ID
    sCorpID = WECOM_COMID
#  腾讯云的函数公网访问域名
    wechaturl = f'https://servicetencentcs.com/release/'

