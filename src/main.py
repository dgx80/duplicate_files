import os
import tkinter as tk
from tkinter import filedialog, messagebox, StringVar
from tkinter.ttk import Progressbar, Radiobutton
from ttkthemes import ThemedTk
import threading
import queue
from src.duplicate_finder import DuplicateFinder  # Importer la classe DuplicateFinder


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
    global cancel_search, to_delete_folder, duplicate_finder, files_to_move
    cancel_search = False
    
    duplicate_finder = None  # Instance de DuplicateFinder
    files_to_move = []  # Liste des fichiers à déplacer après confirmation

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
        if duplicate_finder:
            duplicate_finder.cancel_search()

    # Nettoyage des doublons en fonction de la comparaison binaire
    def cleanup_duplicates():
        folder = folder_entry.get()
        if not folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder before starting the cleanup.")
            return

        if not duplicate_finder or not duplicate_finder.duplicates:
            messagebox.showwarning("No Duplicates Found", "Please perform a search before attempting to clean up duplicates.")
            return

        # Afficher le message d'avertissement
        messagebox.showinfo("Warning", "No files will be deleted by this program. Files will only be moved to a 'to_delete' folder for review.")

        # Demander quel dossier conserver
        select_folder_to_keep()

    # Sélection du dossier à conserver
    def select_folder_to_keep():
        folder_list = list(duplicate_finder.folders.keys())
        if len(folder_list) < 2:
            messagebox.showwarning("Not Enough Folders", "There are not enough folders with duplicates to proceed.")
            return

        select_window = tk.Toplevel()
        select_window.title("Select Folder to Keep - " + folder_entry.get())
        selected_folder = StringVar()
        selected_folder.set(folder_list[0]) if folder_list else None

        for folder in folder_list:
            Radiobutton(select_window, text=f"Keep {folder}", variable=selected_folder, value=folder).pack(anchor='w')

        def confirm_selection():
            folder_to_keep = selected_folder.get()
            global files_to_move
            files_to_move = duplicate_finder.get_files_to_cleanup(folder_to_keep)
            select_window.destroy()
            preview_cleanup(files_to_move, folder_to_keep)

        confirm_button = tk.Button(select_window, text="Confirm", command=confirm_selection)
        confirm_button.pack(pady=10)

    # Prévisualisation des fichiers à supprimer
    def preview_cleanup(files, folder_to_keep):
        preview_window = tk.Toplevel()
        preview_window.title("Cleanup Preview - " + folder_entry.get())
        text_frame = tk.Frame(preview_window)
        text_frame.pack(expand=True, fill='both')

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')

        text_box = tk.Text(text_frame, wrap='word', width=100, height=30, yscrollcommand=scrollbar.set)
        text_box.insert('end', f"Cleaning folder: {folder_entry.get()}\n")
        text_box.insert('end', f"Keeping folder: {folder_to_keep}\n\n")
        for file in files:
            text_box.insert('end', f"{file} -> to_delete\n")
        text_box.config(state='normal')  # Permet de sélectionner du texte
        text_box.pack(expand=True, fill='both')

        scrollbar.config(command=text_box.yview)

        def apply_cleanup():
            to_delete_folder = os.path.join(folder_entry.get(), "to_delete")
            if not os.path.exists(to_delete_folder):
                os.makedirs(to_delete_folder)

            for path in files_to_move:
                filename = os.path.basename(path)
                new_path = os.path.join(to_delete_folder, filename)
                if not os.path.exists(new_path):
                    os.rename(path, new_path)

            messagebox.showinfo("Cleanup Completed", "The duplicate files have been moved to the 'to_delete' folder.")
            preview_window.destroy()

        apply_button = tk.Button(preview_window, text="Apply", command=apply_cleanup)
        apply_button.pack(side='left', padx=10, pady=10)

        skip_button = tk.Button(preview_window, text="Skip Folder", command=preview_window.destroy)
        skip_button.pack(side='right', padx=10, pady=10)

    # Fonction pour générer le texte du résultat
    def generate_result_text():
        result = f"Total files scanned: {duplicate_finder.progress['maximum']}\n"
        if duplicate_finder.duplicates:
            if all_files_var.get():
                result += "Duplicate files found:\n"
                folder_count = Counter()
                for filename, paths in duplicate_finder.duplicates.items():
                    result += f"\n{filename} found in:\n"
                    result += "\n".join(paths) + "\n"
                    for path in paths:
                        folder_count[os.path.dirname(path)] += 1

                if top_10_var.get():
                    result += "\nTop 10 folders with the most duplicates:\n"
                    for folder, count in folder_count.most_common(10):
                        result += f"{folder}: {count} duplicates\n"
            elif top_10_var.get():
                folder_count = Counter()
                for paths in duplicate_finder.duplicates.values():
                    for path in paths:
                        folder_count[os.path.dirname(path)] += 1
                result += "\nTop 10 folders with the most duplicates:\n"
                for folder, count in folder_count.most_common(10):
                    result += f"{folder}: {count} duplicates\n"
        else:
            result += "No duplicate files were found."

        return result

    # Affichage des résultats
    def display_result():
        result = generate_result_text()
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
            result = duplicate_finder.result_queue.get_nowait()
            if result == "cancelled":
                messagebox.showinfo("Search Cancelled", "La recherche a été annulée.")
            else:
                display_result()
                cleanup_button.config(state='normal')
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
        global duplicate_finder
        duplicate_finder = DuplicateFinder(folder, progress, show_top_10, show_all_files)
        search_thread = threading.Thread(target=duplicate_finder.find_duplicates)
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

    # Bouton pour nettoyer les fichiers dupliqués
    cleanup_button = tk.Button(root, text="Cleanup Duplicates", command=cleanup_duplicates, state='disabled')
    cleanup_button.pack(pady=5)

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