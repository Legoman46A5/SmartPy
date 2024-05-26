import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import json
import os
import threading
from datetime import datetime, timedelta
import time

class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List")
        self.root.geometry("800x500")
        self.tasks = []
        self.notifications_enabled = True
        self.theme = "light"

        # Chargement des paramètres
        self.load_settings()

        # Style général
        self.set_theme(self.theme)

        # Frame pour l'entrée et le bouton d'ajout
        self.input_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.input_frame.pack(pady=10, fill=tk.X)

        self.task_label = ttk.Label(self.input_frame, text="Tâche:", style="TLabel")
        self.task_label.pack(side=tk.LEFT, padx=5)

        self.task_entry = ttk.Entry(self.input_frame, width=30, font=self.font_style)
        self.task_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.date_label = ttk.Label(self.input_frame, text="Date butoir:", style="TLabel")
        self.date_label.pack(side=tk.LEFT, padx=5)

        self.date_entry = DateEntry(self.input_frame, width=12, background='darkblue', foreground='white', borderwidth=2, font=self.font_style)
        self.date_entry.pack(side=tk.LEFT, padx=5)

        self.priority_label = ttk.Label(self.input_frame, text="Priorité:", style="TLabel")
        self.priority_label.pack(side=tk.LEFT, padx=5)

        self.priority_var = tk.StringVar()
        self.priority_options = ["Haute", "Moyenne", "Basse"]
        self.priority_menu = ttk.Combobox(self.input_frame, textvariable=self.priority_var, values=self.priority_options)
        self.priority_var.set("Moyenne")
        self.priority_menu.pack(side=tk.LEFT, padx=5)

        self.add_task_button = ttk.Button(self.input_frame, text="Ajouter tâche", command=self.open_content_popup, style="TButton")
        self.add_task_button.pack(side=tk.LEFT, padx=5)

        # Bouton de paramètres
        self.settings_button = ttk.Button(self.input_frame, text="Paramètres", command=self.open_settings, style="TButton")
        self.settings_button.pack(side=tk.LEFT, padx=5)

        # Frame pour la recherche et le filtrage
        self.filter_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.filter_frame.pack(pady=10, fill=tk.X)

        self.search_label = ttk.Label(self.filter_frame, text="Rechercher:", style="TLabel")
        self.search_label.pack(side=tk.LEFT, padx=5)

        self.search_entry = ttk.Entry(self.filter_frame, width=30, font=self.font_style)
        self.search_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.search_entry.bind('<KeyRelease>', self.filter_tasks)

        self.filter_by_label = ttk.Label(self.filter_frame, text="Filtrer par:", style="TLabel")
        self.filter_by_label.pack(side=tk.LEFT, padx=5)

        self.filter_var = tk.StringVar()
        self.filter_options = ["Tous", "Date butoir", "Contenu"]
        self.filter_menu = ttk.Combobox(self.filter_frame, textvariable=self.filter_var, values=self.filter_options)
        self.filter_var.set("Tous")
        self.filter_menu.pack(side=tk.LEFT, padx=5)

        # Frame principale pour les listes et les détails
        self.main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.tasks_frame = ttk.Frame(self.main_frame, padding="10 10 10 10")
        self.tasks_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tasks_listbox = tk.Listbox(self.tasks_frame, width=50, height=15, font=self.font_style, background=self.entry_bg_color, foreground=self.fg_color)
        self.tasks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tasks_frame, orient=tk.VERTICAL)
        self.scrollbar.config(command=self.tasks_listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tasks_listbox.config(yscrollcommand=self.scrollbar.set)
        self.tasks_listbox.bind('<<ListboxSelect>>', self.display_task_content)
        
        # Frame pour les détails de la tâche (initialement masquée)
        self.details_frame = ttk.Frame(self.main_frame, padding="10 10 10 10")

        self.details_label = ttk.Label(self.details_frame, text="Détails de la tâche:", style="TLabel")
        self.details_label.pack(pady=10)

        self.content_text = tk.Text(self.details_frame, width=50, height=15, font=self.font_style, background=self.entry_bg_color, foreground=self.fg_color)
        self.content_text.pack(fill=tk.BOTH, expand=True)

        self.update_priority_label = ttk.Label(self.details_frame, text="Changer la priorité:", style="TLabel")
        self.update_priority_label.pack(pady=5)

        self.update_priority_var = tk.StringVar()
        self.update_priority_menu = ttk.Combobox(self.details_frame, textvariable=self.update_priority_var, values=self.priority_options)
        self.update_priority_var.set("Moyenne")
        self.update_priority_menu.pack(pady=5)

        self.update_task_button = ttk.Button(self.details_frame, text="Mettre à jour le contenu et la priorité", command=self.update_task_content, style="TButton")
        self.update_task_button.pack(pady=10)

        # Bouton pour supprimer une tâche
        self.delete_task_button = ttk.Button(self.root, text="Supprimer tâche", command=self.delete_task, style="TButton")
        self.delete_task_button.pack(pady=10)

        self.root.bind("<Button-1>", self.hide_details_frame)

        # Chargement des tâches depuis un fichier après avoir défini les widgets
        self.load_tasks()
        self.display_all_tasks()

        # Démarrage de la vérification des rappels
        self.reminder_thread = threading.Thread(target=self.check_reminders)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()

    def set_theme(self, theme):
        style = ttk.Style()
        style.theme_use('clam')  # Using 'clam' for better ttk compatibility
        if theme == "light":
            self.bg_color = "#f7f7f7"
            self.fg_color = "#333"
            self.entry_bg_color = "#fff"
            style.configure("TLabel", background="#f7f7f7", foreground="#333")
            style.configure("TFrame", background="#f7f7f7")
            style.configure("TButton", background="#4CAF50", foreground="#fff")
        else:
            self.bg_color = "#333"
            self.fg_color = "#f7f7f7"
            self.entry_bg_color = "#555"
            style.configure("TLabel", background="#333", foreground="#f7f7f7")
            style.configure("TFrame", background="#333")
            style.configure("TButton", background="#555", foreground="#fff")
        self.font_style = ("Helvetica", 12)

    def open_settings(self):
        def save_settings():
            self.theme = theme_var.get()
            self.notifications_enabled = notifications_var.get() == "Oui"
            self.set_theme(self.theme)
            self.apply_theme()
            self.save_settings()
            settings_window.destroy()
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Paramètres")
        settings_window.geometry("400x300")
        settings_window.config(bg=self.bg_color)

        theme_label = ttk.Label(settings_window, text="Thème:", style="TLabel")
        theme_label.pack(pady=10)

        theme_var = tk.StringVar(value=self.theme)
        theme_options = ["light", "dark"]
        theme_menu = ttk.Combobox(settings_window, textvariable=theme_var, values=theme_options)
        theme_menu.pack(pady=10)

        notifications_label = ttk.Label(settings_window, text="Activer les notifications:", style="TLabel")
        notifications_label.pack(pady=10)

        notifications_var = tk.StringVar(value="Oui" if self.notifications_enabled else "Non")
        notifications_options = ["Oui", "Non"]
        notifications_menu = ttk.Combobox(settings_window, textvariable=notifications_var, values=notifications_options)
        notifications_menu.pack(pady=10)

        save_button = ttk.Button(settings_window, text="Enregistrer", command=save_settings, style="TButton")
        save_button.pack(pady=20)

    def apply_theme(self):
        self.root.config(bg=self.bg_color)
        self.input_frame.config(style="TFrame")
        self.filter_frame.config(style="TFrame")
        self.main_frame.config(style="TFrame")
        self.tasks_frame.config(style="TFrame")
        self.details_frame.config(style="TFrame")
        self.tasks_listbox.config(background=self.entry_bg_color, foreground=self.fg_color)

    def open_content_popup(self):
        task = self.task_entry.get()
        due_date = self.date_entry.get()
        priority = self.priority_var.get()

        if task == "":
            messagebox.showwarning("Attention", "Vous devez entrer une tâche.")
            return

        def add_task_content():
            content = content_text.get("1.0", tk.END).strip()
            if content:
                task_details = {"task": task, "due_date": due_date, "priority": priority, "content": content}
                self.tasks.append(task_details)
                self.sort_tasks()
                self.display_all_tasks()
                self.task_entry.delete(0, tk.END)
                popup.destroy()
                self.save_tasks()  # Sauvegarde après ajout
            else:
                messagebox.showwarning("Attention", "Vous devez entrer un contenu.")

        # Création de la fenêtre popup pour le contenu
        popup = tk.Toplevel(self.root)
        popup.title("Contenu de la tâche")
        popup.geometry("600x400")
        popup.config(bg=self.bg_color)

        content_label = ttk.Label(popup, text="Contenu:", style="TLabel")
        content_label.pack(pady=10)

        content_text = tk.Text(popup, width=70, height=15, font=self.font_style, background=self.entry_bg_color, foreground=self.fg_color)
        content_text.pack(pady=10)

        add_content_button = ttk.Button(popup, text="Ajouter contenu", command=add_task_content, style="TButton")
        add_content_button.pack(pady=10)

    def display_task_content(self, event):
        try:
            selected_task_index = self.tasks_listbox.curselection()[0]
            task_details = self.tasks[selected_task_index]
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert(tk.END, task_details["content"])
            self.update_priority_var.set(task_details["priority"])
            self.details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        except IndexError:
            pass

    def update_task_content(self):
        try:
            selected_task_index = self.tasks_listbox.curselection()[0]
            new_content = self.content_text.get("1.0", tk.END).strip()
            new_priority = self.update_priority_var.get()
            if new_content:
                self.tasks[selected_task_index]["content"] = new_content
                self.tasks[selected_task_index]["priority"] = new_priority
                messagebox.showinfo("Succès", "Le contenu et la priorité de la tâche ont été mis à jour.")
                self.sort_tasks()
                self.display_all_tasks()
                self.save_tasks()  # Sauvegarde après mise à jour
            else:
                messagebox.showwarning("Attention", "Le contenu ne peut pas être vide.")
        except IndexError:
            messagebox.showwarning("Attention", "Vous devez sélectionner une tâche.")

    def delete_task(self):
        try:
            selected_task_index = self.tasks_listbox.curselection()[0]
            self.tasks_listbox.delete(selected_task_index)
            del self.tasks[selected_task_index]
            self.content_text.delete("1.0", tk.END)
            self.details_frame.pack_forget()
            self.save_tasks()  # Sauvegarde après suppression
        except IndexError:
            messagebox.showwarning("Attention", "Vous devez sélectionner une tâche.")

    def hide_details_frame(self, event):
        if event.widget not in [self.tasks_listbox, self.content_text, self.update_task_button, self.update_priority_menu]:
            self.details_frame.pack_forget()

    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump(self.tasks, f)

    def load_tasks(self):
        if os.path.exists("tasks.json"):
            with open("tasks.json", "r") as f:
                self.tasks = json.load(f)
            self.sort_tasks()

    def save_settings(self):
        settings = {
            "theme": self.theme,
            "notifications_enabled": self.notifications_enabled
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.theme = settings.get("theme", "light")
                self.notifications_enabled = settings.get("notifications_enabled", True)
                self.set_theme(self.theme)

    def display_all_tasks(self):
        self.tasks_listbox.delete(0, tk.END)
        for task in self.tasks:
            self.tasks_listbox.insert(tk.END, f"{task['task']} (Date butoir: {task['due_date']}) [Priorité: {task['priority']}]")

    def filter_tasks(self, event=None):
        query = self.search_entry.get().strip().lower()
        filter_option = self.filter_var.get()

        filtered_tasks = []
        for task in self.tasks:
            task_str = f"{task['task']} (Date butoir: {task['due_date']})"
            if filter_option == "Date butoir" and query in task['due_date'].lower():
                filtered_tasks.append(task)
            elif filter_option == "Contenu" and query in task['content'].lower():
                filtered_tasks.append(task)
            elif filter_option == "Tous" and (query in task['task'].lower() or query in task['due_date'].lower() or query in task['content'].lower()):
                filtered_tasks.append(task)

        self.tasks_listbox.delete(0, tk.END)
        for task in filtered_tasks:
            self.tasks_listbox.insert(tk.END, f"{task['task']} (Date butoir: {task['due_date']}) [Priorité: {task['priority']}]")

    def sort_tasks(self):
        priority_order = {"Haute": 1, "Moyenne": 2, "Basse": 3}
        self.tasks.sort(key=lambda x: priority_order[x["priority"]])

    def check_reminders(self):
        while True:
            if self.notifications_enabled:
                now = datetime.now()
                reminder_time = now + timedelta(minutes=30)
                for task in self.tasks:
                    due_date = datetime.strptime(task['due_date'], "%m/%d/%y")
                    if now < due_date < reminder_time:
                        messagebox.showinfo("Rappel", f"La tâche '{task['task']}' est prévue pour bientôt.")
            time.sleep(60 * 10)  # Vérifier toutes les 10 minutes

if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)
    root.mainloop()
