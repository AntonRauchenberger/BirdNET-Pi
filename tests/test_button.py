import argparse

from gpiozero import Button
from signal import pause

TEST_PIN = 23

try:
    parser = argparse.ArgumentParser(description="BirdNET-Pi GUI test renderer")
    parser.add_argument("--pin", type=int, default=TEST_PIN, help="GPIO pin number for the button (default: 23)")
    args = parser.parse_args()
    TEST_PIN = args.pin

    print(f"--- Button Test on GPIO {TEST_PIN} started ---")
    print(f"Connect button wire 1 to GND")
    print(f"Connect button wire 2 to GPIO {TEST_PIN}")
    
    # pull_up=True is default: Button connects pin to GND when pressed
    btn = Button(TEST_PIN, pull_up=True)

    def pressed():
        print("Button pressed!")

    def released():
        print("Button released!")

    btn.when_pressed = pressed
    btn.when_released = released

    print("Waiting for button events... (press Ctrl+C to exit)")
    pause()

except Exception as e:
    print(f"Error: {e}")