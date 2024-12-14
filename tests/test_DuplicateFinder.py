import os
import shutil
import pytest
from queue import Queue
from src.duplicate_finder import DuplicateFinder


@pytest.fixture
def setup_test_directory():
    # Copy template directory to the test directory
    template_dir = "tests/fixtures/templates/folders"
    test_dir = "tests/fixtures/tmp/folders"

    # Remove the test directory if it exists
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    if not os.path.exists(template_dir):
        raise error()

    # Copy the template directory to create a fresh test directory
    shutil.copytree(template_dir, test_dir)

    yield test_dir

    # Remove the temporary directory after tests
    shutil.rmtree(test_dir)


@pytest.fixture
def duplicate_finder(setup_test_directory):
    # result_queue = Queue()
    progress = {"maximum": 0, "value": 0}
    return DuplicateFinder(setup_test_directory, progress)


def test_find_duplicates(duplicate_finder):
    # Run the duplicate finding method
    duplicate_finder.find_duplicates()

    # Check that duplicates are found
    duplicates = duplicate_finder.duplicates
    assert "file1.txt" in duplicates
    assert len(duplicates["file1.txt"]) == 3

def test_cleanup_duplicates(duplicate_finder):
    # Run the duplicate finding method
    duplicate_finder.find_duplicates()

    # Clean up duplicates, keeping folder1
    folder_to_keep = os.path.join(duplicate_finder.root_folder, "folder1")
    files_to_delete = duplicate_finder.cleanup_duplicates(folder_to_keep=folder_to_keep)

    # Check that the correct file is marked for deletion
    expected_path = os.path.join(duplicate_finder.root_folder, "folder2", "file1.txt")
    assert expected_path in files_to_delete


# def test_rename_files_with_prefix(duplicate_finder, setup_test_directory):
#     # Run the rename method
#     duplicate_finder.rename_files_with_prefix(setup_test_directory)

#     # Check that files have been renamed with the folder prefix
#     renamed_file_path = os.path.join(setup_test_directory, "folder1", "folder1_unique_file.txt")
#     assert os.path.exists(renamed_file_path)
