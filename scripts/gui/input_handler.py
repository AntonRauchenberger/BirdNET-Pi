"""
Handles input for GUI interactions.
"""


class InputHandler:
    def __init__(self, manager):
        self.manager = manager

    def run(self):
        print("Input handler active: 'o' = OK, 'n' = NEXT, 'q' = quit")

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
