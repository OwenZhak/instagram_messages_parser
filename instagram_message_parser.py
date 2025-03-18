import json
from datetime import datetime

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