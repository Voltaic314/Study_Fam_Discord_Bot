import g4f
from g4f.Provider import (
    Bing,
    HuggingChat,
    OpenAssistant,
)

def initial_prmopt(model_nickname: str) -> str:
    return f"I will call you Study Bot instead of {model_nickname}. "


def ask_bing_ai(message: str) -> str:
    g4f.debug.logging = False  # Enable logging (currently set to False)
    g4f.check_version = False  # Disable automatic version checking
    response = g4f.ChatCompletion.create(
        model=g4f.models.default,
        messages=[{"role": "user", "content": message}],
        provider=Bing,
        auth=True
    )
    return response

def get_news_from_bing_ai() -> str:
    return ask_bing_ai("What's the news today? ")