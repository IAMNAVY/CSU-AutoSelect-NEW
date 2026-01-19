# filename: new_login.py
import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import random

# ================= 配置区域 =================
LOGIN_URL = "https://ca.csu.edu.cn/authserver/login?service=http%3A%2F%2Fcsujwc.its.csu.edu.cn%2Fsso.jsp"
# ============================================

AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"

def random_string(length):
    return ''.join(random.choice(AES_CHARS) for _ in range(length))

def get_aes_string(plaintext, key_text, iv_text):
    key_text = key_text.strip()
    key = key_text.encode('utf-8')
    iv = iv_text.encode('utf-8')
    data = plaintext.encode('utf-8')
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_bytes = cipher.encrypt(pad(data, AES.block_size))
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def encrypt_password(password, salt):
    if not salt:
        return password
    try:
        random_prefix = random_string(64)
        plaintext = random_prefix + password
        iv_str = random_string(16)
        return get_aes_string(plaintext, salt, iv_str)
    except Exception as e:
        print(f"加密失败: {e}")
        return password

def login(username, password):
    """
    执行登录流程，成功返回 session，失败返回 None
    """
    session = requests.Session()
    # 伪装 Header
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    })

    print("[*] [Login] 正在访问登录页获取加密参数...")
    try:
        resp = session.get(LOGIN_URL)
        resp.raise_for_status()
    except Exception as e:
        print(f"[!] 网络请求失败: {e}")
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    execution_input = soup.find('input', {'name': 'execution'})
    if not execution_input:
        print("[!] 错误: 无法获取 execution，可能页面结构变更或IP被封。")
        return None
    execution = execution_input['value']

    salt_input = soup.find('input', {'id': 'pwdEncryptSalt'})
    if not salt_input:
        salt_input = soup.find('input', {'id': 'pwdDefaultEncryptSalt'})
    salt = salt_input['value'] if salt_input else None

    # 加密密码
    encrypted_pw = encrypt_password(password, salt)

    data = {
        "username": username,
        "password": encrypted_pw,
        "captcha": "", # 协议登录目前无法自动处理验证码，如果遇到需要验证码的情况会失败
        "_eventId": "submit",
        "cllt": "userNameLogin",
        "dllt": "generalLogin",
        "lt": "",
        "execution": execution
    }

    print("[*] [Login] 发送登录请求...")
    # 禁止自动跳转，以便捕获 302
    login_resp = session.post(LOGIN_URL, data=data, allow_redirects=False)

    if login_resp.status_code == 302:
        redirect_url = login_resp.headers.get('Location')
        print(f"[+] [Login] 认证成功，正在跳转至教务系统: {redirect_url}")
        
        # 关键一步：手动跟随跳转，让 Session 获取 JWC 的 Cookie
        final_resp = session.get(redirect_url)
        
        # 简单验证一下是否真的进去了（检查Cookie或者页面内容）
        if "csujwc" in final_resp.url or final_resp.status_code == 200:
             print("[+] [Login] Session 初始化完成！")
             return session
        else:
             print("[!] [Login] 跳转后状态异常，但已返回 Session 供尝试。")
             return session
             
    else:
        print(f"[x] [Login] 登录失败，状态码: {login_resp.status_code}")
        # 尝试打印错误信息
        fail_soup = BeautifulSoup(login_resp.text, 'html.parser')
        err_msg = fail_soup.find(id="showErrorTip")
        if err_msg:
            print(f"    提示: {err_msg.text.strip()}")
        return None