# 相关的秘钥等信息
import os

# [企业微信]
# 接口回调TOKEN
WECOM_TOKEN = ''
# 接口回调AESKEY
WECOM_AESKEY = ''
# 企业ID
WECOM_COMID = ''
# 应用SECRET
APP_SECRET = ''
# 应用ID
WECOM_AGENTID = '1000003'

# [AZURE SPEECHSDK]
KEY = ''
REGION = ''
#  USE_DEFAULT_SPEAKER
AUDIO_CONFIG = True
# THE LANGUAGE AND THE VOICE THAT SPEAKS.
VOICE = ''

# [CHATGPT]
# openaikey
OPENAIKEY = ''
# MODEL TO USE
MODEL = 'GPT-3.5-TURBO'
EMAIL = ''
PASSWORD = ''

globals().update(os.environ)
