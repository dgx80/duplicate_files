import os
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import Counter

def select_folder(folder_label):
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_label.config(text=folder_path)

def find_duplicate_files(root_folder, show_top_10, show_all_files):
    file_dict = {}
    total_files = 0
    # Parcours de l'arborescence
    for dirpath, _, filenames in os.walk(root_folder):
        total_files += len(filenames)
        for filename in filenames:
            # Création d'une liste pour chaque nom de fichier trouvé
            if filename not in file_dict:
                file_dict[filename] = []
            file_dict[filename].append(os.path.join(dirpath, filename))
    
    duplicates = {k: v for k, v in file_dict.items() if len(v) > 1}
    
    if duplicates:
        result = f"Total files scanned: {total_files}\n"
        if show_all_files:
            result += "Duplicate files found:\n"
            folder_count = Counter()
            for filename, paths in duplicates.items():
                result += f"\n{filename} found in:\n"
                result += "\n".join(paths) + "\n"
                for path in paths:
                    folder_count[os.path.dirname(path)] += 1
            
            if show_top_10:
                # Top 10 folders with the most duplicates
                result += "\nTop 10 folders with the most duplicates:\n"
                for folder, count in folder_count.most_common(10):
                    result += f"{folder}: {count} duplicates\n"
        elif show_top_10:
            folder_count = Counter()
            for paths in duplicates.values():
                for path in paths:
                    folder_count[os.path.dirname(path)] += 1
            # Top 10 folders with the most duplicates
            result += "\nTop 10 folders with the most duplicates:\n"
            for folder, count in folder_count.most_common(10):
                result += f"{folder}: {count} duplicates\n"
        display_result(result)
    else:
        messagebox.showinfo("No Duplicates", f"Total files scanned: {total_files}\nNo duplicate files were found.")

def display_result(result):
    result_window = tk.Toplevel()
    result_window.title("Duplicate Files Found")
    text_frame = tk.Frame(result_window)
    text_frame.pack(expand=True, fill='both')

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side='right', fill='y')

    text_box = tk.Text(text_frame, wrap='word', width=100, height=30, yscrollcommand=scrollbar.set)
    text_box.insert('1.0', result)
    text_box.config(state='disabled')  # Rend le texte non-éditable
    text_box.pack(expand=True, fill='both')

    scrollbar.config(command=text_box.yview)

    close_button = tk.Button(result_window, text="Close", command=result_window.destroy)
    close_button.pack(pady=10)
    result_window.mainloop()  # Assure que la fenêtre reste ouverte jusqu'à ce qu'elle soit fermée

def main():
    def start_search():
        folder = folder_label.cget("text")
        if not folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder before starting the search.")
            return
        show_top_10 = top_10_var.get()
        show_all_files = all_files_var.get()
        find_duplicate_files(folder, show_top_10, show_all_files)

    root = tk.Tk()
    root.title("Duplicate File Finder")
    root.geometry("500x300")

    select_folder_button = tk.Button(root, text="Select Folder...", command=lambda: select_folder(folder_label))
    select_folder_button.pack(pady=10)

    folder_label = tk.Label(root, text="", fg="blue")
    folder_label.pack()

    top_10_var = tk.BooleanVar()
    top_10_check = tk.Checkbutton(root, text="Show Top 10 Folders with Most Duplicates", variable=top_10_var)
    top_10_check.pack(pady=5)

    all_files_var = tk.BooleanVar()
    all_files_check = tk.Checkbutton(root, text="Show All Duplicate Files", variable=all_files_var)
    all_files_check.pack(pady=5)

    start_button = tk.Button(root, text="Search Files", command=start_search)
    start_button.pack(pady=20)

    root.mainloop()  # S'assure que l'application principale Tkinter reste active

if __name__ == "__main__":
    main()