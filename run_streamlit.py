import subprocess
import time

# Replace 'main_stream.py' with your Streamlit script filename
script_path = 'C:/noam/dogs/pythonProject/main_stream.py'

# Update the path to Google Chrome without invalid escape sequences
chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

# Start the Streamlit server
server = subprocess.Popen(['streamlit', 'run', script_path])

# Wait for the server to start
time.sleep(5)

# Open Chrome with the Streamlit app
try:
    subprocess.Popen([chrome_path, 'http://localhost:8501'])
except FileNotFoundError:
    print("Chrome not found at ", chrome_path)

# Keep the script running to handle Streamlit server termination
try:
    server.wait()
except KeyboardInterrupt:
    server.terminate()

