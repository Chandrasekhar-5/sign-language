"""
Natural language processing for forming proper sentences from gesture sequences.
"""

import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SentenceBuilder:
    """
    Converts sequences of gestures into natural language sentences.
    Uses rule-based mapping for common gesture combinations.
    """
    
    def __init__(self):
        """Initialize the sentence builder with gesture mappings."""
        self.gesture_to_phrase = {
            "Hello": ["hello", "hi", "greetings"],
            "Stop": ["stop", "halt", "cease"],
            "Yes": ["yes", "yeah", "correct"],
            "No": ["no", "negative", "incorrect"],
            "Thank You": ["thank you", "thanks", "appreciate it"],
            "Thumbs Up": ["good", "great", "excellent", "well done"],
            "Point": ["look", "see", "there", "that"],
            "Peace": ["peace", "goodbye", "bye"],
            "OK": ["okay", "alright", "fine"],
            "Rock On": ["awesome", "cool", "rock on"],
            "Call Me": ["call me", "contact me", "reach out"],
            "Dislike": ["dislike", "bad", "terrible"]
        }
        
        # Common phrase mappings for gesture sequences
        self.phrase_mappings = {
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
        }
        
        # Grammar rules for sentence formation
        self.grammar_rules = {
            "capitalize_first": True,
            "add_period": True,
            "remove_repetition": True
        }
    
    def build_sentence(self, gestures: List[str]) -> str:
        """
        Build a natural language sentence from a sequence of gestures.
        
        Args:
            gestures: List of gesture names
            
        Returns:
            Formatted sentence
        """
        if not gestures:
            return ""
        
        # Check for exact phrase mappings
        gesture_tuple = tuple(gestures)
        if gesture_tuple in self.phrase_mappings:
            return self.phrase_mappings[gesture_tuple]
        
        # Check for partial matches (first 2 or 3 gestures)
        for length in [3, 2]:
            if len(gestures) >= length:
                partial_tuple = tuple(gestures[:length])
                if partial_tuple in self.phrase_mappings:
                    remaining = gestures[length:]
                    base = self.phrase_mappings[partial_tuple]
                    if remaining:
                        return self._combine_phrases(base, remaining)
                    return base
        
        # Build sentence word by word
        words = []
        for gesture in gestures:
            phrase = self._get_phrase_for_gesture(gesture)
            if phrase:
                words.append(phrase)
        
        if not words:
            return " ".join(gestures)
        
        # Apply grammar rules
        sentence = " ".join(words)
        
        if self.grammar_rules["capitalize_first"]:
            sentence = sentence.capitalize()
        
        if self.grammar_rules["add_period"] and not sentence.endswith(('!', '?', '.')):
            sentence += "."
        
        # Remove duplicate consecutive words
        if self.grammar_rules["remove_repetition"]:
            sentence = self._remove_duplicates(sentence)
        
        return sentence
    
    def _get_phrase_for_gesture(self, gesture: str) -> str:
        """Get the primary phrase for a gesture."""
        if gesture in self.gesture_to_phrase:
            return self.gesture_to_phrase[gesture][0]
        return gesture.lower()
    
    def _combine_phrases(self, base: str, remaining: List[str]) -> str:
        """Combine a base phrase with remaining gestures."""
        remaining_words = [self._get_phrase_for_gesture(g) for g in remaining]
        
        # Check for conjunctions
        if len(remaining_words) == 1:
            return f"{base.rstrip('!.?')} and {remaining_words[0]}."
        else:
            return f"{base.rstrip('!.?')} {' '.join(remaining_words)}."
    
    def _remove_duplicates(self, text: str) -> str:
        """Remove consecutive duplicate words."""
        words = text.split()
        result = []
        last_word = None
        
        for word in words:
            if word != last_word:
                result.append(word)
                last_word = word
        
        return " ".join(result)
    
    def suggest_next_gestures(self, current_sequence: List[str], top_k: int = 3) -> List[str]:
        """
        Suggest next possible gestures based on current sequence.
        
        Args:
            current_sequence: Current gesture sequence
            top_k: Number of suggestions to return
            
        Returns:
            List of suggested gestures
        """
        suggestions = set()
        
        # Check phrase mappings for patterns
        for phrase_gestures, _ in self.phrase_mappings.items():
            if len(phrase_gestures) > len(current_sequence):
                # Check if current sequence matches the beginning
                match = True
                for i, gesture in enumerate(current_sequence):
                    if i < len(phrase_gestures) and gesture != phrase_gestures[i]:
                        match = False
                        break
                
                if match and len(phrase_gestures) > len(current_sequence):
                    suggestions.add(phrase_gestures[len(current_sequence)])
        
        # Add common next gestures
        if current_sequence:
            last_gesture = current_sequence[-1]
            common_pairs = {
                "Hello": ["Thumbs Up", "Peace", "Point"],
                "Thank You": ["Thumbs Up", "OK"],
                "Yes": ["Thank You", "OK"],
                "No": ["Stop", "Dislike"],
                "Stop": ["Point", "Hello"],
                "Point": ["Stop", "Hello"],
            }
            
            if last_gesture in common_pairs:
                for gesture in common_pairs[last_gesture]:
                    suggestions.add(gesture)
        
        # Return top_k suggestions
        return list(suggestions)[:top_k]

# Singleton instance
sentence_builder = SentenceBuilder()