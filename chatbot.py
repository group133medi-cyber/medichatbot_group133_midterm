import json
import os
import random
import streamlit as st
from huggingface_hub import InferenceClient

# ---------------- HUGGING FACE CLIENT ----------------

client = InferenceClient(
    api_key=st.secrets["HF_TOKEN"]
)

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct:fastest"

# ---------------- LOAD MEDICAL DATA ----------------

base_path = os.path.dirname(__file__)

json_path = os.path.join(
    base_path,
    "medical_data.json"
)

with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# ---------------- MAIN CHATBOT FUNCTION ----------------

def get_response(history):

    # ---------------- SYMPTOM MEMORY ----------------

    if "symptom_memory" not in st.session_state:

        st.session_state.symptom_memory = []

    # ---------------- COMBINE USER MESSAGES ----------------

    recent_text = " ".join(
        [
            h["content"]
            for h in history
            if isinstance(h, dict)
            and h.get("role") == "user"
        ]
    )

    msg = recent_text.lower()

    matched = []

    combo_matches = []

    total_score = 0

    emergency_detected = False

    possible_conditions = []

    # ---------------- SYMPTOM MATCHING ----------------

    for symptom, info in data["symptoms"].items():

        for keyword in info.get("keywords", []):

            if keyword.lower() in msg:

                matched.append(info)

                total_score += info.get("score", 0)

                if info.get("emergency"):

                    emergency_detected = True

                possible_conditions.extend(
                    info.get("possible_conditions", [])
                )

                # SAVE SYMPTOM MEMORY
                if symptom not in st.session_state.symptom_memory:

                    st.session_state.symptom_memory.append(symptom)

                break

    # ---------------- COMBINATION ANALYSIS ----------------

    memory = set(st.session_state.symptom_memory)

    for combo in data["symptom_combinations"]:

        combo_symptoms = set(combo["symptoms"])

        if combo_symptoms.issubset(memory):

            combo_matches.append(combo)

            total_score += combo.get("score_bonus", 0)

            if combo.get("emergency"):

                emergency_detected = True

    # ---------------- AI FALLBACK ----------------

    if not matched and not combo_matches:

        return get_ai_response(history)

    # ---------------- DETERMINE OVERALL SEVERITY ----------------

    if total_score >= 10:

        overall_severity = "🔴 Critical"

    elif total_score >= 5:

        overall_severity = "🟠 Moderate"

    else:

        overall_severity = "🟢 Mild"

    # ---------------- EMERGENCY RESPONSE ----------------

    if emergency_detected:

        emergency_reply = (
            "🚨 EMERGENCY SYMPTOMS DETECTED\n\n"
        )

        for m in matched:

            if m.get("emergency"):

                emergency_reply += (
                    f"⚠️ {m['description']}\n"
                    f"👉 {m['advice']}\n\n"
                )

        for combo in combo_matches:

            if combo.get("emergency"):

                emergency_reply += (
                    f"🧠 {combo['condition']}\n"
                    f"👉 {combo['advice']}\n\n"
                )

        emergency_reply += (
            "Please seek immediate medical attention."
        )

        return emergency_reply

    # ---------------- BUILD RESPONSE ----------------

    reply = f"📊 Overall Severity: {overall_severity}\n\n"

    reply += "🩺 Detected Symptoms:\n\n"

    for m in matched:

        reply += (
            f"• {m['description']}\n"
        )

        reply += (
            f"👉 Advice: {m['advice']}\n\n"
        )

    # ---------------- POSSIBLE CONDITIONS ----------------

    unique_conditions = list(
        set(possible_conditions)
    )

    if unique_conditions:

        reply += "🧠 Possible Related Conditions:\n\n"

        for condition in unique_conditions[:5]:

            reply += f"• {condition}\n"

        reply += "\n"

    # ---------------- SYMPTOM COMBINATION OUTPUT ----------------

    if combo_matches:

        reply += "🔍 Symptom Combination Analysis:\n\n"

        for combo in combo_matches:

            reply += (
                f"🧠 {combo['condition']}\n"
            )

            reply += (
                f"👉 {combo['advice']}\n\n"
            )

    # ---------------- FOLLOW-UP QUESTIONS ----------------

    follow_ups = []

    for m in matched:

        if "follow_up" in m:

            follow_ups.extend(
                m["follow_up"]
            )

    if follow_ups:

        reply += "❓ Follow-up Question:\n\n"

        reply += random.choice(follow_ups)

    return reply.strip()

# ---------------- AI FALLBACK ----------------

def get_ai_response(history):

    try:

        completion = client.chat.completions.create(

            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI medical assistant chatbot.\n\n"

                        "Responsibilities:\n"
                        "- Provide general medical guidance\n"
                        "- Ask follow-up questions\n"
                        "- Explain symptoms clearly\n"
                        "- Never provide prescriptions\n"
                        "- Never claim certainty in diagnosis\n"
                        "- Advise doctor consultation when needed\n"
                        "- If symptoms appear severe, "
                        "recommend immediate medical attention."
                    )
                }
            ] + history[-10:]
        )

        return completion.choices[0].message.content

    except Exception as e:

        print("API Error:", e)

        return (
            "Sorry, I'm having trouble responding right now. "
            "Please try again."
        )