"""Provide a class to analyze customer service conversations."""

from __future__ import annotations

import re

from patterns_config import load_patterns_config
from rapidfuzz import fuzz
from textblob import TextBlob

config_path =  "patterns.yml"

FUZZ_THRESHOLD = 55  # Fuzzy matching threshold for required phrases
POSITIVE_THRESHOLD = 0.1
NEGATIVE_THRESHOLD = -0.1



class ConversationAnalyzer:
    """Analyze customer service conversations."""

    def __init__(self, config_path: str = config_path) -> None:
        """Initialize with config and load NLP models."""
        # Load configuration
        self.config = load_patterns_config(config_path)
        self.prohibited_phrases = self.config.ProhibitedPhrases
        self.greetings = self.config.Greetings
        self.disclaimers = self.config.Disclaimers
        self.closing_statements = self.config.ClosingStatements
        self.personal_info_patterns = self.config.PersonalInformationPatterns
        self.sensitive_info_patterns = self.config.SensitiveInformationPatterns
        self.intent_patterns = self.config.IntentPatterns
        self.issue_patterns = self.config.IssuePatterns
        self.sentiment_boosters = self.config.SentimentBoosters

    def analyze_line(self, line: str) -> dict:
        """Analyze a single line of conversation (structured or plain text)."""
        # Parse structured line if it matches the pattern
        parsed = self.parse_structured_line(line)
        speaker = parsed["speaker"] if parsed else None
        text = parsed["text"] if parsed else line

        # Perform all analyses
        sentiment = self.analyze_sentiment(text)
        intents = self.detect_intents(text)
        issues = self.detect_issues(text)
        req_phrases = self.detect_required_phrases(text)
        pil_info = self.detect_personal_info(text)
        prohibited = self.detect_prohibited_phrases(text)

        return {
            "text": text,
            "speaker": speaker,
            "sentiment": sentiment,
            "intents": intents,
            "issues": issues,
            "required_phrases": req_phrases,
            "personal_info": pil_info,
            "prohibited_phrases": prohibited,
        }

    def parse_structured_line(self, line: str) -> dict | None:
        """Parse structured transcript line."""
        pattern = (
            r"(\d+\.\d+)\s+(\d+\.\d+)\s+(SPEAKER_\d+)\s+(.*?)(?:\s+SENTIMENT:(\w+))?$"
        )
        if match := re.match(pattern, line.strip()):
            return {
                "start": float(match.group(1)),
                "end": float(match.group(2)),
                "speaker": match.group(3),
                "text": match.group(4),
                "sentiment": match.group(5).lower() if match.group(5) else None,
            }
        return None

    def analyze_sentiment(self, text: str) -> dict:
        """Hybrid sentiment analysis."""
        # TextBlob analysis
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity

        # Apply keyword boosts
        text_lower = text.lower()
        pos_boost = any(
            word in text_lower for word in self.sentiment_boosters["positive"]
        )
        neg_boost = any(
            word in text_lower for word in self.sentiment_boosters["negative"]
        )

        if pos_boost:
            return {
                "label": "positive",
                "score": min(1.0, polarity + 0.3),
                "method": "textblob+keywords",
            }
        if neg_boost:
            return {
                "label": "negative",
                "score": min(1.0, abs(polarity) + 0.3),
                "method": "textblob+keywords",
            }
        if polarity > POSITIVE_THRESHOLD:
            return {"label": "positive", "score": polarity, "method": "textblob"}
        if polarity < NEGATIVE_THRESHOLD:
            return {"label": "negative", "score": abs(polarity), "method": "textblob"}
        return {"label": "neutral", "score": 0.5, "method": "textblob"}

    def detect_intents(self, text: str) -> list[dict]:
        """Hybrid intent detection."""
        text_lower = text.lower()
        intents = []

        # Keyword matching
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                intents.append({"intent": intent, "score": 0.8, "method": "keywords"})

        if intents:
            return intents

        return [{"intent": "general", "score": 0.5, "method": "fallback"}]

    def detect_issues(self, text: str) -> list[dict]:
        """Hybrid issue detection."""
        text_lower = text.lower()
        issues = []

        # Keyword matching
        for issue, phrases in self.issue_patterns.items():
            if any(phrase in text_lower for phrase in phrases):
                issues.append({"issue": issue, "score": 0.8, "method": "keywords"})

        if issues:
            return issues


        return issues

    def detect_required_phrases(self, text: str) -> dict:
        """Detect required phrases (greetings, disclaimers, closings)."""
        greets, disclaims, closures, phrase_cat = 0, 0, 0, []

        for greet in self.greetings:
            if fuzz.token_sort_ratio(text, greet) > FUZZ_THRESHOLD:
                greets = 1
                phrase_cat.append("Greetings")
                break

        for disclaim in self.disclaimers:
            if fuzz.token_sort_ratio(text, disclaim) > FUZZ_THRESHOLD:
                disclaims = 1
                phrase_cat.append("Disclaimers")
                break

        for closure in self.closing_statements:
            if fuzz.token_sort_ratio(text, closure) > FUZZ_THRESHOLD:
                closures = 1
                phrase_cat.append("Closing_Statements")
                break

        return {
            "greetings": greets,
            "disclaimers": disclaims,
            "closing_statements": closures,
            "categories": phrase_cat,
        }

    def detect_personal_info(self, text: str) -> dict:
        """Detect personal/sensitive information."""
        pil_present, pil_cat = 0, []

        # Check sensitive info patterns
        for key, pattern in self.sensitive_info_patterns.items():
            if (key != "atm_pin" and re.search(pattern, text)) or (
                key == "atm_pin" and self._is_valid_atm_pin(text)
            ):
                pil_present += 1
                pil_cat.append(key)

        # Check personal info patterns
        for key, pattern in self.personal_info_patterns.items():
            if re.search(pattern, text):
                pil_present += 1
                pil_cat.append(key)

        return {"count": pil_present, "categories": pil_cat}

    def _is_valid_atm_pin(self, text: str) -> bool:
        """Check if text contains a valid ATM PIN that's not part of other patterns."""
        potential_pins = re.findall(self.sensitive_info_patterns["atm_pin"], text)

        for pin in potential_pins:
            # Check if this isn't part of other personal info patterns
            is_personal = any(
                re.search(pattern, pin)
                for pattern in self.personal_info_patterns.values()
            )
            if not is_personal:
                return True
        return False

    def detect_prohibited_phrases(self, text: str) -> dict:
        """Detect prohibited phrases/profanity."""
        words_count, prohibited_words = 0, []
        text_lower = text.lower()
        text_words = text_lower.split()

        for phrase in self.prohibited_phrases:
            if phrase in text_lower and phrase in text_words:
                words_count += 1
                prohibited_words.append(phrase)

        return {"count": words_count, "phrases": prohibited_words}
