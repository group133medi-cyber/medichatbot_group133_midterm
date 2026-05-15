from flask import Flask, render_template, request, jsonify, session
import json
import os
import random
from huggingface_hub import InferenceClient

app = Flask(__name__)
app.secret_key = "super_secret_key"  

client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
)

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct:fastest"


base_path = os.path.dirname(__file__)
json_path = os.path.join(base_path, "medical_data1.json")

with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"].lower().strip()

    
    if "history" not in session:
        session["history"] = []

    
    session["history"].append({
        "role": "user",
        "content": user_message
    })

    
    reply = get_response(session["history"])

    
    session["history"].append({
        "role": "assistant",
        "content": reply
    })

    
    session["history"] = session["history"][-6:]

    return jsonify({"reply": reply})



def get_response(history):
    # Combine last few user messages
    recent_text = " ".join(
        [h["content"] for h in history if h["role"] == "user"]
    )

    msg = recent_text
    matched = []

    
    for symptom, info in data.items():
        for keyword in info.get("keywords", []):
            if keyword in msg:
                matched.append(info)
                break

    
    if not matched:
        return get_ai_response(history)

    
    for m in matched:
        if m.get("severity") == "high":
            return (
                f"⚠️ {m['description']}\n\n"
                f"👉 {m['advice']}\n\n"
                f"Please seek immediate medical attention."
            )

    
    reply = "Based on your symptoms so far:\n\n"

    for m in matched:
        reply += f"• {m['description']}\n"
        reply += f"Advice: {m['advice']}\n\n"

    
    follow_ups = []
    for m in matched:
        if "follow_up" in m:
            follow_ups.extend(m["follow_up"])

    if follow_ups:
        reply += "❓ " + random.choice(follow_ups)

    return reply.strip()



def get_ai_response(history):
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical assistant. Provide general health information only. "
                        "Do not give diagnoses or prescriptions. If symptoms are serious, "
                        "advise consulting a doctor."
                    )
                }
            ] + history[-6:], 
        )

        return completion.choices[0].message["content"]

    except Exception as e:
        print("API Error:", e)
        return "Sorry, I'm having trouble responding right now. Please try again."



@app.route("/reset", methods=["GET"])
def reset():
    session.clear()
    return jsonify({"message": "Conversation reset"})



if __name__ == "__main__":
    app.run(debug=True)
