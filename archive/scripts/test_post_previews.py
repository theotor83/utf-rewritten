import requests
import json
import os

file_path = os.path.join(os.path.dirname(__file__), 'posts_data.json')
error_log_path = os.path.join(os.path.dirname(__file__), '500_error_posts.txt')

# The URL for the post preview view
URL = "http://127.0.0.1:8000/archive/post-preview"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        posts_data = json.load(f)
except FileNotFoundError:
    print(f"Error: {file_path} not found.")
    exit()
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {file_path}.")
    exit()

error_posts_ids = []

counter = 0

for post in posts_data:
    counter += 1
    if counter % 1000 == 0 or counter == 1:
        print(f"Processing post {counter}/{len(posts_data)}")
    
    post_id = post.get('id')
    post_text = post.get('text')

    if post_text is None:
        print(f"Post with ID {post_id} has no 'text' field. Skipping.")
        continue

    payload = {'content': post_text}

    try:
        response = requests.post(URL, data=payload, timeout=10)

        if response.status_code == 500:
            print(f"Post ID {post_id} resulted in a 500 error.")
            error_posts_ids.append(str(post_id))
        elif response.status_code != 200:
            print(f"Post ID {post_id} resulted in a {response.status_code} error.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred for post ID {post_id}: {e}")
        continue

if error_posts_ids:
    with open(error_log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(error_posts_ids))
    print(f"\nLogged {len(error_posts_ids)} post IDs with 500 errors to {error_log_path}")
else:
    print("\nNo posts resulted in a 500 error.") 