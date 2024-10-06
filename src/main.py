import os
import tkinter as tk
from tkinter import filedialog, messagebox

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        find_duplicate_files(folder_path)

def find_duplicate_files(root_folder):
    file_dict = {}
    # Parcours de l'arborescence
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            # Création d'une liste pour chaque nom de fichier trouvé
            if filename not in file_dict:
                file_dict[filename] = []
            file_dict[filename].append(os.path.join(dirpath, filename))
    
    duplicates = {k: v for k, v in file_dict.items() if len(v) > 1}
    
    if duplicates:
        result = "Duplicate files found:\n"
        count_files = 0
        for filename, paths in duplicates.items():
            result += f"\n{filename} found in:\n"
            result += "\n".join(paths) + "\n"
            count_files += 1
        display_result(result, count_files)
    else:
        messagebox.showinfo("No Duplicates", "No duplicate files were found.")

def display_result(result, count: int):
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
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showinfo("Select Folder", "Please select a folder to search for duplicate files.")
    select_folder()
    root.mainloop()  # S'assure que l'application principale Tkinter reste active

if __name__ == "__main__":
    main()