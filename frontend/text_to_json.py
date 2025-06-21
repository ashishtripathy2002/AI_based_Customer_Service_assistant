"""Converts text to JSON format."""

from __future__ import annotations

from text_analyzer import ConversationAnalyzer


class AnalyzerSingleton:
    """Singleton to manage the shared analyzer instance."""

    analyzer: ConversationAnalyzer | None = None

    @classmethod
    def get_analyzer(cls) -> ConversationAnalyzer:
        """Get the pre-initialized analyzer. Initialize it if not already done."""
        if cls.analyzer is None:
            cls.analyzer = ConversationAnalyzer()
        return cls.analyzer


def init_analyzer() -> None:
    """Initialize the analyzer (call this at application startup)."""
    AnalyzerSingleton.get_analyzer()


def textual_analysis(text: list) -> dict:
    """Perform text analysis using the pre-initialized analyzer."""
    init_analyzer()
    analyzer = AnalyzerSingleton.get_analyzer()
    if analyzer is None:
        error_msg = "Analyzer not initialized. Call init_analyzer() first."
        raise RuntimeError(error_msg)

    conversation = []
    (
        total_greets_c,
        total_disclaims_c,
        total_closures_c,
        total_pil_c,
        total_prohibited_words_c,
    ) = 0, 0, 0, 0, 0
    (
        total_greets_a,
        total_disclaims_a,
        total_closures_a,
        total_pil_a,
        total_prohibited_words_a,
    ) = 0, 0, 0, 0, 0
    speaker, main_text, text_analysis = None, None, None
    intent_cat_score, issue_cat_score = None, None
    sentiment_counts = {
        "speakers": {
            "Net": {"positive": 0, "neutral": 0, "negative": 0},
            "Handler": {"positive": 0, "neutral": 0, "negative": 0},
            "Client": {"positive": 0, "neutral": 0, "negative": 0},
        },
    }

    for key_val in text:
        for key, val in key_val.items():
            if key == "sender":
                speaker = val
            else:
                main_text = val
                text_analysis = analyzer.analyze_line(main_text)

        sentiment = text_analysis["sentiment"]["label"]
        new_pil, pil_cat = (
            text_analysis["personal_info"]["count"],
            text_analysis["personal_info"]["categories"],
        )
        prohibited_words_count, prohibited_words = (
            text_analysis["prohibited_phrases"]["count"],
            text_analysis["prohibited_phrases"]["phrases"],
        )
        new_greets, new_disclaims, new_closures = (
            text_analysis["required_phrases"]["greetings"],
            text_analysis["required_phrases"]["disclaimers"],
            text_analysis["required_phrases"]["closing_statements"],
        )
        req_phrase_cat = text_analysis["required_phrases"]["categories"]
        intent_cat_score = [(i["intent"], i["score"]) for i in text_analysis["intents"]]
        issue_cat_score = [(i["issue"], i["score"]) for i in text_analysis["issues"]]

        if speaker == "customer":
            total_greets_c, total_disclaims_c, total_closures_c = (
                total_greets_c + new_greets,
                total_disclaims_c + new_disclaims,
                total_closures_c + new_closures,
            )
            total_pil_c = total_pil_c + new_pil
            total_prohibited_words_c += prohibited_words_count
        else:
            total_greets_a, total_disclaims_a, total_closures_a = (
                total_greets_a + new_greets,
                total_disclaims_a + new_disclaims,
                total_closures_a + new_closures,
            )
            total_pil_a = total_pil_a + new_pil
            total_prohibited_words_a += prohibited_words_count

        # Net count of sentiments
        if sentiment in sentiment_counts["speakers"]["Net"]:
            sentiment_counts["speakers"]["Net"][sentiment] += 1
            if speaker == "customer":
                sentiment_counts["speakers"]["Handler"][sentiment] += 1
            elif speaker == "agent":
                sentiment_counts["speakers"]["Client"][sentiment] += 1

        conversation.append(
            {
                "speaker": speaker,
                "text": main_text,
                "sentiment": sentiment,
                "req_phrase_cat": req_phrase_cat,
                "pil_category": pil_cat,
                "prohibited_words": prohibited_words,
                "Intent_cat_score": intent_cat_score,
                "Issue_cat_score": issue_cat_score,
            },
        )

    return {
        "Total Sentiment" : sentiment_counts["speakers"]["Net"],
        "Customer Sentiment" : sentiment_counts["speakers"]["Client"],
        "Agent Sentiment" : sentiment_counts["speakers"]["Handler"],
        "Total Greeting made by Agent": total_greets_a,
        "Total Disclaimer made by Agent": total_disclaims_a,
        "Total Closures made by Agent": total_closures_a,
        "Total PII violations made by Agent": total_pil_a,
        "Total prohibited word used by Agent": total_prohibited_words_a,
    }
