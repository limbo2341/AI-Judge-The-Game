import json, logging, os, urllib.request, asyncio
logger = logging.getLogger(__name__)

async def _groq(prompt: str) -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not set")
    body = json.dumps({"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],"temperature":0.9,"max_tokens":1000}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body, headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"}, method="POST")
    def do():
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    data = await asyncio.get_event_loop().run_in_executor(None, do)
    return data["choices"][0]["message"]["content"].strip()

async def generate_case(case_type: str) -> dict:
    prompt = f"""Ти генератор юридичних справ для гри-симулятора судді України.
Згенеруй унікальну реалістичну справу категорії {case_type}.
Придумай РЕАЛЬНІ імена, конкретні деталі, місця, докази.
Справа має підпадати під реальну статтю законодавства України.
Відповідь ТІЛЬКИ JSON без markdown:
{{"story":"детальний опис справи 5-7 речень з іменами та деталями","hidden_article":"точна стаття та правильний вирок"}}"""
    try:
        text = await _groq(prompt)
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text[text.find("{"):text.rfind("}")+1])
    except Exception as e:
        logger.error(f"generate_case: {e}")
        return {"story":f"ПОМИЛКА: {e}","hidden_article":"невідомо"}

async def character_dialogue(character_type: str, case_story: str, history: list, user_message: str) -> str:
    hist = ""
    for m in history:
        role = "Суддя" if m["role"]=="user" else character_type
        hist += f"{role}: {m['content']}\n"
    prompt = f"""Ти граєш роль {character_type} у судовій справі України.
СПРАВА: {case_story}
ДІАЛОГ:
{hist}
Суддя: {user_message}
Відповідай від імені {character_type} виходячи з деталей справи. 2-4 речення, емоційно, реалістично."""
    try:
        return await _groq(prompt)
    except Exception as e:
        logger.error(f"dialogue: {e}")
        return f"[Помилка: {e}]"

async def evaluate_verdict(case_story: str, hidden_article: str, user_verdict: str) -> dict:
    prompt = f"""Ти Верховний суддя України. Оціни рішення гравця.
Справа: {case_story}
Правильна стаття: {hidden_article}
Рішення гравця: {user_verdict}
Оціни від 1 до 3. Відповідь ТІЛЬКИ JSON без markdown:
{{"score":2,"feedback":"детальний розбір українською 3-4 речення"}}"""
    try:
        text = await _groq(prompt)
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text[text.find("{"):text.rfind("}")+1])
    except Exception as e:
        logger.error(f"verdict: {e}")
        return {"score":2,"feedback":f"Помилка: {e}"}
