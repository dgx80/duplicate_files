import os
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import Counter, defaultdict
from tkinter.ttk import Progressbar
from ttkthemes import ThemedTk

def main():
    # Initialisation de l'interface principale
    root = ThemedTk(theme="arc")
    root.title("Duplicate File Finder")
    root.geometry("500x350")

    # Entry pour afficher le chemin du dossier sélectionné
    folder_entry = tk.Entry(root, state='readonly', fg='blue', readonlybackground='lightgrey')
    folder_entry.pack(pady=10)

    # Barre de progression pour indiquer l'avancement de la recherche
    progress = Progressbar(root, orient='horizontal', length=300, mode='determinate')
    progress.pack(pady=10)

    # Variables globales
    global cancel_search
    cancel_search = False

    # Sélection du dossier
    def select_folder():
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_entry.config(state='normal')
            folder_entry.delete(0, 'end')
            folder_entry.insert(0, folder_path)
            folder_entry.config(state='readonly')
            start_button.config(state='normal')
            messagebox.showinfo("Folder Selected", "Le dossier a été correctement sélectionné.")

    # Annulation de la recherche
    def cancel():
        global cancel_search
        cancel_search = True

    # Recherche des fichiers dupliqués
    def find_duplicate_files(root_folder, show_top_10, show_all_files):
        global cancel_search
        cancel_search = False
        file_dict = defaultdict(list)
        total_files = 0
        files_processed = 0

        # Parcours de l'arborescence
        for dirpath, _, filenames in os.walk(root_folder):
            if cancel_search:
                messagebox.showinfo("Search Cancelled", "La recherche a été annulée.")
                return

            total_files += len(filenames)

        progress["maximum"] = total_files

        for dirpath, _, filenames in os.walk(root_folder):
            if cancel_search:
                messagebox.showinfo("Search Cancelled", "La recherche a été annulée.")
                return

            for filename in filenames:
                if cancel_search:
                    messagebox.showinfo("Search Cancelled", "La recherche a été annulée.")
                    return

                # Création d'une liste pour chaque nom de fichier trouvé
                file_dict[filename].append(os.path.join(dirpath, filename))

                files_processed += 1
                if files_processed % 100 == 0:  # Mise à jour de la progression tous les 100 fichiers
                    progress["value"] = files_processed
                    root.update_idletasks()
        
        # Mise à jour finale de la barre de progression
        progress["value"] = total_files
        root.update_idletasks()

        # Filtrer les fichiers dupliqués
        duplicates = {k: v for k, v in file_dict.items() if len(v) > 1}
        
        # Affichage des résultats
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

    # Affichage des résultats
    def display_result(result):
        result_window = tk.Toplevel()
        result_window.title("Duplicate Files Found")
        text_frame = tk.Frame(result_window)
        text_frame.pack(expand=True, fill='both')

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')

        text_box = tk.Text(text_frame, wrap='word', width=100, height=30, yscrollcommand=scrollbar.set)
        text_box.insert('1.0', result)
        text_box.config(state='normal')  # Permet de sélectionner du texte
        text_box.pack(expand=True, fill='both')

        def copy_selection(event):
            result_window.clipboard_clear()
            result_window.clipboard_append(text_box.selection_get())

        text_box.bind('<Button-3>', copy_selection)  # Clic droit pour copier

        scrollbar.config(command=text_box.yview)

        close_button = tk.Button(result_window, text="Close", command=result_window.destroy)
        close_button.pack(pady=10)

        result_window.mainloop()

    # Lancer la recherche
    def start_search():
        folder = folder_entry.get()
        if not folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder before starting the search.")
            return
        show_top_10 = top_10_var.get()
        show_all_files = all_files_var.get()
        find_duplicate_files(folder, show_top_10, show_all_files)

    # Bouton pour sélectionner le dossier
    select_folder_button = tk.Button(root, text="Select Folder...", command=select_folder)
    select_folder_button.pack(pady=10)

    # Bouton pour lancer la recherche
    start_button = tk.Button(root, text="Search Files", command=start_search, state='disabled')
    start_button.pack(pady=20)

    # Bouton pour annuler la recherche
    cancel_button = tk.Button(root, text="Cancel", command=cancel)
    cancel_button.pack(pady=5)

    # Checkbox pour les options d'affichage
    top_10_var = tk.BooleanVar()
    top_10_check = tk.Checkbutton(root, text="Show Top 10 Folders with Most Duplicates", variable=top_10_var)
    top_10_check.pack(pady=5)

    all_files_var = tk.BooleanVar()
    all_files_check = tk.Checkbutton(root, text="Show All Duplicate Files", variable=all_files_var)
    all_files_check.pack(pady=5)

    # Lancer l'application principale
    root.mainloop()

if __name__ == "__main__":
    main()