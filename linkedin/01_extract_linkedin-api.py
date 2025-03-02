# https://github.com/tomquirk/linkedin-api
# https://linkedin-api.readthedocs.io/
# "sub": "nz-CeibFvN"

import json
import os
from linkedin_api import Linkedin
import shutil

# Function to load existing data from a JSON file
def load_existing_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print(f"Warning: {file_path} contains invalid JSON. Starting with an empty dataset.")
                return []
    return []

# Function to create a backup of the existing file
def backup_file(file_path):
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        shutil.copy(file_path, backup_path)
        print(f"Backup created: {backup_path}")

# Function to deduplicate posts based on unique keys (e.g., 'id')
def deduplicate_posts(existing_posts, new_posts):
    existing_ids = {post.get("id") for post in existing_posts if "id" in post}
    unique_new_posts = [post for post in new_posts if post.get("id") not in existing_ids]
    return existing_posts + unique_new_posts

# Main script
def main():
    # Load credentials from credentials.json
    with open("credentials.json", "r") as f:
        credentials = json.load(f)

    if not credentials:
        print("Error: No credentials found in credentials.json")
        return

    # Initialize the LinkedIn API client
    linkedin = Linkedin(credentials["username"], credentials["password"], refresh_cookies=True)

    # Retrieve up to 50 posts from the profile
    profile_posts = linkedin.get_profile_posts("ACoAAAOG-DsBYRJPbgKIzHGv-CAEZR0xmGLIq_I", post_count=200)
    print(f"Number of posts retrieved: {len(profile_posts)}")

    # Load existing posts from posts.json
    posts_file_path = "posts.json"
    existing_posts = load_existing_data(posts_file_path)

    # Deduplicate posts and merge
    all_posts = deduplicate_posts(existing_posts, profile_posts)

    # Backup the current posts file
    backup_file(posts_file_path)

    # Save the updated posts to posts.json with indentation
    with open(posts_file_path, "w") as posts_file:
        json.dump(all_posts, posts_file, ensure_ascii=False, indent=4)

    print(f"Posts have been updated and saved to {posts_file_path}. Total posts: {len(all_posts)}")

# Run the script
if __name__ == "__main__":
    main()
