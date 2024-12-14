import queue
import os
import hashlib
from collections import defaultdict, Counter
from typing import Dict, List

class DuplicateFinder:
    def __init__(self, root_folder, progress, show_top_10=False, show_all_files=False):
        self.root_folder = root_folder
        self.progress = progress
        self.show_top_10 = show_top_10
        self.show_all_files = show_all_files
        self.cancel_search_flag = False
        self.duplicates = {}
        self.folders: Dict[str, List[str]] = {}
        self.result_queue = queue.Queue()

    def cancel_search(self):
        self.cancel_search_flag = True

    def find_duplicates(self):
        self.result_queue = queue.Queue()
        file_dict = defaultdict(list)
        total_files = 0
        files_processed = 0

        # Parcours de l'arborescence pour compter le nombre total de fichiers
        for dirpath, _, filenames in os.walk(self.root_folder):
            if self.cancel_search_flag:
                return "cancelled"
            total_files += len(filenames)

        self.progress["maximum"] = total_files

        # Parcours de l'arborescence pour stocker les chemins des fichiers
        for dirpath, _, filenames in os.walk(self.root_folder):
            if self.cancel_search_flag:
                self.result_queue.put("cancelled")
                return "cancelled"

            for filename in filenames:
                if self.cancel_search_flag:
                    self.result_queue.put("cancelled")
                    return "cancelled"

                file_dict[filename].append(os.path.join(dirpath, filename))
                files_processed += 1

                if files_processed % 100 == 0:  # Mise à jour de la progression tous les 100 fichiers
                    self.progress["value"] = files_processed

        # Mise à jour finale de la barre de progression
        self.progress["value"] = total_files

        # Filtrer les fichiers dupliqués
        self.duplicates = {k: v for k, v in file_dict.items() if len(v) > 1}
        
        # Préparer les dossiers contenant des duplicatas
        if self.duplicates:
            self.result_queue.put("There are duplicate")
            for duplicated_file, folders in self.duplicates.items():
                for fullpath in folders:
                    folder = os.path.dirname(fullpath)
                    if folder not in self.folders:
                        self.folders[folder] = []
                    self.folders[folder].append(duplicated_file)
        else:
            self.result_queue.put("There are no duplicate")

    def calculate_file_hash(self, filepath):
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def cleanup_duplicates(self, folder):
        to_delete_folder = os.path.join(self.root_folder, "to_delete")
        if not os.path.exists(to_delete_folder):
            os.makedirs(to_delete_folder)

        folder_count = Counter()
        for paths in self.duplicates.values():
            for path in paths:
                folder_count[os.path.dirname(path)] += 1

        sorted_folders = folder_count.most_common()

        if len(sorted_folders) < 2:
            return

        folder1, folder2 = sorted_folders[0][0], sorted_folders[1][0]
        folder_to_clean = folder1 if folder1 != folder else folder2

        files_to_move = []
        for filename, paths in self.duplicates.items():
            paths_in_clean_folder = [path for path in paths if path.startswith(folder_to_clean)]
            paths_in_kept_folder = [path for path in paths if path.startswith(folder)]
            if len(paths_in_kept_folder) > 0:
                reference_path = paths_in_kept_folder[0]
                reference_hash = self.calculate_file_hash(reference_path)
                for path in paths_in_clean_folder:
                    file_hash = self.calculate_file_hash(path)
                    if file_hash == reference_hash:
                        files_to_move.append(path)

        for path in files_to_move:
            filename = os.path.basename(path)
            new_path = os.path.join(to_delete_folder, filename)
            os.rename(path, new_path)