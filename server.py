import os
import requests
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
API_URL = "https://api.groq.com/openai/v1/chat/completions"

HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SK Astra AI</title>
<style>
:root {
 --bg:#101827; --panel:#17243a; --chat:#202f43;
 --text:#ffffff; --muted:#aabbd2; --border:#30415c;
 --user:#2455a0; --accent:#3679e8;
}
body.light {
 --bg:#f1f5fb; --panel:#ffffff; --chat:#e4ebf5;
 --text:#17243a; --muted:#52647b; --border:#ccd7e6;
 --user:#c9ddff; --accent:#2867cf;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
 font-family:Arial,sans-serif;transition:.2s}
header{padding:14px;background:var(--panel);
 border-bottom:1px solid var(--border);text-align:center}
header h2{margin:0;color:#72aaff}
header p{margin:5px 0 0;color:var(--muted);font-size:13px}
.toolbar{display:flex;justify-content:center;gap:8px;
 flex-wrap:wrap;padding:10px;background:var(--panel)}
button{border:0;border-radius:10px;background:var(--accent);
 color:white;padding:10px 14px;font-size:14px;cursor:pointer}
button:disabled{opacity:.5}
#layout{max-width:1100px;margin:auto;display:flex;gap:12px;padding:12px}
#sidebar{width:230px;flex-shrink:0;background:var(--panel);
 border:1px solid var(--border);border-radius:12px;padding:10px;
 max-height:65vh;overflow-y:auto}
#historyList button{width:100%;text-align:left;margin-top:7px;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#historyList button.active{background:#174b99}
#main{flex:1;min-width:0}
#chat{height:58vh;overflow-y:auto;padding:12px;
 background:var(--bg);border:1px solid var(--border);border-radius:12px}
.msg{padding:13px 16px;margin:12px 0;border-radius:15px;
 line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere}
.user{background:var(--user);color:var(--text);margin-left:35px}
.ai{background:var(--chat);color:var(--text);margin-right:35px}
..bottom{
 padding:12px 0;
}
form{
 display:flex;
 flex-direction:row;
 align-items:stretch;
 gap:8px;
}
textarea{
 flex:1;
 min-width:0;
 resize:vertical;
 border:1px solid var(--border);
 border-radius:12px;
 padding:13px;
 background:var(--panel);
 color:var(--text);
 font-size:16px;
 min-height:48px;
}
form button{
 flex-shrink:0;
 min-width:85px;
}
textarea{flex:1;resize:vertical;border:1px solid var(--border);
 border-radius:12px;padding:13px;background:var(--panel);
 color:var(--text);font-size:16px;min-height:48px}
.small{font-size:12px;color:var(--muted);text-align:center}
@media(max-width:650px){
 #layout{display:block;padding:8px}
 #sidebar{width:100%;max-height:125px;margin-bottom:10px}
 #historyList{display:flex;gap:6px;overflow-x:auto}
 #historyList button{min-width:130px}
 #chat{height:54vh}
 form{flex-wrap:wrap}
 textarea{width:100%;flex-basis:100%}
}
</style>
</head>
<body>
<header>
<h2>✦ SK Astra AI</h2>
<p>Your Personal AI Assistant • Created by SK BOSS</p>
</header>

<div class="toolbar">
<button onclick="newChat()">＋ New Chat</button>
<button onclick="toggleTheme()" id="themeBtn">☀️ Light Mode</button>
<button onclick="startVoice()">🎤 Voice</button>
<button onclick="stopSpeaking()">🔇 Stop Voice</button>
</div>

<div id="layout">
<aside id="sidebar">
<strong>💬 Chat History</strong>
<div id="historyList"></div>
</aside>

<main id="main">
<div id="chat">
<div class="msg ai">আসসালামু আলাইকুম! আমি SK Astra AI। কীভাবে সাহায্য করতে পারি?</div>
</div>
<div class="bottom">
<form id="form">
<textarea id="input" placeholder="এখানে মেসেজ লিখুন..." rows="2"></textarea>
<button id="send">Send</button>
</form>
</div>
<div class="small">SK Astra AI • Powered by Groq</div>
</main>
</div>

<script>
const chat=document.getElementById('chat');
const form=document.getElementById('form');
const input=document.getElementById('input');
const send=document.getElementById('send');
const historyList=document.getElementById('historyList');

let conversations=[];
let currentId=null;
let messages=[];

function saveData(){
 sessionStorage.setItem('skastra_chats',JSON.stringify(conversations));
}

function addMessage(text,role){
 const div=document.createElement('div');
 div.className='msg '+role;
 div.textContent=text;
 chat.appendChild(div);
 chat.scrollTop=chat.scrollHeight;
}

function renderMessages(){
 chat.innerHTML='';
 if(messages.length===0){
  addMessage('আসসালামু আলাইকুম! আমি SK Astra AI। কীভাবে সাহায্য করতে পারি?','ai');
  return;
 }
 messages.forEach(m=>{
  addMessage(m.content,m.role==='user'?'user':'ai');
 });
}

function renderHistory(){
 historyList.innerHTML='';
 conversations.slice().reverse().forEach(c=>{
  const b=document.createElement('button');
  b.textContent=c.title || 'New Chat';
  if(c.id===currentId)b.classList.add('active');
  b.onclick=()=>openChat(c.id);
  historyList.appendChild(b);
 });
}

function saveCurrent(){
 if(!currentId || messages.length===0)return;
 const c=conversations.find(x=>x.id===currentId);
 if(!c)return;
 c.messages=messages;
 c.title=messages.find(x=>x.role==='user')?.content.slice(0,35)||'New Chat';
 saveData();
 renderHistory();
}

function newChat(){
 saveCurrent();
 currentId=String(Date.now());
 messages=[];
 conversations.push({
  id:currentId,title:'New Chat',messages:[]
 });
 saveData();
 renderMessages();
 renderHistory();
 input.focus();
}

function openChat(id){
 saveCurrent();
 const c=conversations.find(x=>x.id===id);
 if(!c)return;
 currentId=id;
 messages=c.messages||[];
 renderMessages();
 renderHistory();
}

function loadChats(){
 try{
  conversations=JSON.parse(sessionStorage.getItem('skastra_chats')||'[]');
  if(!Array.isArray(conversations))conversations=[];
 }catch(e){conversations=[]}

 if(conversations.length){
  const c=conversations[conversations.length-1];
  currentId=c.id;
  messages=c.messages||[];
 }else{
  currentId=String(Date.now());
  conversations.push({id:currentId,title:'New Chat',messages:[]});
 }
 renderMessages();
 renderHistory();
}

function toggleTheme(){
 document.body.classList.toggle('light');
 const light=document.body.classList.contains('light');
 localStorage.setItem('skastra_theme',light?'light':'dark');
 document.getElementById('themeBtn').textContent=
  light?'🌙 Dark Mode':'☀️ Light Mode';
}

function loadTheme(){
 if(localStorage.getItem('skastra_theme')==='light'){
  document.body.classList.add('light');
  document.getElementById('themeBtn').textContent='🌙 Dark Mode';
 }
}

function stopSpeaking(){
 if('speechSynthesis' in window)speechSynthesis.cancel();
}

function speak(text){
 if(!('speechSynthesis' in window))return;
 stopSpeaking();
 const utterance=new SpeechSynthesisUtterance(text);
 utterance.lang=/[\\u0980-\\u09FF]/.test(text)?'bn-BD':'en-US';
 speechSynthesis.speak(utterance);
}

function startVoice(){
 const SpeechRecognition=window.SpeechRecognition||
  window.webkitSpeechRecognition;
 if(!SpeechRecognition){
  alert('এই ব্রাউজারে Voice Input সমর্থিত নয়। Chrome ব্যবহার করে দেখুন।');
  return;
 }
 const recognition=new SpeechRecognition();
 recognition.lang='bn-BD';
 recognition.interimResults=false;
 recognition.onresult=e=>{
  input.value=e.results[0][0].transcript;
  input.focus();
 };
 recognition.onerror=()=>alert('মাইক্রোফোন অনুমতি ও ব্রাউজার সেটিং পরীক্ষা করুন।');
 recognition.start();
}

form.addEventListener('submit',async e=>{
 e.preventDefault();
 const message=input.value.trim();
 if(!message)return;

 messages.push({role:'user',content:message});
 addMessage(message,'user');
 input.value='';
 send.disabled=true;
 send.textContent='...';

 try{
  const response=await fetch('/api/chat',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({messages:messages})
  });
  const data=await response.json();
  if(!response.ok)throw new Error(data.error||'Request failed');

  messages.push({role:'assistant',content:data.reply});
  addMessage(data.reply,'ai');
  saveCurrent();
  speak(data.reply);
 }catch(err){
  addMessage('সমস্যা: '+err.message,'ai');
 }finally{
  send.disabled=false;
  send.textContent='Send';
 }
});

loadTheme();
loadChats();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "SK Astra AI"})

@app.route("/api/chat", methods=["POST"])
def chat():
    if not API_KEY:
        return jsonify({"error": "GROQ_API_KEY সেট করা হয়নি।"}), 503

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "মেসেজ পাঠান।"}), 400

    safe_messages = []
    for item in messages[-30:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        safe_messages.append({
            "role": role,
            "content": content[:10000]
        })

    if not safe_messages:
        return jsonify({"error": "সঠিক মেসেজ পাওয়া যায়নি।"}), 400

    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "My name is SK Astra AI. "
                    "I was created by SK BOSS. "
                    "If asked my name, say: My name is SK Astra AI. "
                    "If asked who created you, say: I was created by SK BOSS. "
                    "Never say I created SK BOSS. "
                    "When replying in Bengali, say: আমার নাম SK Astra AI, এবং আমাকে তৈরি করেছেন SK BOSS। "
                    "Groq is only my API provider. "
                    "Always reply in the user's language, clearly and politely."
                )
            }
        ] + safe_messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=90
        )

        if response.status_code != 200:
            return jsonify({
                "error": "AI API Error: " + response.text[:500]
            }), 502

        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except requests.Timeout:
        return jsonify({
            "error": "AI উত্তর দিতে বেশি সময় নিচ্ছে। আবার চেষ্টা করুন।"
        }), 504
    except requests.RequestException:
        return jsonify({"error": "ইন্টারনেট সংযোগ পরীক্ষা করুন।"}), 502
    except (KeyError, IndexError, ValueError):
        return jsonify({
            "error": "AI থেকে সঠিক উত্তর পাওয়া যায়নি।"
        }), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
