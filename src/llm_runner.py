import json
import re
import asyncio
from pydantic import ValidationError
from openai import AsyncOpenAI, OpenAI
from src import config
from utils.logger import logging
from llm_schema_prompts.llm_output_format import LLMAnswer
from llm_schema_prompts.model_prompts import USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def build_user_prompt(case: dict) -> str:
    logger.debug(f"Building user prompt for case: {case.get('id', 'unknown')}")
    case_id = case["id"]
    desc = case["description"]
    inputs = case["input_tables"]
    sql_transformation = case["sql_script"]
    focus = case.get("focus", "Datentypen, Transformationen, Rechenlogik")
    schema_json = LLMAnswer.json_schema_str()

    prompt = USER_PROMPT_TEMPLATE.format(
        case_id=case_id,
        desc=desc,
        inputs=json.dumps(inputs, ensure_ascii=False),
        sql_transformation=sql_transformation,
        focus=focus,
        schema_json=schema_json
    )
    logger.debug(f"User prompt built: {prompt[:200]}...")  # Log only the first 200 chars
    return prompt

# Aufruf der OpenAI-kompatiblen API (llm-stats.com mit api_key)
def _client() -> OpenAI:
    logger.debug("Initializing OpenAI client")
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL, timeout=60, max_retries=0)
        logger.info("OpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        raise

# Aufruf der AsyncOpenAI-kompatiblen API (llm-stats.com mit api_key)
def _async_client() -> AsyncOpenAI:
    logger.debug("Initializing AsyncOpenAI client")
    try:
        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL, timeout=60, max_retries=0)
        logger.info("AsyncOpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize AsyncOpenAI client: {e}")
        raise

# Synchroner API-Aufruf für einzelne Anfragen
def prompt_llm(model: str, system_prompt: str, user_prompt: str) -> str:
    logger.info(f"Prompting LLM with model: {model}")
    client = _client()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.TEMPERATURE,
            # testen des forced JSON-Outputs
            response_format={"type": "json_object"}
        )
        logger.info("Received response from LLM")
        logger.debug(f"LLM response: {resp.choices[0].message.content[:200]}...")
        # return raw output text
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"Error during LLM prompt: {e}")
        raise

# Asynchroner API-Aufruf für parallele Anfragen
async def async_prompt_llm(model: str, system_prompt: str, user_prompt: str) -> str:
    logger.info(f"Prompting LLM with model: {model}")
    client = _async_client()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.TEMPERATURE,
            # testen des forced JSON-Outputs
            response_format={"type": "json_object"}
        )
        logger.info(f"Received response from LLM with model: {model}")
        logger.debug(f"LLM response: {resp.choices[0].message.content[:200]}...")
        # return raw output text
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"Error during LLM prompt: {e}")
        raise

def ping_llm():
    try:
        # Funktion zum Pingen des LLMs
        client = _client()
        r = client.chat.completions.create(
            model=config.DEFAULT_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            temperature=0.2
        )
        logger.debug(f"LLM-Antwort auf Ping: {r.choices[0].message.content}")
        logger.info("Ping erfolgreich!")
    except Exception as e:
        logger.error(f"Ping fehlgeschlagen: {e}")

# JSON-Extraktion aus der LLM-Antwort
def _extract_json(text: str) -> dict:
    """
    Erwartet die JSON LLMANSWER. Textangaben außerhalb der JSON wird der Text abgeschnitten.
    """
    logger.debug("Extracting JSON from LLM response")
    try:
        result = json.loads(text)
        logger.debug("JSON extraction successful")
        return result
    except json.JSONDecodeError:
        logger.warning("Direct JSON load failed, trying regex extraction")
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            logger.error("No JSON object found in text")
            raise ValueError("Es konnte kein JSON-Objekt im Text gefunden werden.")
        try:
            result = json.loads(m.group(0))
            logger.debug("Regex JSON extraction successful")
            return result
        except Exception as e:
            logger.error(f"Regex JSON extraction failed: {e}")
            raise

# parse Antwort und validiere gegen das Schema LLMAnswer
def parse_answer(raw: str) -> LLMAnswer:
    logger.debug("Parsing and validating LLM answer")
    data = _extract_json(raw)
    try:
        answer = LLMAnswer.model_validate(data)
        logger.info("LLM answer validated successfully")
        return answer
    except ValidationError as e:
        logger.error(f"Antwort entspricht nicht dem Schema: {e}")
        raise ValueError(f"Antwort entspricht nicht dem Schema: {e}")
