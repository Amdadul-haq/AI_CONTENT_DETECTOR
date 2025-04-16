# backend/ai_detector.py
import re
from statistics import mean, stdev
import math
import random  # For demonstration purposes only

def detect_ai_content(text):
    """Detect AI-generated content using improved heuristic methods"""
    try:
        if not text or len(text) < 50:
            return {
                'ai_percentage': 0,
                'highlighted_sections': [],
                'details': {
                    'sentence_variety': 0,
                    'word_repetition': 0,
                    'transition_usage': 0,
                    'burstiness': 0
                }
            }

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 1. Sentence structure variety
        sentence_lengths = [len(s.split()) for s in sentences]
        
        # Calculate variance and normalize based on text length
        try:
            sentence_variance = stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
            # AI text often has consistent sentence lengths
            sentence_variety_score = min(100, max(0, 100 - (20 * (5 / (sentence_variance + 1)))))
        except:
            sentence_variety_score = 50
        
        # 2. Word repetition analysis
        words = re.findall(r'\b\w+\b', text.lower())
        word_count = len(words)
        
        if word_count > 0:
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only consider meaningful words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Calculate repetition score
            if word_freq:
                unique_ratio = len(word_freq) / word_count
                repetition_score = min(100, max(0, 100 * (1 - unique_ratio) * 3))
            else:
                repetition_score = 0
        else:
            repetition_score = 0
        
        # 3. Transition words analysis
        transition_words = [
            'however', 'therefore', 'moreover', 'furthermore', 'consequently',
            'additionally', 'nevertheless', 'thus', 'hence', 'accordingly',
            'subsequently', 'meanwhile', 'conversely', 'similarly', 'likewise'
        ]
        
        transition_count = sum(text.lower().count(" " + word + " ") for word in transition_words)
        # Normalize by text length
        transition_ratio = transition_count / (word_count / 100) if word_count > 0 else 0
        transition_score = min(100, max(0, transition_ratio * 10))
        
        # 4. Burstiness (human writing tends to be more "bursty" with varied word usage)
        if len(sentences) > 5:
            # Calculate lexical diversity in different parts of the text
            chunks = [words[i:i+len(words)//3] for i in range(0, len(words), len(words)//3)]
            chunk_diversities = []
            
            for chunk in chunks:
                if chunk:
                    chunk_freq = {}
                    for word in chunk:
                        if len(word) > 3:
                            chunk_freq[word] = chunk_freq.get(word, 0) + 1
                    chunk_diversities.append(len(chunk_freq) / len(chunk))
            
            # Calculate variance in lexical diversity
            burstiness = stdev(chunk_diversities) * 100 if len(chunk_diversities) > 1 else 50
            burstiness_score = min(100, max(0, 100 - burstiness))
        else:
            burstiness_score = 50
        
        # Calculate final score with weighted components
        weights = {
            'sentence_variety': 0.25,
            'word_repetition': 0.3,
            'transition_usage': 0.2,
            'burstiness': 0.25
        }
        
        ai_percentage = int(
            sentence_variety_score * weights['sentence_variety'] +
            repetition_score * weights['word_repetition'] +
            transition_score * weights['transition_usage'] +
            burstiness_score * weights['burstiness']
        )
        
        # Find sections that appear most AI-generated
        highlighted_sections = []
        if len(sentences) > 3:
            sentence_scores = []
            
            for i, sentence in enumerate(sentences):
                if len(sentence.split()) > 5:
                    # Score each sentence based on length, common phrases, etc.
                    words_in_sentence = sentence.lower().split()
                    
                    # Check for transition words
                    has_transition = any(word in transition_words for word in words_in_sentence)
                    
                    # Check for sentence length compared to average
                    avg_length = mean(sentence_lengths)
                    length_diff = abs(len(words_in_sentence) - avg_length)
                    
                    # Score the sentence
                    sentence_score = 0
                    if has_transition:
                        sentence_score += 30
                    if length_diff < 2:  # Very close to average length
                        sentence_score += 40
                    
                    sentence_scores.append((i, sentence, sentence_score))
            
            # Sort by score and take top 3
            sentence_scores.sort(key=lambda x: x[2], reverse=True)
            for _, sentence, score in sentence_scores[:3]:
                if score > 50 and len(sentence) > 20:
                    highlighted_sections.append(sentence)
        
        return {
            'ai_percentage': ai_percentage,
            'highlighted_sections': highlighted_sections,
            'details': {
                'sentence_variety': int(sentence_variety_score),
                'word_repetition': int(repetition_score),
                'transition_usage': int(transition_score),
                'burstiness': int(burstiness_score)
            }
        }
    except Exception as e:
        return {"error": f"Error during AI detection: {str(e)}"}
