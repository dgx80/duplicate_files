import os
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import Counter, defaultdict
from tkinter.ttk import Progressbar
from ttkthemes import ThemedTk
import threading
import queue
import hashlib

def main():
    # Initialisation de l'interface principale
    root = ThemedTk(theme="arc")
    root.title("Duplicate File Finder")
    root.geometry("600x600")

    # Entry pour afficher le chemin du dossier sélectionné
    folder_entry = tk.Entry(root, state='readonly', fg='blue', readonlybackground='lightgrey')
    folder_entry.pack(pady=10)

    # Barre de progression pour indiquer l'avancement de la recherche
    progress = Progressbar(root, orient='horizontal', length=300, mode='determinate')
    progress.pack(pady=10)

    # Variables globales
    global cancel_search, duplicates
    cancel_search = False
    result_queue = queue.Queue()
    duplicates = {}

    # Sélection du dossier
    def select_folder():
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_entry.config(state='normal')
            folder_entry.delete(0, 'end')
            folder_entry.insert(0, folder_path)
            folder_entry.config(state='readonly')
            start_button.config(state='normal')
            rename_button.config(state='normal')
            messagebox.showinfo("Folder Selected", "Le dossier a été correctement sélectionné.")

    # Annulation de la recherche
    def cancel():
        global cancel_search
        cancel_search = True

    # Recherche des fichiers dupliqués
    def find_duplicate_files(root_folder, show_top_10, show_all_files, result_queue):
        global cancel_search, duplicates
        cancel_search = False
        file_dict = defaultdict(list)
        total_files = 0
        files_processed = 0

        # Parcours de l'arborescence
        for dirpath, _, filenames in os.walk(root_folder):
            if cancel_search:
                result_queue.put("cancelled")
                return

            total_files += len(filenames)

        progress["maximum"] = total_files

        for dirpath, _, filenames in os.walk(root_folder):
            if cancel_search:
                result_queue.put("cancelled")
                return

            for filename in filenames:
                if cancel_search:
                    result_queue.put("cancelled")
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
        
        # Préparer les résultats
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
            result_queue.put(result)
        else:
            result_queue.put(f"Total files scanned: {total_files}\nNo duplicate files were found.")

    # Comparaison des fichiers dupliqués
    def compare_duplicates():
        comparison_results = "Comparison of Duplicate Files:\n"
        total_files = sum(len(paths) for paths in duplicates.values() if len(paths) > 1)
        progress["maximum"] = total_files
        files_compared = 0

        for filename, paths in duplicates.items():
            if len(paths) > 1:
                base_path = paths[0]
                base_size = os.path.getsize(base_path)
                for path in paths[1:]:
                    if cancel_search:
                        messagebox.showinfo("Comparison Cancelled", "La comparaison a été annulée.")
                        return

                    size = os.path.getsize(path)
                    if base_size != size:
                        comparison_results += f"\n{filename} differs by size:\n  {base_path} ({base_size} bytes)\n  {path} ({size} bytes)\n"
                    elif binary_compare_var.get():
                        base_hash = calculate_file_hash(base_path)
                        file_hash = calculate_file_hash(path)
                        if base_hash != file_hash:
                            comparison_results += f"\n{filename} differs by hash:\n  {base_path}\n  {path}\n"
                        else:
                            comparison_results += f"\n{filename} is identical:\n  {base_path}\n  {path}\n"
                    else:
                        comparison_results += f"\n{filename} is identical (size match):\n  {base_path}\n  {path}\n"

                    files_compared += 1
                    progress["value"] = files_compared
                    root.update_idletasks()

        display_result(comparison_results)

    # Calculer le hash d'un fichier
    def calculate_file_hash(filepath):
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    # Renommer les fichiers en utilisant un préfixe basé sur le dossier parent
    def rename_files_with_prefix():
        folder = folder_entry.get()
        if not folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder before renaming files.")
            return

        for dirpath, _, filenames in os.walk(folder):
            if any(len(duplicates[filename]) > 1 for filename in filenames if filename in duplicates):
                # Création de la fenêtre de prévisualisation
                preview_window = tk.Toplevel()
                preview_window.title("Rename Preview")
                preview_frame = tk.Frame(preview_window)
                preview_frame.pack(expand=True, fill='both')

                scrollbar = tk.Scrollbar(preview_frame)
                scrollbar.pack(side='right', fill='y')

                text_box = tk.Text(preview_frame, wrap='word', width=100, height=20, yscrollcommand=scrollbar.set)
                rename_map = []

                folder_name = os.path.basename(dirpath).replace(" ", "_")
                for filename in filenames:
                    if filename in duplicates and len(duplicates[filename]) > 1:
                        new_name = f"{folder_name}_{filename.replace(' ', '_')}"
                        old_path = os.path.join(dirpath, filename)
                        new_path = os.path.join(dirpath, new_name)
                        rename_map.append((old_path, new_path))
                        text_box.insert('end', f"{filename} -> {new_name}\n")

                text_box.config(state='normal')  # Permet de sélectionner du texte
                text_box.pack(expand=True, fill='both')
                scrollbar.config(command=text_box.yview)

                def apply_rename():
                    for old_path, new_path in rename_map:
                        os.rename(old_path, new_path)
                    messagebox.showinfo("Renaming Completed", "Les fichiers ont été renommés avec succès.")
                    preview_window.destroy()

                def skip_folder():
                    preview_window.destroy()

                apply_button = tk.Button(preview_window, text="Apply", command=apply_rename)
                apply_button.pack(side='left', padx=10, pady=10)

                skip_button = tk.Button(preview_window, text="Skip Folder", command=skip_folder)
                skip_button.pack(side='right', padx=10, pady=10)

                preview_window.wait_window()

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

        result_window.wait_window()

    # Vérifier la file de résultats
    def check_result_queue():
        try:
            result = result_queue.get_nowait()
            if result == "cancelled":
                messagebox.showinfo("Search Cancelled", "La recherche a été annulée.")
            else:
                display_result(result)
                if duplicates:
                    compare_button.config(state='normal')
        except queue.Empty:
            root.after(100, check_result_queue)

    # Lancer la recherche
    def start_search():
        folder = folder_entry.get()
        if not folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder before starting the search.")
            return
        show_top_10 = top_10_var.get()
        show_all_files = all_files_var.get()
        search_thread = threading.Thread(target=find_duplicate_files, args=(folder, show_top_10, show_all_files, result_queue))
        search_thread.start()
        check_result_queue()

    # Bouton pour sélectionner le dossier
    select_folder_button = tk.Button(root, text="Select Folder...", command=select_folder)
    select_folder_button.pack(pady=10)

    # Bouton pour lancer la recherche
    start_button = tk.Button(root, text="Search Files", command=start_search, state='disabled')
    start_button.pack(pady=20)

    # Bouton pour annuler la recherche
    cancel_button = tk.Button(root, text="Cancel", command=cancel)
    cancel_button.pack(pady=5)

    # Bouton pour comparer les fichiers dupliqués
    compare_button = tk.Button(root, text="Compare Duplicates", command=compare_duplicates, state='disabled')
    compare_button.pack(pady=5)

    # Bouton pour renommer les fichiers avec un préfixe basé sur le dossier parent
    rename_button = tk.Button(root, text="Rename Files with Folder Prefix", command=rename_files_with_prefix, state='disabled')
    rename_button.pack(pady=5)

    # Checkbox pour les options d'affichage
    top_10_var = tk.BooleanVar()
    top_10_check = tk.Checkbutton(root, text="Show Top 10 Folders with Most Duplicates", variable=top_10_var)
    top_10_check.pack(pady=5)

    all_files_var = tk.BooleanVar()
    all_files_check = tk.Checkbutton(root, text="Show All Duplicate Files", variable=all_files_var)
    all_files_check.pack(pady=5)

    # Checkbox pour la comparaison binaire
    binary_compare_var = tk.BooleanVar()
    binary_compare_check = tk.Checkbutton(root, text="Perform Binary Comparison (Hash)", variable=binary_compare_var)
    binary_compare_check.pack(pady=5)

    # Lancer l'application principale
    root.mainloop()

if __name__ == "__main__":
    main()