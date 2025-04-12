import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import openai
import os
import shutil
from utils import ask_gpt
from excel_analyzer import analyze_order_file


# Create folders if not exist
os.makedirs("history", exist_ok=True)
os.makedirs("uploads", exist_ok=True)


class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚚 Logistics Chatbot Pro")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f2f5")


        self.dark_mode = False  # Dark mode status


        # Title
        title = tk.Label(root, text="Logistics Chatbot", font=("Helvetica", 20, "bold"), bg="#f0f2f5")
        title.pack(pady=10)


        # Chat history area
        self.chat_area = scrolledtext.ScrolledText(root, font=("Helvetica", 12), wrap=tk.WORD, bg="white")
        self.chat_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.chat_area.config(state=tk.DISABLED)


        # Theme switch button
        theme_btn = tk.Button(root, text="🌓 Switch Theme", command=self.toggle_theme, bg="#9C27B0", fg="white", font=("Helvetica", 12, "bold"))
        theme_btn.pack(pady=5)


        # Input Frame
        input_frame = tk.Frame(root, bg="#f0f2f5")
        input_frame.pack(pady=10)


        self.input_entry = tk.Entry(input_frame, font=("Helvetica", 14), width=60)
        self.input_entry.grid(row=0, column=0, padx=5)


        send_btn = tk.Button(input_frame, text="Send", command=self.send_message, bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
        send_btn.grid(row=0, column=1, padx=5)


        upload_btn = tk.Button(root, text="📄 Upload Excel", command=self.upload_file, bg="#2196F3", fg="white", font=("Helvetica", 12, "bold"))
        upload_btn.pack(pady=5)


        # Quick Questions
        quick_frame = tk.Frame(root, bg="#f0f2f5")
        quick_frame.pack(pady=10)


        quick_questions = [
            "How to optimize warehouse operations?",
            "Best practices in supply chain management?",
            "How to reduce trucking costs?",
            "What is 3PL in logistics?"
        ]


        for idx, question in enumerate(quick_questions):
            btn = tk.Button(
                quick_frame, text=question,
                command=lambda q=question: self.quick_question(q),
                bg="#607D8B", fg="white", font=("Helvetica", 10)
            )
            btn.grid(row=idx // 2, column=idx % 2, padx=5, pady=5)


    def toggle_theme(self):
        if self.dark_mode:
            self.root.configure(bg="#f0f2f5")
            self.chat_area.configure(bg="white", fg="black")
            self.dark_mode = False
        else:
            self.root.configure(bg="#2c2f33")
            self.chat_area.configure(bg="#23272a", fg="white")
            self.dark_mode = True


    def send_message(self):
        user_message = self.input_entry.get().strip()
        if not user_message:
            messagebox.showwarning("Warning", "Please enter a message!")
            return


        self.display_message("You", user_message)


        bot_response = ask_gpt(user_message)
        self.display_message("Bot", bot_response)


        self.input_entry.delete(0, tk.END)


        # Save history
        self.save_chat()


    def upload_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx")]
        )
        if file_path:
            try:
                dest_path = os.path.join("uploads", os.path.basename(file_path))
                shutil.copy(file_path, dest_path)
                result = analyze_order_file(dest_path)
                self.display_message("Bot", result)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload file: {e}")


    def display_message(self, sender, message):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)


    def save_chat(self):
        chat_text = self.chat_area.get("1.0", tk.END)
        with open("history/chat_history.txt", "w", encoding="utf-8") as f:
            f.write(chat_text)


    def quick_question(self, question):
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, question)
        self.send_message()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()







excel_analyzer.py
import pandas as pd


def analyze_order_file(filepath):
    try:
        df = pd.read_excel(filepath)


        summary = f"✅ File loaded successfully with {len(df)} records.\n"


        if 'Order Date' in df.columns:
            df['Order Date'] = pd.to_datetime(df['Order Date'])
            earliest = df['Order Date'].min().date()
            latest = df['Order Date'].max().date()
            summary += f"• Orders from {earliest} to {latest}\n"


        if 'Country' in df.columns:
            countries = df['Country'].nunique()
            summary += f"• Delivered to {countries} countries\n"


        if 'Order Value' in df.columns:
            total_value = df['Order Value'].sum()
            summary += f"• Total Order Value: ${total_value:,.2f}\n"


        return summary
    except Exception as e:
        return f"Error analyzing file: {e}"




