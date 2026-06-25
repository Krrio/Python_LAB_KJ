
import re

POS_WORDS = {"good","great","excellent","wonderful","love","best","amazing","brilliant","perfect"}
NEG_WORDS = {"bad","worst","awful","terrible","hate","boring","waste","poor","horrible"}

def sentiment_score(text: str) -> int:
    """CPU-bound: tokenizuj, policz pozytywne minus negatywne."""
    slowa = re.findall(r"\w+", text.lower())
    pozytywne = sum(1 for w in slowa if w in POS_WORDS)
    negatywne = sum(1 for w in slowa if w in NEG_WORDS)
    return pozytywne - negatywne
