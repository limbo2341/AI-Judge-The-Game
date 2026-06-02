import json, logging, os, urllib.request, asyncio
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logger = logging.getLogger(__name__)
async def _gemini_request(prompt: str) -> str:
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    def do_request():
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, do_request)
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
async def generate_case(case_type: str) -> dict:
    prompt = f"""Ти — генератор юридичних ігор. Згенеруй унікальну правову ситуацію в Україні категорії: {case_type}. Поверни ТІЛЬКИ JSON без markdown:\n{{"story": "текст справи 3-5 речень", "hidden_article": "стаття та правильне рішення"}}"""
    try:
        text = await _gemini_request(prompt)
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"generate_case error: {e}")
        return {"story": "Справа №001. Громадянин Петренко звинувачується у дрібному хуліганстві. Поліція склала протокол.", "hidden_article": "Стаття 173 КУпАП — Дрібне хуліганство."}
async def character_dialogue(character_type: str, case_story: str, history: list, user_message: str) -> str:
    history_text = ""
    for msg in history:
        role = "Суддя" if msg["role"] == "user" else character_type
        history_text += f"{role}: {msg['content']}\n"
    prompt = f"""Ти граєш роль {character_type} у справі: {case_story}\nПопередній діалог:\n{history_text}\nСуддя: {user_message}\nВідповідай від імені {character_type}, коротко 2-4 речення, реалістично."""
    try:
        return await _gemini_request(prompt)
    except Exception as e:
        logger.error(f"dialogue error: {e}")
        return "Вибачте, мені потрібен адвокат."
async def evaluate_verdict(case_story: str, hidden_article: str, user_verdict: str) -> dict:
    prompt = f"""Ти Верховний Суддя. Оціни рішення гравця.\nСправа: {case_story}\nПравильна стаття: {hidden_article}\nРішення гравця: {user_verdict}\nОціни від 1 до 3. Поверни ТІЛЬКИ JSON без markdown:\n{{"score": 2, "feedback": "розбір українською"}}"""
    try:
        text = await _gemini_request(prompt)
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"verdict error: {e}")
        return {"score": 2, "feedback": "Технічна помилка. Вирок прийнято умовно."}
