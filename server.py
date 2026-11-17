from flask import Flask, request, jsonify, render_template_string
import os
import requests

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SK Advanced AI</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;background:#101522;color:white;
 font-family:Arial,sans-serif;
}
.container{max-width:850px;margin:auto;padding:15px}
header{text-align:center;padding:15px}
header h1{color:#43d9ff}
#chat{
 height:68vh;overflow-y:auto;
 background:#192235;border-radius:15px;padding:15px;
}
.msg{
 padding:13px;margin:10px 0;border-radius:12px;
 line-height:1.6;white-space:pre-wrap;
 overflow-wrap:anywhere;
}
.user{background:#155e75;margin-left:30px}
.ai{background:#29364e;margin-right:30px}
form{display:flex;gap:8px;margin-top:15px}
textarea{
 flex:1;resize:none;padding:14px;
 border-radius:12px;border:1px solid #46536a;
 background:#192235;color:white;font-size:16px;
}
button{
 background:#06b6d4;color:#00131a;
 border:0;border-radius:12px;
 padding:12px 20px;font-weight:bold;
}
button:disabled{opacity:.5}
</style>
</head>
<body>
<div class="container">
<header>
<h1>SK Advanced AI</h1>
<p>Your Personal AI Assistant</p>
</header>
<div id="chat">
<div class="msg ai">আসসালামু আলাইকুম! আমি SK Advanced AI। কীভাবে সাহায্য করতে পারি?</div>
</div>
<form id="form">
<textarea id="message" rows="2"
placeholder="এখানে লিখুন..." required></textarea>
<button id="send" type="submit">Send</button>
</form>
</div>
<script>
const chat=document.getElementById('chat');
const form=document.getElementById('form');
const input=document.getElementById('message');
const send=document.getElementById('send');
let history=[];

function addMessage(text,type){
 const div=document.createElement('div');
 div.className='msg '+type;
 div.textContent=text;
 chat.appendChild(div);
 chat.scrollTop=chat.scrollHeight;
 return div;
}

form.addEventListener('submit',async e=>{
 e.preventDefault();
 const message=input.value.trim();
 if(!message)return;

 addMessage(message,'user');
 input.value='';
 send.disabled=true;

 const loading=addMessage('উত্তর তৈরি হচ্ছে...','ai');

 try{
  const response=await fetch('/chat',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({message,history})
  });

  const data=await response.json();

  if(!response.ok) throw new Error(data.error||'API Error');

  loading.textContent=data.reply;
  history.push(
   {role:'user',parts:[{text:message}]},
   {role:'model',parts:[{text:data.reply}]}
  );
 }catch(error){
  loading.textContent='সমস্যা: '+error.message;
 }finally{
  send.disabled=false;
  input.focus();
 }
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "বার্তা লিখুন"}), 400

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({"error": "Gemini API Key সেট করা হয়নি"}), 503

    history = data.get("history", [])
    contents = []

    if isinstance(history, list):
        for item in history[-20:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            parts = item.get("parts")
            if role in ("user", "model") and isinstance(parts, list):
                contents.append({"role": role, "parts": parts})

    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash:generateContent"
    )

    try:
        response = requests.post(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "systemInstruction": {
                    "parts": [{
                        "text": "তুমি SK Advanced AI। তুমি একজন সহায়ক, "
                                "বন্ধুসুলভ AI assistant। বাংলায় প্রশ্ন "
                                "করলে বাংলায় উত্তর দেবে।"
                    }]
                },
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            },
            timeout=60
        )

        result = response.json()

        if response.status_code != 200:
            error = result.get("error", {}).get(
                "message", "Gemini API Error"
            )
            return jsonify({"error": error}), 502

        candidates = result.get("candidates", [])
        if not candidates:
            return jsonify({"error": "AI কোনো উত্তর দেয়নি"}), 502

        parts = candidates[0].get("content", {}).get("parts", [])
        reply = "\n".join(
            part["text"] for part in parts if "text" in part
        )

        return jsonify({"reply": reply or "উত্তর পাওয়া যায়নি"})

    except requests.RequestException:
        return jsonify({"error": "Gemini সার্ভারের সঙ্গে সংযোগ হয়নি"}), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
