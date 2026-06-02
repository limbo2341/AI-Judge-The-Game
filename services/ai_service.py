import json, logging, os, urllib.request, urllib.error, asyncio
logger = logging.getLogger(__name__)

async def _gemini(prompt: str) -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    body = json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.9}}).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"}, method="POST")
    def do():
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    data = await asyncio.get_event_loop().run_in_executor(None, do)
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

async def generate_case(case_type: str) -> dict:
    prompt = f"""Ти генератор юридичних справ для гри-симулятора судді України.
Згенеруй унікальну реалістичну справу категорії {case_type}.
Придумай РЕАЛЬНІ імена та прізвища людей, конкретні деталі, місця, докази.
Справа має підпадати під реальну статтю законодавства України.
Відповідь ТІЛЬКИ JSON без markdown:
{{"story":"детальний опис справи 5-7 речень з іменами та деталями","hidden_article":"точна стаття та правильний вирок"}}"""
    try:
        text = await _gemini(prompt)
        text = text.replace("```json","").replace("```","").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception as e:
        logger.error(f"generate_case: {e}")
        return {"story":f"ПОМИЛКА ГЕНЕРАЦІЇ: {e}","hidden_article":"невідомо"}

async def character_dialogue(character_type: str, case_story: str, history: list, user_message: str) -> str:
    hist = ""
    for m in history:
        role = "Суддя" if m["role"]=="user" else character_type
        hist += f"{role}: {m['content']}\n"
    prompt = f"""Ти граєш роль {character_type} у судовій справі.
ДЕТАЛІ СПРАВИ: {case_story}
ПОПЕРЕДНІЙ ДІАЛОГ:
{hist}
Суддя запитує: {user_message}

Відповідай ВИКЛЮЧНО від імені {character_type} виходячи з деталей цієї конкретної справи.
Відповідь коротка (2-4 речення), реалістична, емоційна. НЕ кажи про адвоката якщо тебе не питають."""
    try:
        return await _gemini(prompt)
    except Exception as e:
        logger.error(f"dialogue: {e}")
        return f"[Помилка AI: {e}]"

async def evaluate_verdict(case_story: str, hidden_article: str, user_verdict: str) -> dict:
    prompt = f"""Ти Верховний суддя-експерт України. Оціни рішення гравця.
Справа: {case_story}
Правильна кваліфікація: {hidden_article}
Рішення гравця: {user_verdict}
Оціни від 1 до 3 (3-ідеально, 2-частково, 1-неправильно).
Відповідь ТІЛЬКИ JSON без markdown:
{{"score":2,"feedback":"детальний розбір українською 3-4 речення"}}"""
    try:
        text = await _gemini(prompt)
        text = text.replace("```json","").replace("```","").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception as e:
        logger.error(f"verdict: {e}")
        return {"score":2,"feedback":f"Помилка оцінки: {e}"}
