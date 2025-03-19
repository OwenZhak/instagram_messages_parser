import json
from datetime import datetime
import re
from collections import Counter

def decode_content(text):
    """Decode escape sequences to readable text."""
    if not isinstance(text, str):
        return text
    
    try:
        # Handle standard Instagram encoding
        return bytes(text, 'latin1').decode('utf-8')
    except Exception as exc:
        print(f"Primary decoding failed: {exc}")
        
        # Attempt alternative decodings
        try:
            return bytes(text.encode('latin1')).decode('utf-8')
        except:
            try:
                return text.encode('ascii').decode('unicode_escape')
            except:
                return text

def parse_instagram_json(file_path):
    """Parse Instagram JSON file and return filtered/decoded messages and participants."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as exc:
        print(f"Error reading file {file_path}: {exc}")
        return {"messages": [], "participants": []}
    
    participants = [p.get('name', '') for p in data.get('participants', [])]
    all_messages = []
    
    for msg in data.get('messages', []):
        sender = msg.get('sender_name', '')
        content = msg.get('content', '')
        
        # Filter out likes, reactions, edited messages, etc.
        if (
            content != "Liked a message"
            and not content.startswith("Reacted")
            and not content.startswith("Liked")
            and "edited" not in content
            and "to your message" not in content
        ):
            decoded = decode_content(content)
            timestamp = msg.get('timestamp_ms', 0)
            
            all_messages.append({
                'sender_name': sender,
                'content': decoded,
                'timestamp': timestamp
            })
    
    return {"messages": all_messages, "participants": participants}

class MessageAnalyzer:
    """Analyze messages: stats, sorting, longest, etc."""
    
    @staticmethod
    def format_timestamp(timestamp_ms):
        if not timestamp_ms:
            return ""
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def calculate_stats(messages):
        sender_counts = {}
        sender_chars = {}
        
        for msg in messages:
            sender = msg['sender_name']
            content = msg['content']
            
            sender_counts.setdefault(sender, 0)
            sender_chars.setdefault(sender, 0)
            
            sender_counts[sender] += 1
            sender_chars[sender] += len(content) if content else 0
            
        return {
            "total_messages": len(messages),
            "sender_counts": sender_counts,
            "sender_chars": sender_chars
        }
    
    @staticmethod
    def find_longest_messages(messages, count=20):
        valid_messages = [m for m in messages if m.get('content')]
        return sorted(valid_messages, key=lambda x: len(x['content']), reverse=True)[:count]
    
    @staticmethod
    def sort_by_timestamp(messages, reverse=True):
        return sorted(messages, key=lambda x: x.get('timestamp', 0), reverse=reverse)
    
    @staticmethod
    def find_most_common_words(messages, sender=None, top_n=50, min_length=1):
        """Find most common words used by a specific sender or all senders.
        
        Args:
            messages: List of message dictionaries
            sender: Specific sender to analyze (None for all)
            top_n: Number of top words to return
            min_length: Minimum word length to consider
            
        Returns:
            List of (word, count) tuples for the most common words
        """
        # Filter messages by sender if specified
        if sender:
            filtered_msgs = [m for m in messages if m['sender_name'] == sender]
        else:
            filtered_msgs = messages
        
        # Extract all words from messages
        all_words = []
        for msg in filtered_msgs:
            if 'content' in msg and msg['content']:
                # Convert to lowercase and split by common separators
                text = msg['content'].lower()
                # Replace common punctuation with spaces
                text = re.sub(r'[,.!?;:"\'\(\)\[\]\{\}]', ' ', text)
                # Split by whitespace and filter out short words
                words = [w.strip() for w in text.split() if len(w.strip()) >= min_length]
                all_words.extend(words)
        
        # Count word occurrences and return top N
        word_counts = Counter(all_words)
        return word_counts.most_common(top_n)
    
    @staticmethod
    def analyze_word_usage_by_sender(messages, top_n=50, min_length=1):
        """Analyze word usage for each sender.
        
        Returns:
            Dictionary mapping each sender to their most common words
        """
        # Get unique senders
        senders = set(m['sender_name'] for m in messages)
        
        # Find most common words for each sender
        result = {}
        for sender in senders:
            result[sender] = MessageAnalyzer.find_most_common_words(
                messages, sender, top_n, min_length)
        
        return result