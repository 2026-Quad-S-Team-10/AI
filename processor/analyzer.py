import json
import re
from pathlib import Path


class EconomicNewsProcessor:
    def __init__(self, glossary_path="storage/glossary.json"):
        self.glossary = self._load_glossary(glossary_path)
        self._sorted_terms = sorted(
            self.glossary.keys(), key=len, reverse=True
        )

    def _load_glossary(self, glossary_path):
        path = Path(glossary_path)
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {item["term"]: item["definition"] for item in data if "term" in item}
        return {}

    def _normalize(self, text):
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def classify(self, article):
        text = " ".join(
            [
                article.get("title") or "",
                article.get("description") or "",
                article.get("content") or "",
            ]
        )
        text = self._normalize(text)

        categories = set()

        if re.search(
            r"(부동산|아파트|주택|전세|월세|분양|재건축|재개발|청약|임대|LTV|DSR)",
            text,
        ):
            categories.add("부동산")

        if re.search(
            r"(주식|증시|코스피|코스닥|NASDAQ|NYSE|S&P|ETF|IPO|상장|배당|주가)",
            text,
        ):
            categories.add("주식")

        if re.search(r"(미국|중국|일본|유럽|EU|FOMC|Fed|ECB|BOJ|IMF|OECD|달러|유로|엔|위안)", text):
            categories.add("국외")

        if re.search(r"(한국|국내|정부|기재부|한은|금통위|코스피|코스닥)", text):
            categories.add("국내")

        if not categories:
            categories.add("국내")

        return sorted(categories)

    def extract_terms(self, article, max_terms=5):
        text = " ".join(
            [
                article.get("title") or "",
                article.get("description") or "",
                article.get("content") or "",
            ]
        )
        text = self._normalize(text)

        found = []
        used = set()
        for term in self._sorted_terms:
            if term in used:
                continue
            if term and term in text:
                used.add(term)
                found.append(term)
                if len(found) >= max_terms:
                    break

        return [
            {"term": term, "definition": self.glossary.get(term, "")}
            for term in found
        ]

    def build_summary(self, article, max_chars=400):
        desc = article.get("description") or ""
        content = article.get("content") or ""
        summary = desc if desc else content
        summary = self._normalize(summary)
        if not summary:
            summary = self._normalize(article.get("title") or "")
        return summary[:max_chars]

    def build_cloze_quiz(self, summary, terms):
        if not summary:
            return {"question": "", "answer": ""}
        if not terms:
            return {"question": summary, "answer": ""}

        term = terms[0]["term"]
        question = summary.replace(term, "____", 1)
        return {"question": question, "answer": term}

    def build_ox_quiz(self, terms):
        quizzes = []
        if not terms:
            return quizzes

        for i, item in enumerate(terms):
            term = item["term"]
            definition = item["definition"]
            if not definition:
                continue
            quizzes.append(
                {
                    "question": f"{term}은(는) {definition}을(를) 의미한다.",
                    "answer": True,
                }
            )

            other = terms[(i + 1) % len(terms)]
            if other["definition"] and other["definition"] != definition:
                quizzes.append(
                    {
                        "question": f"{term}은(는) {other['definition']}을(를) 의미한다.",
                        "answer": False,
                    }
                )

        return quizzes

    def process_article(self, article):
        terms = self.extract_terms(article, max_terms=5)
        summary = self.build_summary(article)
        cloze = self.build_cloze_quiz(summary, terms)
        ox = self.build_ox_quiz(terms)
        categories = self.classify(article)

        return {
            "article": article,
            "categories": categories,
            "summary": summary,
            "terms": terms,
            "quiz": {
                "cloze": cloze,
                "ox": ox,
            },
        }
