class RenameFilesTool:
    @staticmethod
    def rename_files_with_prefix(self, folder):
        for dirpath, _, filenames in os.walk(folder):
            if filenames:
                folder_name = os.path.basename(dirpath).replace(" ", "_")
                for filename in filenames:
                    new_name = f"{folder_name}_{filename.replace(' ', '_')}"
                    old_path = os.path.join(dirpath, filename)
                    new_path = os.path.join(dirpath, new_name)
                    os.rename(old_path, new_path)
        