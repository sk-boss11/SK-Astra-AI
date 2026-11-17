from PIL import Image
from io import BytesIO
import base64
import uuid
from flask import Flask, request, jsonify, render_template_string
import os
import requests
import time

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
os.makedirs("static/generated", exist_ok=True)


def post_with_retry(url, **kwargs):
    for attempt in range(3):
        response = requests.post(url, **kwargs)

        if response.status_code not in (429, 500, 502, 503, 504):
            return response

        if attempt < 2:
            time.sleep(2 * (attempt + 1))

    return response


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

#imageEditor{margin-top:22px;padding:16px;background:#192235;border-radius:15px}
#imageEditor h2{color:#43d9ff}
#imageEditor input[type=file]{width:100%;padding:12px;background:#101522;border-radius:10px;color:white}
#imageEditor textarea{width:100%;margin-top:12px;min-height:85px}
#imagePreview{display:none;max-width:100%;max-height:350px;margin:15px auto;border-radius:12px}
#editedImage{display:none;max-width:100%;margin:15px auto;border-radius:12px}
#editStatus{white-space:pre-wrap;margin-top:12px}

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

<section id="imageEditor">
<h2>🎨 AI Image Editor</h2>
<p>ছবি নির্বাচন করুন এবং কী পরিবর্তন চান লিখুন।</p>
<form id="imageForm">
<input id="imageFile" type="file" accept="image/jpeg,image/png,image/webp" required>
<img id="imagePreview" alt="নির্বাচিত ছবি">
<textarea id="imagePrompt" placeholder="যেমন: ছবির ব্যাকগ্রাউন্ড সুন্দর করে দাও..." required></textarea>
<button id="editButton" type="submit">ছবি এডিট করুন</button>
</form>
<div id="editStatus"></div>
<img id="editedImage" alt="এডিট করা ছবি">
</section>

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

const imageForm=document.getElementById('imageForm');
const imageFile=document.getElementById('imageFile');
const imagePrompt=document.getElementById('imagePrompt');
const imagePreview=document.getElementById('imagePreview');
const editedImage=document.getElementById('editedImage');
const editButton=document.getElementById('editButton');
const editStatus=document.getElementById('editStatus');

imageFile.addEventListener('change',()=>{
 const file=imageFile.files[0];
 if(!file)return;
 imagePreview.src=URL.createObjectURL(file);
 imagePreview.style.display='block';
 editedImage.style.display='none';
 editStatus.textContent='';
});

imageForm.addEventListener('submit',async e=>{
 e.preventDefault();
 const file=imageFile.files[0];
 const prompt=imagePrompt.value.trim();
 if(!file||!prompt)return;

 const body=new FormData();
 body.append('image',file);
 body.append('prompt',prompt);
 editButton.disabled=true;
 editStatus.textContent='AI ছবি এডিট করছে... অপেক্ষা করুন।';
 editedImage.style.display='none';

 try{
  const response=await fetch('/edit-image',{method:'POST',body});
  const data=await response.json();
  if(!response.ok)throw new Error(data.error||'ছবি এডিট করা যায়নি');

  const imageUrl=data.image_url;
  editedImage.src=imageUrl;
  editedImage.style.display='block';
  editStatus.textContent='ছবি এডিট সম্পন্ন হয়েছে!';

  const save=confirm('এডিট করা ছবিটি আপনার ফোনে সেভ বা শেয়ার করতে চান?');
  if(save){
   const imageResponse=await fetch(imageUrl);
   const blob=await imageResponse.blob();
   const editedFile=new File([blob],'SK-Advanced-AI-Edited.png',{type:blob.type||'image/png'});

   if(navigator.share && navigator.canShare && navigator.canShare({files:[editedFile]})){
    await navigator.share({files:[editedFile],title:'SK Advanced AI Edited Image'});
   }else{
    const link=document.createElement('a');
    link.href=URL.createObjectURL(blob);
    link.download='SK-Advanced-AI-Edited.png';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(()=>URL.revokeObjectURL(link.href),60000);
    editStatus.textContent='ছবি ডাউনলোড শুরু হয়েছে। ফোনের Gallery/Photos-এ সেভ করুন।';
   }
  }
 }catch(error){
  if(error.name==='AbortError'){
   editStatus.textContent='শেয়ার বাতিল হয়েছে। এডিট করা ছবি ওয়েবসাইটে আছে।';
  }else{
   editStatus.textContent='সমস্যা: '+error.message;
  }
 }finally{
  editButton.disabled=false;
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



@app.route("/edit-image", methods=["POST"])
def edit_image():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "Gemini API Key সেট করা হয়নি"}), 503

    uploaded = request.files.get("image")
    prompt = str(request.form.get("prompt", "")).strip()

    if not uploaded:
        return jsonify({"error": "একটি ছবি নির্বাচন করুন"}), 400
    if not prompt:
        return jsonify({"error": "ছবি কীভাবে এডিট করতে চান লিখুন"}), 400
    if len(prompt) > 2000:
        return jsonify({"error": "এডিট নির্দেশনা ২০০০ অক্ষরের মধ্যে রাখুন"}), 400

    mime = uploaded.mimetype
    if mime not in ("image/jpeg", "image/png", "image/webp"):
        return jsonify({"error": "শুধু JPG, PNG অথবা WEBP ছবি দিন"}), 400

    try:
        raw = uploaded.read()
        if not raw:
            return jsonify({"error": "ছবিটি খালি"}), 400

        with Image.open(BytesIO(raw)) as img:
            if img.width * img.height > 25000000:
                return jsonify({"error": "ছবির আকার ২৫ মেগাপিক্সেলের বেশি"}), 400
            img.verify()

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-3.1-flash-image:generateContent"
        )

        response = post_with_retry(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "contents": [{
                    "parts": [
                        {"text": "Edit this image according to the user's "
                                 "instructions. Preserve the main subject "
                                 "unless asked otherwise. Instructions: " + prompt},
                        {"inlineData": {
                            "mimeType": mime,
                            "data": base64.b64encode(raw).decode("utf-8")
                        }}
                    ]
                }],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"]
                }
            },
            timeout=180
        )

        result = response.json()
        if response.status_code != 200:
            message = result.get("error", {}).get("message", "Image API Error")
            return jsonify({"error": message}), 502

        parts = (
            result.get("candidates", [{}])[0]
            .get("content", {}).get("parts", [])
        )

        for part in parts:
            data = part.get("inlineData") or part.get("inline_data")
            if data and data.get("data"):
                output = base64.b64decode(data["data"])
                output_mime = data.get("mimeType") or data.get("mime_type", "image/png")
                ext = {"image/jpeg": "jpg", "image/webp": "webp"}.get(
                    output_mime, "png"
                )
                filename = str(uuid.uuid4()) + "." + ext
                Path("static/generated").mkdir(parents=True, exist_ok=True)
                Path("static/generated", filename).write_bytes(output)

                return jsonify({
                    "reply": "ছবি এডিট সম্পন্ন হয়েছে",
                    "image_url": "/static/generated/" + filename
                })

        return jsonify({"error": "AI কোনো এডিট করা ছবি ফেরত দেয়নি"}), 502

    except Exception:
        app.logger.exception("Image editing failed")
        return jsonify({"error": "ছবি এডিট করা যায়নি। ছবিটি ও নির্দেশনা পরীক্ষা করুন।"}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
