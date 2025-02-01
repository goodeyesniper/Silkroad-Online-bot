import threading
import time
import tkinter as tk
from tkinter import messagebox

import cv2
import keyboard
import numpy as np
import pyautogui
from pynput.keyboard import Controller

# Parameters
IMAGES = [
    "image1.png", "image1_bold.png", "image1_bold_underlined.png",
    "image2.png", "image2_bold.png", "image2_bold_underlined.png",
    "image3.png", "image3_bold.png", "image3_bold_underlined.png"
] # Paths to images

SEARCH_INTERVAL = 0.1  # Default time (in seconds) between search attempts
RIGHT_CLICK_INTERVAL = 10  # Default time (in seconds) between right-click actions

# Dragging coordinates
START_COORDS = (580, 350)
END_COORDS = (1220, 350)

# Global Variables
bot_running = False  # Bot start/pause state
last_screen_rotate_time = time.time()
search_area = None  # Area to search for images (left, top, width, height)
key_range = (1, 6)  # Default range of keys to spam (1 to 6)
keyboard_controller = Controller()

## NEW GLOBAL VARIABLES
message_received = False
image_path_GM = "message.png"  # Path to the image you want to scan for
image_path_scroll = "return_scroll.png"
image_repair_hammer = "repair_hammer.png"

just_stop_it = False


def stop_attack():
    global just_stop_it
    just_stop_it = True

## NEW ADDITION ##########################################################

def locate_repair_hammer(image_repair_hammer):
    try:
        return pyautogui.locateOnScreen(image_repair_hammer, confidence=0.8)
    except pyautogui.ImageNotFoundException as e:
        print(f"Image not found: {e}")
        return None

def repair_items():
    while True:
        if bot_running and repair_items_var.get():
            locate_hammer = locate_repair_hammer(image_repair_hammer)
            if locate_hammer:
                try:
                    pyautogui.click(locate_hammer, button='right')
                    time.sleep(0.1)
                    keyboard.press_and_release("enter")
                    time.sleep(7200)

                except ValueError as e:
                    print(f"An error occurred: {e}")
        
        time.sleep(0.1)  # Prevent busy waiting when bot_running is False


def locate_image_message(image_path_GM):
    try:
        return pyautogui.locateOnScreen(image_path_GM, confidence=0.8)
    except pyautogui.ImageNotFoundException as e:
        print(f"Searching for messages..: {e}")
        return None

def locate_image_scroll(image_path_scroll):
    try:
        return pyautogui.locateOnScreen(image_path_scroll, confidence=0.8)
    except pyautogui.ImageNotFoundException as e:
        print(f"Image not found: {e}")
        return None

def find_and_act():
    global message_received, bot_running
    while True:
        if bot_running and monitor_GM_message_var.get() and not message_received:
            location = locate_image_message(image_path_GM)
            time.sleep(5)
            if location:
                try:
                    # Press F7
                    stop_attack()
                    time.sleep(5)

                    # Move mouse to the image location and click
                    pyautogui.click(location)

                    # Type the message
                    pyautogui.typewrite("hello brb")
                    time.sleep(0.5)
                    keyboard.press_and_release("enter")
                    time.sleep(0.5)

                    # Calculate center of the screen
                    screen_width, screen_height = pyautogui.size()
                    center_x, center_y = screen_width // 2, screen_height // 2
                    
                    # Left click the center of the screen
                    pyautogui.click(center_x, center_y)
                    time.sleep(2)

                    locate_scroll = locate_image_scroll(image_path_scroll)
                    if locate_scroll:
                        pyautogui.click(locate_scroll, button='right')

                    # Set message_received flag to True and stop the bot
                    message_received = True
                    toggle_bot()

                except ValueError as e:
                    print(f"An error occurred: {e}")
            
        time.sleep(0.1)  # Prevent busy waiting when bot_running is False

## NEW ADDITION ##########################################################


def select_search_area():
    """Interactive area selection overlay."""
    overlay = tk.Tk()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-alpha", 0.3)
    overlay.configure(bg="black")
    canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    rect_id = None

    def on_mouse_press(event):
        """Capture the starting point."""
        nonlocal rect_id
        select_search_area.start_x, select_search_area.start_y = event.x, event.y
        rect_id = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def on_mouse_drag(event):
        """Update the rectangle as the mouse is dragged."""
        canvas.coords(rect_id, select_search_area.start_x, select_search_area.start_y, event.x, event.y)

    def on_mouse_release(event):
        """Capture the ending point and close the overlay."""
        select_search_area.end_x, select_search_area.end_y = event.x, event.y
        overlay.destroy()
        print(f"Selected area: ({select_search_area.start_x}, {select_search_area.start_y}) to ({select_search_area.end_x}, {select_search_area.end_y})")
        global search_area
        search_area = (
            select_search_area.start_x,
            select_search_area.start_y,
            select_search_area.end_x - select_search_area.start_x,
            select_search_area.end_y - select_search_area.start_y,
        )
        print(f"Search area set to: {search_area}")

    # Bind events
    canvas.bind("<ButtonPress-1>", on_mouse_press)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_release)

    overlay.mainloop()

def locate_image_on_screen(image_paths, confidence=0.8):
    """Locate any image from the list within the defined search area."""
    if search_area is None:
        print("No search area defined. Searching the entire screen.")
        screen = pyautogui.screenshot()
    else:
        print(f"Searching within area: {search_area}")
        screen = pyautogui.screenshot(region=search_area)

    screen_array = np.array(screen)
    screen_gray = cv2.cvtColor(screen_array, cv2.COLOR_BGR2GRAY)  # Convert to grayscale

    for image_path in image_paths:
        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"Error: Unable to read image {image_path}. Check the file path.")
            continue

        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            # Calculate the center of the matched image
            center_x = max_loc[0] + template.shape[1] // 2
            center_y = max_loc[1] + template.shape[0] // 2 + 20

            if search_area is not None:
                # Adjust for the offset of the search area
                center_x += search_area[0]
                center_y += search_area[1]

            return (center_x, center_y)

    return None

def spam_keys():
    start, end = key_range
    for key in range(start, end + 1):
        keyboard.press(str(key))
        keyboard.release(str(key))
        time.sleep(0.02)
    keyboard.press('x')
    keyboard.release('x')
    time.sleep(0.02)

def listen_for_hotkeys():
    """Listen for hotkeys to control the bot."""
    print("Listening for hotkeys...")
    keyboard.add_hotkey("F7", toggle_bot)  # Toggle bot
    keyboard.wait("esc")  # Stop the program with 'esc' key

def perform_screen_rotate():
    """Perform the right-click drag action."""
    global point1, point2  # Ensure access to global coordinates
    if screen_rotate_checkbox_var.get():  # Use the checkbox variable to check the toggle state
        pyautogui.moveTo(*START_COORDS)
        pyautogui.mouseDown(button="right")
        pyautogui.moveTo(*END_COORDS, duration=0.4)  # Faster drag
        pyautogui.mouseUp(button="right")

def perform_move_forward():
    while True:
        if bot_running and move_forward_checkbox_var.get() and not just_stop_it:
            for _ in range(3):  # Repeat the loop 3 times

                screen_width, screen_height = pyautogui.size()
                center_x, center_y = screen_width // 2, screen_height // 2
                    
                # Left click the center of the screen
                pyautogui.click(center_x, (center_y / 2))
                time.sleep(4)

        time.sleep(0.1)  # Prevent busy waiting when bot_running is False

def bot_loop():
    """Main bot loop."""
    global bot_running, last_screen_rotate_time, SEARCH_INTERVAL, RIGHT_CLICK_INTERVAL, just_stop_it

    while True:
        if bot_running and not just_stop_it:
            location = locate_image_on_screen(IMAGES)
            if location:
                print(f"Image found at {location}. Clicking and spamming keys...")
                pyautogui.click(location)  # Click the adjusted location
                spam_keys()

            if time.time() - last_screen_rotate_time >= RIGHT_CLICK_INTERVAL:
                print("Performing right-click drag action...")
                perform_screen_rotate()
                last_screen_rotate_time = time.time()

        time.sleep(SEARCH_INTERVAL)

def update_search_interval(value):
    """Update the image search interval."""
    global SEARCH_INTERVAL
    SEARCH_INTERVAL = float(value)
    print(f"Search interval updated to {SEARCH_INTERVAL} seconds.")

def update_right_click_interval(value):
    """Update the right-click interval."""
    global RIGHT_CLICK_INTERVAL
    RIGHT_CLICK_INTERVAL = float(value)
    print(f"Right-click interval updated to {RIGHT_CLICK_INTERVAL} seconds.")

def update_key_range():
    """Update the key range based on user input in the GUI."""
    try:
        start = int(start_key_var.get())
        end = int(end_key_var.get())
        if start < 1 or start > 10 or end < 1 or end > 10 or start > end:
            raise ValueError
        global key_range
        key_range = (start, end)
        print(f"Key range updated to: {key_range}")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numbers between 1 and 10 for the key range.")


def buffer():
    """Clicks F3, spams keys 1 to 7 for 8 seconds, stops, and then clicks F1."""
    while True:
        if bot_running and buffer_checkbox_var.get() and not just_stop_it:  # Check if bot is running and buffer is enabled
            # Press F3 once
            keyboard.press_and_release("F3")

            # Get the delay for F3 from the GUI
            try:
                f3_delay = float(f3_delay_var.get())
                if f3_delay < 0:
                    raise ValueError("Negative delay")
            except ValueError:
                f3_delay = 8  # Default to 8 seconds if invalid input
            
            start_time = time.time()
            while time.time() - start_time < f3_delay:  # Spam for 8 seconds
                start, end = key_range
                for key in range(start, end + 1):
                    keyboard.press_and_release(str(key))  # Press the key
                    time.sleep(0.02)  # Slight delay to avoid overwhelming

            # Press F1 once
            keyboard.press_and_release("F1")
            print("Pressed F1")

            time.sleep(30 * 60)  # Wait for 30 minutes before the next cycle
        else:
            time.sleep(0.1)  # Prevent busy waiting

# Keyboard Hook
def listen_for_hotkeys():
    """Listen for the F7 key to toggle the bot."""
    keyboard.add_hotkey("F7", toggle_bot)

    # Keep the thread alive
    keyboard.wait()

### TOGGLES ##################################

def toggle_bot():
    """Start or pause the bot."""
    global bot_running, status_label, message_received, just_stop_it
    message_received = False
    just_stop_it = False
    bot_running = not bot_running
    status_label.config(text=f"Bot Status: {'Running' if bot_running else 'Paused'}")
    print(f"Bot {'started' if bot_running else 'paused'}.")

def toggle_buffer():
    """Toggle the buffer action based on the checkbox state."""
    print(f"Buffer action {'enabled' if buffer_checkbox_var.get() else 'disabled'}.")

def toggle_move_forward():
    """Toggle the perform move forward action based on the checkbox state."""
    print(f"Move forward action {'enabled' if move_forward_checkbox_var.get() else 'disabled'}.")

def toggle_right_click():
    """Enable or disable the right-click drag action based on the checkbox."""
    global enable_right_click
    enable_right_click = screen_rotate_checkbox_var.get()
    print(f"Right-click drag action {'enabled' if enable_right_click else 'disabled'}.")


def toggle_monitor_GM_message():
    print(f"Monitor GM message {'enabled' if monitor_GM_message_var.get() else 'disabled'}.")

def toggle_repair_items():
    print(f"Repair items {'enabled' if repair_items_var.get() else 'disabled'}.")

### TOGGLES ##################################

def start_gui():
    """Launch the GUI."""
    global status_label

    root = tk.Tk()
    root.title("LazyAss")

    global screen_rotate_checkbox_var, buffer_checkbox_var, move_forward_checkbox_var, start_key_var, end_key_var, f3_delay_var, monitor_GM_message_var, repair_items_var

    # Initialize variables
    screen_rotate_checkbox_var = tk.BooleanVar(value=True)
    buffer_checkbox_var = tk.BooleanVar(value=False)
    move_forward_checkbox_var = tk.BooleanVar(value=False)
    monitor_GM_message_var = tk.BooleanVar(value=True)
    repair_items_var = tk.BooleanVar(value=True)
    start_key_var = tk.StringVar(value="1")
    end_key_var = tk.StringVar(value="6")
    f3_delay_var = tk.StringVar(value="8")

    # Layout
    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10)

    # Row 1, Column 1: Select Search Area Button
    set_area_button = tk.Button(main_frame, text="Set Search Area", command=select_search_area, font=("Arial", 10))
    set_area_button.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # Row 2-5, Column 1: Movement Panel
    checkbox_frame = tk.LabelFrame(main_frame, text="Movement Settings", font=("Arial", 10, "bold"), padx=10, pady=10)
    checkbox_frame.grid(row=2, column=1, rowspan=4, padx=5, pady=5, sticky="w")

    buffer_checkbox = tk.Checkbutton(checkbox_frame, text="Enable Buffs (Skills on F3)", variable=buffer_checkbox_var, command=toggle_buffer, font=("Arial", 10))
    buffer_checkbox.pack(anchor="w")

    screen_rotate = tk.Checkbutton(checkbox_frame, text="Enable Screen Rotate", variable=screen_rotate_checkbox_var, command=toggle_right_click, font=("Arial", 10))
    screen_rotate.pack(anchor="w")

    move_forward_checkbox = tk.Checkbutton(checkbox_frame, text="Perform Move Forward", variable=move_forward_checkbox_var, command=toggle_move_forward, font=("Arial", 10))
    move_forward_checkbox.pack(anchor="w")

    # Row 6-7, Column 1: Set Key Range Panel
    key_range_frame = tk.LabelFrame(main_frame, text="Set Key Range", font=("Arial", 10, "bold"), padx=10, pady=10)
    key_range_frame.grid(row=6, column=1, padx=5, pady=5, sticky="w")

    tk.Label(key_range_frame, text="Start:", font=("Arial", 10)).grid(row=0, column=0, padx=5)
    start_entry = tk.Entry(key_range_frame, textvariable=start_key_var, width=5, justify="center", font=("Arial", 10))
    start_entry.grid(row=0, column=1, padx=5)

    tk.Label(key_range_frame, text="End:", font=("Arial", 10)).grid(row=0, column=2, padx=5)
    end_entry = tk.Entry(key_range_frame, textvariable=end_key_var, width=5, justify="center", font=("Arial", 10))
    end_entry.grid(row=0, column=3, padx=5)

    set_key_range_button = tk.Button(key_range_frame, text="Set", command=update_key_range, font=("Arial", 10))
    set_key_range_button.grid(row=0, column=4, padx=10)

    # Row 7, Column 1: Monitor GM message
    monitor_GM_frame = tk.LabelFrame(main_frame, text="Stop bot on GM msg", font=("Arial", 10, "bold"), padx=10, pady=10)
    monitor_GM_frame.grid(row=7, column=1, rowspan=2, padx=5, pady=5, sticky="w")

    monitor_GM_message = tk.Checkbutton(monitor_GM_frame, text="On/Off", variable=monitor_GM_message_var, command=toggle_monitor_GM_message, font=("Arial", 10))
    monitor_GM_message.pack(anchor="w")

    # Row 1-2, Column 2: Speed Settings Panel
    tk.Label(main_frame, text="Speed Settings", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=5, pady=5, sticky="w")
    f3_delay_frame = tk.Frame(main_frame)
    f3_delay_frame.grid(row=2, column=2, padx=5, pady=5, sticky="w")
    f3_delay_entry = tk.Entry(f3_delay_frame, textvariable=f3_delay_var, width=5, justify="center", font=("Arial", 10))
    f3_delay_entry.grid(row=0, column=0, padx=5)
    tk.Label(f3_delay_frame, text="Buffs Delay", font=("Arial", 10)).grid(row=0, column=1, padx=5)

    # Row 3-4, Column 2: Search Speed Panel
    search_speed_frame = tk.LabelFrame(main_frame, text="Search Speed", font=("Arial", 10, "bold"), padx=10, pady=10)
    search_speed_frame.grid(row=3, column=2, rowspan=2, padx=5, pady=5, sticky="w")

    search_speed_slider = tk.Scale(search_speed_frame, from_=0.1, to=5.0, resolution=0.1, orient="horizontal", command=update_search_interval)
    search_speed_slider.set(SEARCH_INTERVAL)
    search_speed_slider.pack(anchor="w")

    # Row 5-6, Column 2: Screen Rotate Panel
    screen_rotate_frame = tk.LabelFrame(main_frame, text="Screen Rotate", font=("Arial", 10, "bold"), padx=10, pady=10)
    screen_rotate_frame.grid(row=5, column=2, rowspan=2, padx=5, pady=5, sticky="w")

    right_click_slider = tk.Scale(screen_rotate_frame, from_=5.0, to=30.0, resolution=1, orient="horizontal", command=update_right_click_interval)
    right_click_slider.set(RIGHT_CLICK_INTERVAL)
    right_click_slider.pack(anchor="w")

    # Row 8, Column 1: Repair Items
    repair_items_frame = tk.LabelFrame(main_frame, text="Auto Repair", font=("Arial", 10, "bold"), padx=10, pady=10)
    repair_items_frame.grid(row=7, column=2, rowspan=2, padx=5, pady=5, sticky="w")

    repair_items_message = tk.Checkbutton(repair_items_frame, text="On/Off", variable=repair_items_var, command=toggle_repair_items, font=("Arial", 10))
    repair_items_message.pack(anchor="w")

    # Row 7, Column 2: Start/Pause and Quit Buttons
    button_frame = tk.Frame(main_frame)
    button_frame.grid(row=9, column=1, columnspan=2, pady=5, padx=5, sticky="nsew")  # Span across two columns

    # Configure the columns of the button frame to equally distribute space
    button_frame.grid_columnconfigure(0, weight=1)  # Center Start/Pause button in the first column
    button_frame.grid_columnconfigure(1, weight=1)  # Center Quit button in the second column

    # Start/Pause Button
    start_pause_button = tk.Button(button_frame, text="Start/Pause", command=toggle_bot, font=("Arial", 10))
    start_pause_button.grid(row=0, column=0, padx=5)

    # Quit Button
    quit_button = tk.Button(button_frame, text="Quit", command=root.destroy, font=("Arial", 10))
    quit_button.grid(row=0, column=1, padx=5)


    # Status Label
    status_label = tk.Label(root, text="Bot Status: Paused", font=("Arial", 10), fg="red")
    status_label.pack(pady=5)

    # Show instructions
    messagebox.showinfo(
        "HOW TO USE",
        "Press F7 to start/pause the bot.\n"
        "Use 'Set Search Area' to highlight the search region.\n"
        "Attacking skills on F1. Buff skills on F3. \n"
        "BERSERK is assigned on X key.\n"
        "Set the key range to define which keys to spam.\n",
    )

    root.mainloop()


# Start the threads
if __name__ == "__main__":
    # Monitor GM message
    threading.Thread(target=find_and_act, daemon=True).start()

    # Repair items
    threading.Thread(target=repair_items, daemon=True).start()

    # Run the bot loop in a separate thread
    threading.Thread(target=bot_loop, daemon=True).start()

    # Run the buffer action in a separate thread
    threading.Thread(target=buffer, daemon=True).start()

    # Perform move forward
    threading.Thread(target=perform_move_forward, daemon=True).start()

    # Start listening for hotkeys in a separate thread
    threading.Thread(target=listen_for_hotkeys, daemon=True).start()

    # Start the GUI
    start_gui()