"""
Handles input for GUI interactions.
"""

from gpiozero import Button

GPIO_OK_BUTTON = 26
GPIO_NEXT_BUTTON = 16


class KeyboardInputHandler:
    def __init__(self, manager):
        self.manager = manager

    def run(self):
        print("Keyboard input handler active: 'o' = OK, 'n' = NEXT, 'q' = quit")

        while True:
            try:
                user_input = input("> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if user_input == "o":
                self.manager.handle_ok()
            elif user_input == "n":
                self.manager.handle_next()
            elif user_input == "q":
                break
            elif user_input:
                print("Unknown input. Use 'o', 'n', or 'q'.")


class ButtonInputHandler:
    def __init__(self, manager):
        self.manager = manager
        
        self.btn_next = Button(GPIO_NEXT_BUTTON, bounce_time=0.1)
        self.btn_ok = Button(GPIO_OK_BUTTON, bounce_time=0.1)
        
        self.btn_next.when_pressed = self._next_clicked
        self.btn_ok.when_pressed = self._ok_clicked

    def _next_clicked(self):
        self.manager.handle_next()

    def _ok_clicked(self):
        self.manager.handle_ok()
