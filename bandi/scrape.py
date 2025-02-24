import subprocess
from datetime import datetime, timedelta
import time

# Define the scripts to run in the ./scraper/ directory
scripts = [
    "./scraper/arter.py",
    "./scraper/euportal.py",
    "./scraper/eucall-rss.py",
    "./scraper/inpa.py",
    "./scraper/onepass.py",
    "./scraper/comparison.py"
]

# Run each script
total_scripts = len(scripts)
elapsed_times = []

for index, script in enumerate(scripts):
    print(f"\nRunning {script} ({index + 1}/{total_scripts})...")
    start_time = time.time()
    process = subprocess.Popen(["python3", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Print output line by line
    for line in iter(process.stdout.readline, ''):
        print(line, end='')  # Print each line as it comes

    process.stdout.close()
    process.wait()

    if process.returncode == 0:
        print(f"{script} completed successfully.")
    else:
        error_output = process.stderr.read()
        print(f"Error running {script}:\n{error_output}")
        exit(1)  # Exit if a script fails

    # Record the elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_times.append(elapsed_time)

    # Calculate and display estimated remaining time
    avg_time = sum(elapsed_times) / len(elapsed_times)
    remaining_scripts = total_scripts - (index + 1)
    estimated_remaining_time = timedelta(seconds=int(avg_time * remaining_scripts))
    print(f"Estimated time remaining for all scripts: {estimated_remaining_time}")

# Commit and push the updates to Git
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
commit_message = f"dati aggiornati al {now}"

try:
    print("\nCommitting changes to Git...")
    subprocess.run(["git", "commit", "-am", commit_message], check=True)
    print("Pushing changes to remote repository...")
    subprocess.run(["git", "push"], check=True)
    print("Git push completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Git operation failed: {e}")
