# CSUAutoSelect (API版)

**中南大学自动选课工具 / CSU Course Auto-Selector**

> 🚀 **重构更新**：摒弃笨重的 Selenium 浏览器自动化，改用 Requests + AES 加密直接模拟登录协议。速度更快，无需配置浏览器驱动，内存占用极低。

当前重构：[@IAMNAVY](https://github.com/IAMNAVY)

原始作者：[@DavidHuang](https://github.com/CrazyDaveHDY)

二次更新：[@chichuxwx](https://github.com/chichuxwx)

---

本项目通过模拟 CSU 统一认证平台的登录协议（AES 加密），直接获取 Session 并对接教务系统接口，实现高效、轻量的自动抢课。

**⚠️ 警告：所有代码仅供学习交流使用，请遵守相关法律法规和校规校纪。禁止用于商业用途（如代抢）和非法用途。如作他用，所造成的一切后果和法律责任一概与本人无关。**

---

## ✨ 功能特性

* **协议登录**：无需打开浏览器，直接通过 HTTP 请求模拟登录，秒级响应。
* **轻量高效**：移除 Selenium 依赖，无需下载 `msedgedriver.exe`，极低内存占用，适合服务器或低配电脑运行。
* **自动加密**：内置与教务系统一致的 AES 密码加密算法。
* **双重模式**：支持“公选课”与“体育/专业课”两种选课接口。
* **配置灵活**：通过 `config.ini` 配置文件管理账号与课程。
* **自动轮询**：自动循环尝试抢课，直到成功或手动停止。

---

## 🛠 环境要求

需要 Python 3.x

由于移除了 Selenium，现在你需要安装以下轻量级依赖（特别是加密库和网页解析库）：

```bash
pip install requests pycryptodome beautifulsoup4
```

> **注意**：请务必安装 `pycryptodome` 而不是 `crypto`，以确保 AES 加密功能正常。

---

## 🚀 使用指南

### 1. 配置账号与课程

在项目根目录下找到或新建 `config.ini` 文件，并按照以下格式填写：

```ini
[config]
username = 8210xxxxxxx
password = 你的密码
#上面的密码是统一登陆的密码
#学期 202520262指的是2025-2026学年第二学期，根据自己要选的课的时间修改
time = 202520262

#公选 num1内填入要抢的课的数量  idn = xxxxxx  n为第几个id
num1 = 1
id1 = 011111

#专业课体育课  num2内填入要抢的课的数量  id_n = xxxxxx  n为第几个id  注意这里id后面有个下划线
num2=1
id_1 = 011111

```

### 2. 运行脚本

在命令行中进入项目目录，运行：

```bash
python main.py
```

### 3. 运行效果

* 自动完成登录并跳转至教务系统获取 Session。
* 开始对配置的课程 ID 进行轮询抢课，直到抢课成功。

---

## 🔍 如何找到 6 位课程 ID

要准确填写 `config.ini`，你需要找到课程的 ID。

1. **按教师查询法**：
进入 [中南大学教务系统课表查询页面](https://www.google.com/search?q=http://csujwc.its.csu.edu.cn/jiaowu/pkgl/llsykb/llsykb_find_jg0101.jsp%3Fxnxq01id%3D2024-2025-2%26init%3D1%26isview%3D0)，点击「按教师」按钮，输入学年学期和教师姓名。查询结果中，格子中央的数字编号即为课程 ID（通常为6位）。
2. **课表查询法**：
在教务系统的“全校课表查询”或“我的选课”页面中，查看网页源代码或通过 F12 开发者工具抓包，均可找到对应的 `jx0404id` 参数，即为课程 ID。

---

## 📝 常见问题

**Q: 运行报错 `ModuleNotFoundError: No module named 'Crypto'`**

A: 请执行 `pip uninstall crypto pycrypto` 清理旧库，然后执行 `pip install pycryptodome`。

**Q: 需要验证码吗？**

A: 目前版本的协议登录无法处理强制弹出的图片验证码。如果学校服务器开启了强制验证码（通常在输错密码多次或高频请求后），脚本可能会登录失败。建议稍后重试或在网页端手动登录一次以解除风控。
    Update: 2026/01/19 新版已可实现自动识别验证码并登录！！！


---

## ⚖️ 许可协议

CSUAutoSelect 遵循 [GPL-3.0 License](https://github.com/CrazyDaveHDY/CSUAutoSelect/blob/master/LICENSE) 开源协议。