import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from telethon import TelegramClient

app = Flask(__name__)
app.secret_key = "SUPERSECRET"

SESSIONS = {}  # Store active clients in-memory

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/send_phone", methods=["POST"])
def send_phone():
    api_id = request.form["api_id"]
    api_hash = request.form["api_hash"]
    phone = request.form["phone"]

    client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
    SESSIONS[phone] = client

    async def start():
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)

    client.loop.run_until_complete(start())
    session["phone"] = phone
    return redirect(url_for("otp"))

@app.route("/otp")
def otp():
    return render_template("otp.html")

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    phone = session.get("phone")
    code = request.form["otp"]
    client = SESSIONS[phone]

    async def finish():
        await client.sign_in(phone, code)

    client.loop.run_until_complete(finish())
    return redirect(url_for("chats"))

@app.route("/chats")
def chats():
    return render_template("chats.html")

@app.route("/api/chats")
def api_chats():
    phone = session.get("phone")
    client = SESSIONS[phone]

    async def fetch_chats():
        dialogs = await client.get_dialogs()
        return [{"id": d.id, "name": d.name} for d in dialogs]

    data = client.loop.run_until_complete(fetch_chats())
    return jsonify(data)

@app.route("/api/messages/<int:chat_id>")
def api_messages(chat_id):
    phone = session.get("phone")
    client = SESSIONS[phone]

    async def fetch_messages():
        msgs = await client.get_messages(chat_id, limit=20)
        return [{"from": m.sender_id, "text": m.text} for m in msgs]

    data = client.loop.run_until_complete(fetch_messages())
    return jsonify(data)

@app.route("/api/send", methods=["POST"])
def api_send():
    phone = session.get("phone")
    chat_id = request.form["chat_id"]
    text = request.form["text"]
    client = SESSIONS[phone]

    async def send_msg():
        await client.send_message(int(chat_id), text)

    client.loop.run_until_complete(send_msg())
    return "OK"

if __name__ == "__main__":
    os.makedirs("sessions", exist_ok=True)
    app.run(host="0.0.0.0", port=8080)
