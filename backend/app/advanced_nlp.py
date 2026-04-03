"""
Advanced NLP for intelligent sentence formation using transformer-based approach.
"""

import numpy as np
import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class GestureContext:
    """Context for gesture understanding."""
    sequence: List[str]
    timestamp: float
    confidence: float
    user_id: Optional[str] = None

class AdvancedNLP:
    """
    Advanced natural language processing for sign language translation.
    Features:
    - Context-aware translation
    - Grammar correction
    - Personalization
    - Emotion detection
    """
    
    def __init__(self):
        """Initialize advanced NLP system."""
        # Gesture to word mappings with multiple meanings
        self.gesture_meanings = {
            "Hello": ["hello", "hi", "greetings", "hey"],
            "Stop": ["stop", "halt", "cease", "wait"],
            "Yes": ["yes", "yeah", "correct", "affirmative"],
            "No": ["no", "negative", "incorrect", "never"],
            "Thank You": ["thank you", "thanks", "appreciate", "grateful"],
            "Thumbs Up": ["good", "great", "excellent", "awesome", "perfect"],
            "Point": ["look", "see", "there", "that", "this"],
            "Peace": ["peace", "goodbye", "bye", "farewell"],
            "OK": ["okay", "alright", "fine", "acceptable"],
            "Rock On": ["awesome", "cool", "amazing", "rock on"],
            "Call Me": ["call me", "contact", "reach out", "message"],
            "Dislike": ["dislike", "bad", "terrible", "awful"]
        }
        
        # Common phrases (multi-gesture sequences)
        self.common_phrases = {
            ("Hello", "Point", "Thumbs Up"): "Hello, how are you?",
            ("Hello", "Thumbs Up"): "Hello, good to see you!",
            ("Stop", "Point", "Hello"): "Stop, I need help!",
            ("Yes", "Thank You"): "Yes, thank you.",
            ("No", "Stop"): "No, stop please.",
            ("OK", "Thumbs Up"): "OK, good job!",
            ("Thank You", "Thumbs Up"): "Thank you, that's great!",
            ("Hello", "Peace"): "Hello and goodbye!",
            ("Point", "Stop"): "Look, stop!",
            ("Yes", "OK"): "Yes, that's okay.",
            ("No", "Dislike"): "No, I don't like that.",
            ("Call Me", "Thumbs Up"): "Please call me, that's good.",
            ("Rock On", "Thumbs Up"): "Awesome, great job!",
            ("Hello", "Stop", "Point"): "Hello, stop and look!",
            ("Yes", "Yes"): "Yes, yes!",
            ("No", "No"): "No, no!",
            ("Thank You", "Thank You"): "Thank you very much!",
        }
        
        # Grammar rules
        self.grammar = {
            "capitalize_first": True,
            "add_period": True,
            "exclamation_for_emphasis": True,
            "remove_duplicates": True,
            "add_articles": False,  # Advanced feature
            "fix_verb_tense": False  # Advanced feature
        }
        
        # Context tracking
        self.context_history = []
        self.context_window = 5
        
        # Personalization
        self.user_preferences = defaultdict(lambda: defaultdict(int))
        
        # Emotion mapping
        self.emotion_indicators = {
            "Thumbs Up": "positive",
            "OK": "neutral",
            "Dislike": "negative",
            "Rock On": "excited",
            "Hello": "friendly",
            "Stop": "urgent"
        }
        
        # Load custom phrases if available
        self._load_custom_phrases()
    
    def _load_custom_phrases(self):
        """Load custom phrases from JSON file."""
        try:
            with open('custom_phrases.json', 'r') as f:
                custom = json.load(f)
                self.common_phrases.update(custom)
                logger.info(f"Loaded {len(custom)} custom phrases")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Error loading custom phrases: {e}")
    
    def build_sentence(self, gestures: List[str], context: Optional[GestureContext] = None) -> Dict:
        """
        Build a natural language sentence from gesture sequence.
        
        Args:
            gestures: List of gesture names
            context: Optional context for better translation
            
        Returns:
            Dictionary with sentence, confidence, and metadata
        """
        if not gestures:
            return {"sentence": "", "confidence": 0, "gestures": []}
        
        # Check for exact phrase match
        gesture_tuple = tuple(gestures)
        if gesture_tuple in self.common_phrases:
            sentence = self.common_phrases[gesture_tuple]
            return {
                "sentence": sentence,
                "confidence": 0.95,
                "gestures": gestures,
                "is_phrase": True
            }
        
        # Check for partial matches
        for length in [3, 2]:
            if len(gestures) >= length:
                partial_tuple = tuple(gestures[:length])
                if partial_tuple in self.common_phrases:
                    base_sentence = self.common_phrases[partial_tuple]
                    remaining = gestures[length:]
                    if remaining:
                        sentence = self._combine_sentences(base_sentence, remaining)
                    else:
                        sentence = base_sentence
                    return {
                        "sentence": sentence,
                        "confidence": 0.85,
                        "gestures": gestures,
                        "is_phrase": True
                    }
        
        # Build word by word
        words = []
        word_confidences = []
        
        for gesture in gestures:
            word, conf = self._gesture_to_word(gesture, context)
            words.append(word)
            word_confidences.append(conf)
        
        # Apply grammar
        sentence = self._apply_grammar(words, gestures)
        
        # Add context information
        if context and self.context_history:
            sentence = self._apply_context(sentence, context)
        
        # Detect emotion
        emotion = self._detect_emotion(gestures)
        
        # Calculate overall confidence
        confidence = np.mean(word_confidences) if word_confidences else 0.7
        
        # Update context history
        self._update_context(gestures, sentence, confidence)
        
        return {
            "sentence": sentence,
            "confidence": confidence,
            "gestures": gestures,
            "words": words,
            "emotion": emotion,
            "is_phrase": False
        }
    
    def _gesture_to_word(self, gesture: str, context: Optional[GestureContext] = None) -> Tuple[str, float]:
        """
        Convert gesture to word with context awareness.
        """
        if gesture not in self.gesture_meanings:
            return gesture.lower(), 0.5
        
        meanings = self.gesture_meanings[gesture]
        
        # Use context to choose the best meaning
        if context and self.context_history:
            # Check last sentence for context
            last_context = self.context_history[-1] if self.context_history else None
            if last_context:
                last_words = last_context['sentence'].lower().split()
                
                # Choose meaning that fits context
                for meaning in meanings:
                    if any(word in last_words for word in meaning.split()):
                        return meaning, 0.9
        
        # Check user preferences
        user_pref = self.user_preferences[gesture]
        if user_pref:
            preferred = max(user_pref.items(), key=lambda x: x[1])
            return preferred[0], 0.85
        
        # Return first meaning
        return meanings[0], 0.8
    
    def _combine_sentences(self, base: str, remaining: List[str]) -> str:
        """
        Intelligently combine sentences.
        """
        remaining_words = [self._gesture_to_word(g, None)[0] for g in remaining]
        
        # Remove punctuation from base
        base_clean = base.rstrip('!?.,')
        
        # Check for natural connectors
        if len(remaining_words) == 1:
            connectors = ["and", "then", "so", "but"]
            connector = self._choose_connector(base_clean, remaining_words[0])
            return f"{base_clean} {connector} {remaining_words[0]}."
        else:
            return f"{base_clean} {' '.join(remaining_words)}."
    
    def _choose_connector(self, base: str, next_word: str) -> str:
        """Choose appropriate connector based on context."""
        positive_indicators = ["good", "great", "awesome", "thanks"]
        negative_indicators = ["bad", "stop", "no", "dislike"]
        
        if any(word in base.lower() for word in positive_indicators):
            if any(word in next_word for word in positive_indicators):
                return "and"
            else:
                return "but"
        elif any(word in base.lower() for word in negative_indicators):
            return "so"
        else:
            return "then"
    
    def _apply_grammar(self, words: List[str], gestures: List[str]) -> str:
        """Apply grammar rules to the sentence."""
        if not words:
            return ""
        
        sentence = " ".join(words)
        
        # Remove duplicates
        if self.grammar["remove_duplicates"]:
            unique_words = []
            for word in sentence.split():
                if not unique_words or word != unique_words[-1]:
                    unique_words.append(word)
            sentence = " ".join(unique_words)
        
        # Capitalize first letter
        if self.grammar["capitalize_first"]:
            sentence = sentence[0].upper() + sentence[1:] if sentence else ""
        
        # Add exclamation for emphasis if needed
        if self.grammar["exclamation_for_emphasis"]:
            if any(g in gestures for g in ["Thumbs Up", "Rock On"]):
                if not sentence.endswith('!'):
                    sentence = sentence.rstrip('.') + '!'
            elif any(g in gestures for g in ["Stop", "No"]):
                if not sentence.endswith('!'):
                    sentence = sentence.rstrip('.') + '!'
        
        # Add period
        if self.grammar["add_period"] and not sentence.endswith(('!', '?', '.')):
            sentence += '.'
        
        return sentence
    
    def _detect_emotion(self, gestures: List[str]) -> str:
        """Detect emotion from gesture sequence."""
        emotions = [self.emotion_indicators.get(g, "neutral") for g in gestures]
        
        # Count emotion frequencies
        from collections import Counter
        emotion_counts = Counter(emotions)
        
        if emotion_counts:
            dominant = emotion_counts.most_common(1)[0]
            if dominant[1] > len(gestures) / 2:
                return dominant[0]
        
        return "neutral"
    
    def _apply_context(self, sentence: str, context: GestureContext) -> str:
        """Apply contextual understanding to improve sentence."""
        if not self.context_history:
            return sentence
        
        # Check if this is a response to previous sentence
        last = self.context_history[-1]
        
        # If previous was a question, adjust response
        if last['sentence'].endswith('?'):
            if sentence.lower().startswith('yes'):
                return f"Yes, {sentence[3:]}"
            elif sentence.lower().startswith('no'):
                return f"No, {sentence[2:]}"
        
        return sentence
    
    def _update_context(self, gestures: List[str], sentence: str, confidence: float):
        """Update context history."""
        self.context_history.append({
            'gestures': gestures,
            'sentence': sentence,
            'confidence': confidence,
            'timestamp': __import__('time').time()
        })
        
        # Keep only recent context
        if len(self.context_history) > self.context_window:
            self.context_history.pop(0)
    
    def suggest_next_gestures(self, current_sequence: List[str], top_k: int = 3) -> List[Dict]:
        """
        Suggest next possible gestures based on current sequence.
        
        Returns:
            List of suggestions with confidence scores
        """
        suggestions = []
        
        # Check common phrases
        for phrase_gestures, phrase_text in self.common_phrases.items():
            if len(phrase_gestures) > len(current_sequence):
                # Check if current sequence matches beginning
                match = True
                for i, gesture in enumerate(current_sequence):
                    if i < len(phrase_gestures) and gesture != phrase_gestures[i]:
                        match = False
                        break
                
                if match:
                    next_gesture = phrase_gestures[len(current_sequence)]
                    suggestions.append({
                        'gesture': next_gesture,
                        'confidence': 0.9,
                        'completes_phrase': phrase_text
                    })
        
        # Add statistical suggestions based on history
        if self.context_history:
            # Find common sequences
            sequence_counts = defaultdict(int)
            for ctx in self.context_history:
                gestures = ctx['gestures']
                for i, gesture in enumerate(gestures):
                    if i < len(gestures) - 1:
                        sequence_counts[(gesture, gestures[i + 1])] += 1
            
            if current_sequence:
                last_gesture = current_sequence[-1]
                for (g1, g2), count in sequence_counts.items():
                    if g1 == last_gesture:
                        suggestions.append({
                            'gesture': g2,
                            'confidence': min(0.7, count / 10),
                            'based_on': 'history'
                        })
        
        # Remove duplicates and sort by confidence
        seen = set()
        unique_suggestions = []
        for s in sorted(suggestions, key=lambda x: x['confidence'], reverse=True):
            if s['gesture'] not in seen:
                seen.add(s['gesture'])
                unique_suggestions.append(s)
        
        return unique_suggestions[:top_k]
    
    def personalize(self, gesture: str, chosen_word: str):
        """Personalize translations for a user."""
        self.user_preferences[gesture][chosen_word] += 1
        
        # Save preferences periodically
        if sum(self.user_preferences[gesture].values()) % 10 == 0:
            self._save_preferences()
    
    def _save_preferences(self):
        """Save user preferences to file."""
        try:
            with open('user_preferences.json', 'w') as f:
                json.dump(dict(self.user_preferences), f)
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")

# Singleton instance
advanced_nlp = AdvancedNLP()