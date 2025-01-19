import requests
from pynput import keyboard

# Shelly One URL
SHELLY_URL = "http://192.168.1.213/relay/0?turn="

def send_request(action):
    try:
        response = requests.get(SHELLY_URL + action)
        print(f"Response: {response.status_code}, {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

def on_press(key):
    try:
        if key.char == 'o':  # Open the garage door
            print("Opening the garage door...")
            send_request("on")
        elif key.char == 'c':  # Close the garage door
            print("Closing the garage door...")
            send_request("off")
        elif key.char == 'q':  # Quit the program
            print("Exiting the program.")
            return False
    except AttributeError:
        pass  # Handle special keys like Ctrl, Alt, etc.

def main():
    print("Press 'o' to open the garage door, 'c' to close it, and 'q' to quit.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
