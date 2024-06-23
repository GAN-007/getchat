import openai
import sqlite3
import datetime
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
import threading
import time
import os
from tokenManager import TokenManager

# Initialize TokenManager (optional, for users with an API key)
api_key_file = "api_key.txt"
if os.path.exists(api_key_file):
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
        tokens = [api_key]  # Assume the API key is the token
else:
    tokens = []
    api_key = None

token_manager = TokenManager(api_key, tokens)

# Create a SQLite database or connect to it if it already exists
conn = sqlite3.connect('chat_history.db')
c = conn.cursor()

# Create a table to store chat history
c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
                user_input TEXT,
                gpt_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
             )''')
conn.commit()

def store_chat(user_input, gpt_response):
    """Store the chat interaction in the database."""
    c.execute("INSERT INTO chat_history (user_input, gpt_response) VALUES (?, ?)", (user_input, gpt_response))
    conn.commit()

def retrieve_chat_history():
    """Retrieve and return the entire chat history."""
    c.execute("SELECT * FROM chat_history")
    rows = c.fetchall()
    history = ""
    for row in rows:
        history += f"ID: {row[0]}\nUser Input: {row[1]}\nGPT Response: {row[2]}\nTimestamp: {row[3]}\n--------\n"
    return history

def chat_with_gpt(prompt):
    """Interact with OpenAI GPT and store the interaction."""
    token = token_manager.get_next_token()
    if token is None:
        # Mock response for users without an API key
        gpt_response = f"Simulated response for input: {prompt}"
    else:
        response = openai.Completion.create(
            engine="davinci-codex",
            prompt=prompt,
            max_tokens=150,
            api_key=token
        )
        gpt_response = response.choices[0].text.strip()
        token_manager.log_token_usage(token)
    store_chat(prompt, gpt_response)
    return gpt_response

def send_input():
    """Send user input to GPT and display the response."""
    user_input = user_input_field.get("1.0", tk.END).strip()
    if user_input:
        chat_display.insert(tk.END, f"You: {user_input}\n")
        chat_display.see(tk.END)
        loading_animation()
        gpt_reply = chat_with_gpt(user_input)
        chat_display.insert(tk.END, f"GPT: {gpt_reply}\n\n")
        user_input_field.delete("1.0", tk.END)

def display_history():
    """Display the chat history in the chat display."""
    history = retrieve_chat_history()
    chat_display.insert(tk.END, f"\nChat History:\n\n{history}\n")

def loading_animation():
    """Display a loading animation."""
    loading_label = tk.Label(root, text="Loading...", bg='black', fg='green', font=("Courier", 12))
    loading_label.pack(pady=5)
    root.update_idletasks()
    time.sleep(2)  # Simulate a delay for loading
    loading_label.destroy()

def start_chat():
    """Start the chat interaction."""
    threading.Thread(target=send_input).start()

# Create the main application window
root = tk.Tk()
root.title("Chat with OpenAI GPT")
root.configure(bg='black')

# Create and configure the chat display
chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg='black', fg='green', font=("Courier", 12))
chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create and configure the user input field
user_input_field = tk.Text(root, height=3, bg='black', fg='green', font=("Courier", 12))
user_input_field.pack(padx=10, pady=10, fill=tk.X)

# Create the send button
send_button = tk.Button(root, text="Send", command=start_chat, bg='black', fg='green', font=("Courier", 12))
send_button.pack(padx=10, pady=5)

# Create the display history button
history_button = tk.Button(root, text="Display History", command=display_history, bg='black', fg='green', font=("Courier", 12))
history_button.pack(padx=10, pady=5)

# Start the main event loop
root.mainloop()

# Close the connection to the database
conn.close()
