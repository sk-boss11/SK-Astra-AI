from io import BytesIO
import base64
import uuid
from flask import Flask, request, jsonify, render_template_string
import os
import requests
import time

app = Flask(__name__)
os.makedirs("static/generated", exist_ok=True)


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
#form{display:flex;gap:8px;margin-top:10px}
#composer{margin-top:12px;padding:12px;background:#192235;border:1px solid #46536a;border-radius:16px}
#toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#toolbar button{padding:9px 13px}
#toolbar .active{background:#155e75;color:white}
#toolbar select{background:#101522;color:white;border:1px solid #46536a;border-radius:9px;padding:9px;max-width:115px}
#toolbar button:disabled{opacity:.5}
#form textarea{min-width:0}
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
<div id="composer">
<div id="toolbar">
<button type="button" class="active">💬 Chat</button>
<select id="modelSelect" aria-label="AI Model">
<option value="auto">Auto</option>
<option value="gemini">Gemini</option>
</select>
<button type="button" id="voiceButton">🎙️ Voice</button>
<select id="voiceLanguage" aria-label="ভাষা">
<option value="bn-BD">বাংলা</option>
<option value="en-US">English</option>
</select>
<button type="button" id="speakToggle">🔊 Voice Reply: OFF</button>
</div>
<form id="form">
<textarea id="message" rows="2"
placeholder="এখানে লিখুন..." required></textarea>
<button id="send" type="submit">Send</button>
</form>
</div>


</div>
<script>
const chat=document.getElementById('chat');
const form=document.getElementById('form');
const input=document.getElementById('message');
const send=document.getElementById('send');
const modelSelect=document.getElementById('modelSelect');
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
   body:JSON.stringify({message,history,model:modelSelect.value})
  });

  const data=await response.json();

  if(!response.ok) throw new Error(data.error||'API Error');

  loading.textContent=data.reply;
    speakReply(data.reply);
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

const voiceButton=document.getElementById('voiceButton');
const voiceLanguage=document.getElementById('voiceLanguage');
const speakToggle=document.getElementById('speakToggle');
let voiceReplyEnabled=false;
let recognition=null;
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;

if(SpeechRecognition){
 recognition=new SpeechRecognition();
 recognition.interimResults=false;
 recognition.maxAlternatives=1;
 recognition.onstart=()=>{
  voiceButton.textContent='🛑 Stop Voice';
  voiceButton.classList.add('active');
 };
 recognition.onresult=event=>{
  input.value=event.results[0][0].transcript;
  input.focus();
 };
 recognition.onerror=event=>{
  addMessage('Voice সমস্যা: '+event.error,'ai');
 };
 recognition.onend=()=>{
  voiceButton.textContent='🎙️ Voice';
  voiceButton.classList.remove('active');
 };
 voiceButton.addEventListener('click',()=>{
  if(voiceButton.classList.contains('active')){
   recognition.stop();
  }else{
   recognition.lang=voiceLanguage.value;
   try{recognition.start();}
   catch(error){addMessage('Voice চালু করা যায়নি। আবার চেষ্টা করুন।','ai');}
  }
 });
}else{
 voiceButton.disabled=true;
 voiceButton.title='এই ব্রাউজারে Voice Recognition সমর্থিত নয়';
}

speakToggle.addEventListener('click',()=>{
 voiceReplyEnabled=!voiceReplyEnabled;
 speakToggle.textContent=voiceReplyEnabled?'🔊 Voice Reply: ON':'🔊 Voice Reply: OFF';
 if(!voiceReplyEnabled && 'speechSynthesis' in window){
  window.speechSynthesis.cancel();
 }
});

function speakReply(text){
 if(!voiceReplyEnabled || !('speechSynthesis' in window))return;
 window.speechSynthesis.cancel();
 const utterance=new SpeechSynthesisUtterance(text);
 utterance.lang=voiceLanguage.value;
 window.speechSynthesis.speak(utterance);
}

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
    selected_model = str(data.get("model", "auto")).lower()

    if selected_model not in ("auto", "gemini"):
        return jsonify({"error": "নির্বাচিত AI Model সমর্থিত নয়"}), 400

    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "বার্তা লিখুন"}), 400

    search_terms = (
        "latest", "news", "today", "current", "recent",
        "search", "online", "internet", "web", "price",
        "weather", "update", "breaking",
        "সর্বশেষ", "আজকের", "আজ", "খবর", "সংবাদ",
        "বর্তমান", "সাম্প্রতিক", "অনলাইন", "ইন্টারনেট",
        "খুঁজে", "সার্চ", "দাম", "আবহাওয়া", "আপডেট"
    )
    needs_search = any(term in message.lower() for term in search_terms)

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
        "models/gemini-flash-lite-latest:generateContent"
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
                        "text": (
                            "You are SK Advanced AI, an intelligent, helpful, "
                            "friendly and reliable multilingual AI assistant. "
                            "Understand and respond in the user's language. "
                            "Support Bengali, English, Arabic, Hindi, Urdu, "
                            "Chinese, Japanese, Korean and other languages "
                            "supported by your model. Match the user's language "
                            "unless they request another language. "
                            "Help with programming, debugging, mathematics, "
                            "science, education, research, writing, translation, "
                            "summarization, planning and general knowledge. "
                            "Explain difficult topics clearly and step by step "
                            "when useful. Provide accurate, practical answers. "
                            "Never invent facts, sources, links or current news. "
                            "Clearly say when you are uncertain or when information "
                            "may be outdated. Be respectful, concise when appropriate, "
                            "and ask a clarifying question when necessary. "
                            "Your name is SK Advanced AI."
                        )
                    }]
                },
                "contents": contents,
                "tools": [{"google_search": {}}] if needs_search else [],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            },
            timeout=60
        )

        result = response.json()

        if response.status_code == 429:
            return jsonify({
                "error": (
                    "SK Advanced AI-এর Gemini API ব্যবহারের সীমা আপাতত শেষ "
                    "হয়েছে। কিছুক্ষণ পরে আবার চেষ্টা করুন। প্রয়োজনে Google AI "
                    "Studio-তে API quota ও billing পরীক্ষা করুন।"
                )
            }), 429

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

        grounding = candidates[0].get("groundingMetadata", {})
        sources = []
        seen_urls = set()

        for chunk in grounding.get("groundingChunks", []):
            web = chunk.get("web", {})
            uri = web.get("uri", "")
            if uri.startswith("https://") and uri not in seen_urls:
                seen_urls.add(uri)
                sources.append({
                    "title": web.get("title") or "ওয়েব উৎস",
                    "url": uri
                })

        return jsonify({
            "reply": reply or "উত্তর পাওয়া যায়নি",
            "sources": sources
        })

    except requests.RequestException:
        return jsonify({"error": "Gemini সার্ভারের সঙ্গে সংযোগ হয়নি"}), 502



if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
