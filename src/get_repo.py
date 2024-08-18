import os
import shutil
from git import Repo
from datetime import datetime


def clone_fpl_repo():
    # Define the repository URL
    repo_url = "https://github.com/vaastav/Fantasy-Premier-League.git"

    # Generate the folder name with the current date inside the project root
    current_date = datetime.now().strftime("%Y-%m-%d")
    project_root = os.path.dirname(os.path.dirname(__file__))  # Navigate to the project root
    base_directory = os.path.join(project_root, "fpl-data")
    folder_name = os.path.join(base_directory, current_date)
    clone_directory = folder_name

    # Check if today's data already exists
    if os.path.exists(clone_directory):
        print(f"Today's data already exists at {clone_directory}. No need to download again.")
        return clone_directory
    else:
        # Delete existing data in `/fpl-data/` if any
        if os.path.exists(base_directory):
            shutil.rmtree(base_directory)
            print(f"Deleted existing data in {base_directory}.")

        # Create the directory structure and clone the repository
        os.makedirs(clone_directory)
        Repo.clone_from(repo_url, clone_directory)
        print(f"Repository cloned to {clone_directory}")

    return clone_directory


# Example usage:
if __name__ == "__main__":
    repo_path = clone_fpl_repo()
