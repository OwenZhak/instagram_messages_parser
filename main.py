import json
import tkinter as tk
from tkinter import filedialog, ttk
import os
import ctypes
from datetime import datetime
import re

# Enable DPI awareness for better text rendering on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

def decode_content(text):
    """Decode Unicode escape sequences to readable Russian text and emojis."""
    if not isinstance(text, str):
        return text
    
    try:
        # Special handling for emojis and Russian text in Instagram format
        # Step 1: Handle standard Instagram encoding
        decoded = bytes(text, 'latin1').decode('utf-8')
        
        return decoded
    
    except Exception as e:
        print(f"Primary decoding failed: {e}")
        # Alternative approaches
        try:
            # Try another common encoding pattern for emojis
            return bytes(text.encode('latin1')).decode('utf-8')
        except:
            try:
                # Last resort direct Unicode escape decoding
                return text.encode('ascii').decode('unicode_escape')
            except:
                return text

def parse_instagram_json(file_path):
    """Parse Instagram JSON file and extract messages with decoded content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        messages = []
        participants = [p.get('name', '') for p in data.get('participants', [])]
        print(f"Participants in chat: {participants}")
        
        for message in data.get('messages', []):
            sender = message.get('sender_name', '')
            
            # Handle regular messages with content
            if 'content' in message:
                content = message.get('content', '')
                # Skip reaction messages, likes, and edited messages
                if (content != "Liked a message" and 
                    not content.startswith("Reacted") and 
                    not content.startswith("Liked") and
                    "edited" not in content and
                    "to your message" not in content):
                        decoded_content = decode_content(content)
                        timestamp = message.get('timestamp_ms', 0)
                        
                        messages.append({
                            'sender_name': sender,
                            'content': decoded_content,
                            'timestamp': timestamp
                        })
        
        print(f"Parsed {len(messages)} messages from file")
        return {"messages": messages, "participants": participants}
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return {"messages": [], "participants": []}

class InstagramMessageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Message Viewer")
        self.root.geometry("1280x720")  # Larger default size
        
        # Set font scaling for better readability
        default_font = ('Segoe UI', 11)  # Use a font that supports emojis well
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection controls
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        self.select_button = ttk.Button(
            self.control_frame, 
            text="Select JSON Files", 
            command=self.select_files
        )
        self.select_button.pack(side=tk.LEFT, padx=5)
        
        self.files_label = ttk.Label(self.control_frame, text="No files selected", font=default_font)
        self.files_label.pack(side=tk.LEFT, padx=5)
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Tab 1: Statistics
        self.stats_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.stats_frame, text="Statistics")
        
        # Tab 2: Messages
        self.messages_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.messages_frame, text="Messages")
        
        # Tab 3: Longest Messages
        self.longest_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.longest_frame, text="20 Longest Messages")
        
        # Create text widgets for each tab with scrollbars
        # Statistics tab
        self.stats_scrollbar = ttk.Scrollbar(self.stats_frame)
        self.stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text = tk.Text(
            self.stats_frame, 
            wrap=tk.WORD, 
            yscrollcommand=self.stats_scrollbar.set,
            font=default_font
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_scrollbar.config(command=self.stats_text.yview)
        
        # Messages tab
        self.messages_scrollbar = ttk.Scrollbar(self.messages_frame)
        self.messages_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.messages_text = tk.Text(
            self.messages_frame, 
            wrap=tk.WORD, 
            yscrollcommand=self.messages_scrollbar.set,
            font=default_font
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True)
        self.messages_scrollbar.config(command=self.messages_text.yview)
        
        # Longest messages tab
        self.longest_scrollbar = ttk.Scrollbar(self.longest_frame)
        self.longest_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.longest_text = tk.Text(
            self.longest_frame,
            wrap=tk.WORD,
            yscrollcommand=self.longest_scrollbar.set,
            font=default_font
        )
        self.longest_text.pack(fill=tk.BOTH, expand=True)
        self.longest_scrollbar.config(command=self.longest_text.yview)
        
        # Configure text styles for all text widgets
        for text_widget in [self.stats_text, self.messages_text, self.longest_text]:
            text_widget.tag_configure("header", font=('Segoe UI', 14, "bold"))
            text_widget.tag_configure("subheader", font=('Segoe UI', 12, "bold"))
            text_widget.tag_configure("info", font=default_font)
            text_widget.tag_configure("time", font=('Segoe UI', 9), foreground="#757575")
            text_widget.config(tabs=("4c", "10c"))  # Set tab stops at 4cm and 10cm
        
        # The sender tags will be created dynamically based on participants found
        self.sender_colors = ["#1E88E5", "#43A047", "#FB8C00", "#E53935", "#8E24AA", "#00ACC1"]
        self.sender_tags = {}  # Will map sender names to tag names
        
        self.selected_files = []
        
    def select_files(self):
        """Open file dialog to select multiple JSON files."""
        file_paths = filedialog.askopenfilenames(
            title="Select Instagram JSON Files",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_paths:
            return
        
        self.selected_files = list(file_paths)
        self.files_label.config(text=f"{len(self.selected_files)} files selected")
        self.display_messages()
    
    def format_timestamp(self, timestamp_ms):
        """Convert millisecond timestamp to readable date format."""
        if not timestamp_ms:
            return ""
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def display_messages(self):
        """Display messages from selected JSON files."""
        # Clear all text widgets
        self.stats_text.delete(1.0, tk.END)
        self.messages_text.delete(1.0, tk.END)
        self.longest_text.delete(1.0, tk.END)
        
        all_messages = []
        all_participants = set()
        file_info = []
        
        # Process each selected file
        for file_path in self.selected_files:
            result = parse_instagram_json(file_path)
            messages = result["messages"]
            participants = result["participants"]
            
            all_messages.extend(messages)
            all_participants.update(participants)
            
            file_name = os.path.basename(file_path)
            file_info.append(f"{file_name}: {len(messages)} messages")
        
        # Create sender tags dynamically based on participants found
        self.sender_tags = {}
        for i, participant in enumerate(sorted(all_participants)):
            color_index = i % len(self.sender_colors)
            tag_name = f"sender_{i}"
            self.sender_tags[participant] = tag_name
            # Apply tags to all text widgets
            for text_widget in [self.stats_text, self.messages_text, self.longest_text]:
                text_widget.tag_configure(tag_name, 
                                        font=('Segoe UI', 11, "bold"), 
                                        foreground=self.sender_colors[color_index])
        
        # --- STATISTICS TAB ---
        self.stats_text.insert(tk.END, "CHAT INFORMATION\n", "header")
        self.stats_text.insert(tk.END, "----------------\n\n", "header")
        
        # Show participants
        self.stats_text.insert(tk.END, "Chat Participants:\n", "subheader")
        for participant in sorted(all_participants):
            tag = self.sender_tags[participant]
            self.stats_text.insert(tk.END, f"• {participant}\n", tag)
        self.stats_text.insert(tk.END, "\n")
        
        # Show files processed
        if file_info:
            self.stats_text.insert(tk.END, "Files Processed:\n", "subheader")
            for info in file_info:
                self.stats_text.insert(tk.END, f"• {info}\n", "info")
            self.stats_text.insert(tk.END, "\n")
        
        # Count messages and characters by sender
        sender_counts = {}
        sender_chars = {}
        for message in all_messages:
            sender = message['sender_name']
            content = message['content']
            
            # Count messages
            if sender not in sender_counts:
                sender_counts[sender] = 0
                sender_chars[sender] = 0
            
            sender_counts[sender] += 1
            sender_chars[sender] += len(content) if content else 0
        
        # Show message statistics
        self.stats_text.insert(tk.END, "Message Statistics:\n", "subheader")
        self.stats_text.insert(tk.END, f"• Total messages: {len(all_messages)}\n", "info")
        for sender, count in sender_counts.items():
            msg_percentage = (count / len(all_messages)) * 100 if all_messages else 0
            char_count = sender_chars[sender]
            tag = self.sender_tags.get(sender, "info")
            self.stats_text.insert(tk.END, f"• {sender}: {count} messages ({msg_percentage:.1f}%), {char_count} characters\n", tag)
        
        # --- LONGEST MESSAGES TAB ---
        # Find 20 longest messages
        valid_messages = [msg for msg in all_messages if msg.get('content')]
        longest_messages = sorted(valid_messages, 
                                key=lambda x: len(x['content']), 
                                reverse=True)[:20]
        
        self.longest_text.insert(tk.END, "20 LONGEST MESSAGES\n", "header")
        self.longest_text.insert(tk.END, "-------------------\n\n", "header")
        
        # Display the longest messages
        for i, message in enumerate(longest_messages, 1):
            sender = message['sender_name']
            content = message['content']
            timestamp = self.format_timestamp(message.get('timestamp', 0))
            char_count = len(content)
            
            # Get sender tag for colorization
            tag = self.sender_tags.get(sender, "info")
            
            # Display message header with count, sender, timestamp and character count
            self.longest_text.insert(tk.END, f"{i}. ", "info")
            self.longest_text.insert(tk.END, f"{sender}", tag)
            self.longest_text.insert(tk.END, f" ({timestamp}, {char_count} characters):\n", "info")
            
            # Display content - if it's very long (>1000 chars), truncate with ellipsis
            if len(content) > 1000:
                preview = content[:997] + "..."
                self.longest_text.insert(tk.END, f"{preview}\n\n", "info")
            else:
                self.longest_text.insert(tk.END, f"{content}\n\n", "info")
        
        # --- MESSAGES TAB ---
        self.messages_text.insert(tk.END, "MESSAGES (Chronological Order)\n", "header")
        self.messages_text.insert(tk.END, "------------------------------\n\n", "header")
        
        # Sort messages by timestamp (newest first)
        all_messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Display all messages in chronological order
        for message in all_messages:
            timestamp = self.format_timestamp(message.get('timestamp', 0))
            self.messages_text.insert(tk.END, f"[{timestamp}]\t", "time")
            
            # Use different colors for different senders dynamically
            sender = message['sender_name']
            tag = self.sender_tags.get(sender, "info")
            
            # Use tab for alignment
            self.messages_text.insert(tk.END, f"{sender}:\t", tag)
            
            # Insert content after the tab stop
            self.messages_text.insert(tk.END, f"{message['content']}\n\n")

def main():
    root = tk.Tk()
    app = InstagramMessageViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()