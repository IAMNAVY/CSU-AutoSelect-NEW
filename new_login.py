# filename: new_login.py
import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import random
import time
import ddddocr  # 导入 ddddocr

# ================= 配置区域 =================
LOGIN_URL = "https://ca.csu.edu.cn/authserver/login?service=http%3A%2F%2Fcsujwc.its.csu.edu.cn%2Fsso.jsp"
CAPTCHA_CHECK_URL = "https://ca.csu.edu.cn/authserver/checkNeedCaptcha.htl"
CAPTCHA_IMG_URL = "https://ca.csu.edu.cn/authserver/getCaptcha.htl"
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

def _get_timestamp():
    return int(time.time() * 1000)

def check_need_captcha(session, username):
    """检测是否需要验证码"""
    params = {"username": username, "_": _get_timestamp()}
    try:
        resp = session.get(CAPTCHA_CHECK_URL, params=params)
        if resp.status_code == 200:
            return resp.json().get("isNeed", False)
    except Exception:
        pass
    return False

def get_captcha_bytes(session):
    """获取验证码图片二进制数据"""
    try:
        url = f"{CAPTCHA_IMG_URL}?{_get_timestamp()}"
        resp = session.get(url)
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        print(f"验证码下载失败: {e}")
    return None

def login(username, password):
    """
    执行登录流程（自动识别验证码 + Cookie 修复）
    """
    # 初始化 OCR，show_ad=False 关闭广告输出
    print("[*] 正在加载 OCR 模型...")
    ocr = ddddocr.DdddOcr(show_ad=False)
    print("[*] OCR 模型加载完成")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1"
    })

    retry_count = 0
    max_retries = 10  # 防止无限死循环

    while retry_count < max_retries:
        retry_count += 1
        print(f"\n[*] [Login] 第 {retry_count} 次尝试登录...")
        
        try:
            resp = session.get(LOGIN_URL)
            resp.raise_for_status()
        except Exception as e:
            print(f"[!] 连接服务器失败: {e}")
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. 获取 execution 和 salt
        execution_input = soup.find('input', {'name': 'execution'})
        if not execution_input:
            if "Log Out" in resp.text or "退出" in resp.text:
                print("[+] 检测到已处于登录状态")
                return session
            print("[!] 错误: 无法解析页面参数 (execution丢失)")
            return None
        execution = execution_input['value']

        salt_input = soup.find('input', {'id': 'pwdEncryptSalt'})
        if not salt_input:
            salt_input = soup.find('input', {'id': 'pwdDefaultEncryptSalt'})
        salt = salt_input['value'] if salt_input else None

        # 2. 检测并自动识别验证码
        captcha_code = ""
        if check_need_captcha(session, username):
            print("[*] 系统提示：需要验证码，正在自动获取并识别...")
            img_bytes = get_captcha_bytes(session)
            if img_bytes:
                # === ddddocr 自动识别 ===
                captcha_code = ocr.classification(img_bytes)
                print(f"[*] OCR自动识别结果: {captcha_code}")
            else:
                print("[x] 验证码获取失败，尝试空值提交...")

        # 3. 加密密码
        encrypted_pw = encrypt_password(password, salt)

        # 4. 发送登录请求
        data = {
            "username": username,
            "password": encrypted_pw,
            "captcha": captcha_code,
            "_eventId": "submit",
            "cllt": "userNameLogin",
            "dllt": "generalLogin",
            "lt": "",
            "execution": execution
        }

        login_resp = session.post(LOGIN_URL, data=data, allow_redirects=False)

        if login_resp.status_code == 302:
            redirect_url = login_resp.headers.get('Location')
            print(f"[+] [Login] 认证通过，跳转中: {redirect_url}")
            
            # 跟随跳转
            session.get(redirect_url)
            
            # ================= [Cookie 冲突修复] =================
            cookies_to_keep = []
            for cookie in session.cookies:
                # 剔除 CAS 的 JSESSIONID
                if cookie.name == 'JSESSIONID' and ('ca.csu' in cookie.domain or 'authserver' in cookie.domain):
                    continue
                cookies_to_keep.append(cookie)
            
            session.cookies.clear()
            for cookie in cookies_to_keep:
                session.cookies.set_cookie(cookie)
                
            print("[+] [Login] Session Cookie 修复完成，会话已建立")
            return session
            
        else:
            # 登录失败，检查原因
            fail_soup = BeautifulSoup(login_resp.text, 'html.parser')
            err_msg = "未知错误"
            err_elem = fail_soup.find(id="showErrorTip") or fail_soup.find('span', {'id': 'msg'})
            if err_elem:
                err_msg = err_elem.text.strip()
            
            print(f"[x] [Login] 登录失败: {err_msg}")
            
            if "验证码" in err_msg:
                print("[*] 验证码识别错误，1秒后自动重试...")
                time.sleep(1)
                continue # 重新循环
            else:
                # 密码错误，直接返回None
                return None
    
    print("[!] 超过最大重试次数，登录失败")
    return None