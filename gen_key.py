import hmac
import hashlib
import base64
dig = hmac.new(b'1234567890', msg='abcdefghijklmnopqrstuvxwyz', digestmod=hashlib.sha256).digest()
print (base64.b64encode(dig).decode())      # py3k-mode
