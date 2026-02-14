import tkinter as tk
from PIL import Image, ImageTk
import cache_image
import threading
from database.models import search_cards

class CardsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.current_cards = []

        tk.Label(self, text="Card List", font=("Arial", 14)).pack(pady=10)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_cards)

        tk.Entry(self, textvariable=self.search_var, width=40).pack(pady=5)

        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True)

        left_frame = tk.Frame(main_container)
        left_frame.pack(side="left", padx=10, fill="both", expand=True)

        self.searchable_list = tk.Listbox(left_frame, width=60, height=20)
        self.searchable_list.pack(fill="both", expand = True, pady=10)
        self.searchable_list.bind("<<ListboxSelect>>", self.show_card_image)

        #Creating fixed frame for image, preventing frame resizing when it first shows up
        right_frame = tk.Frame(main_container, width=220)
        right_frame.pack(side="right", padx=10, fill="y")
        right_frame.pack_propagate(False)

        self.image_label = tk.Label(right_frame, text="Select a card")
        self.image_label.pack(expand=True)

        tk.Button(self, text="Return", command=lambda: controller.show_frame("HomeFrame")).pack(pady=10)

        self.load_cards()

    def load_cards(self):
        self.current_cards = search_cards()
        self.searchable_list.delete(0, tk.END)

        for card in self.current_cards:
            self.searchable_list.insert(tk.END, card[1])

    def filter_cards(self, *args):
        name = self.search_var.get()
        self.current_cards = search_cards(name = name)
        self.searchable_list.delete(0, tk.END)

        for card in self.current_cards:
            self.searchable_list.insert(tk.END, card[1])

    def show_card_image(self, event):
        selection = self.searchable_list.curselection()
        if not selection:
            return

        card = self.current_cards[selection[0]]
        card_id = card[0]

        threading.Thread(
            target=self.load_image_async,
            args=(card_id,),
            daemon=True #Background Processing
        ).start()

    #With threading implemented, the application won't momentarily freeze
    #after clicking an image that was not previously fetched.

    def load_image_async(self, card_id):
        img_path = cache_image.get_card_image(card_id)

        if not img_path:
            return

        img = Image.open(img_path).resize((200, 300))
        tk_img = ImageTk.PhotoImage(img)

        self.after(0, self.update_image_label, tk_img)

    def update_image_label(self, tk_img):
        self.tk_image = tk_img  # Prevents Garbage Collection. Card won't show up
        self.image_label.config(image=self.tk_image)