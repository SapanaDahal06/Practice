import tkinter as tk
import time
import random

# ---------------------------
# 🌟 ChatBot Response Logic
# ---------------------------
def get_response(user_input):
    user_input = user_input.lower()

    # Basic memory
    global user_name

    if "my name is" in user_input:
        user_name = user_input.split("is")[-1].strip().capitalize()
        return f"Nice to meet you, {user_name}! 😊"

    if "your name" in user_input:
        return "I'm ChatBox, your Python-powered assistant 🤖"

    if "hello" in user_input or "hi" in user_input:
        return random.choice([
            "Hey there! 👋", 
            "Hello! How are you doing?", 
            "Hi! Nice to see you 😊"
        ])

    if "how are you" in user_input:
        return "I'm doing great, thanks for asking! How about you?"

    if "time" in user_input:
        current_time = time.strftime("%I:%M %p")
        return f"The current time is {current_time} 🕒"

    if "joke" in user_input:
        jokes = [
            "Why did the computer show up at work late? It had a hard drive! 😂",
            "I told my laptop a joke... it didn’t laugh, it just crashed 😅",
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐞"
        ]
        return random.choice(jokes)

    if "bye" in user_input or "exit" in user_input:
        return "Goodbye! Have a great day! 👋"

    if user_name:
        return f"Sorry {user_name}, I’m not sure about that 🤔"
    else:
        return "Sorry, I didn’t quite get that. Try saying something else!"

# ---------------------------
# 🪄 GUI Setup (tkinter)
# ---------------------------
def send_message():
    user_input = entry.get().strip()
    if not user_input:
        return
    
    chat_window.insert(tk.END, f"You: {user_input}\n", "user")
    entry.delete(0, tk.END)

    bot_response = get_response(user_input)
    chat_window.insert(tk.END, f"ChatBox: {bot_response}\n\n", "bot")

    chat_window.see(tk.END)

# ---------------------------
# 🌈 Window Design
# ---------------------------
window = tk.Tk()
window.title("💬 ChatBox - Your Python Assistant")
window.configure(bg="#1e1e2f")

chat_window = tk.Text(window, height=20, width=60, bg="#2b2b3d", fg="white", font=("Consolas", 11), wrap="word", bd=0, padx=10, pady=10)
chat_window.pack(padx=10, pady=10)
chat_window.tag_config("user", foreground="#90ee90")
chat_window.tag_config("bot", foreground="#00ffff")

frame = tk.Frame(window, bg="#1e1e2f")
frame.pack(pady=5)

entry = tk.Entry(frame, width=45, font=("Consolas", 11), bg="#3c3c54", fg="white", insertbackground="white", bd=2)
entry.pack(side=tk.LEFT, padx=5, pady=5)

send_button = tk.Button(frame, text="Send 🚀", command=send_message, bg="#00bfff", fg="white", font=("Consolas", 11, "bold"), bd=0, padx=10, pady=5, activebackground="#00a3cc")
send_button.pack(side=tk.LEFT)

chat_window.insert(tk.END, "ChatBox: Hello there! I'm your Python assistant 🤖\nType 'my name is [your name]' to get started!\n\n", "bot")

user_name = ""

window.mainloop()
