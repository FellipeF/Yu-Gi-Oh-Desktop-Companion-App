import tkinter as tk
from PIL import Image, ImageTk
import cache_image
import threading
from database.models import search_cards

class CardsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        #TODO: Add Scroll Bar so that user is able to see card list progress
        #TODO: Implement Pagination?
        #TODO: Add Filters
        #TODO: Order by different parameters
        #TODO: Since most of this is actually used on DuelistDetailsFrame, see if there's a refactoring approach for this.

        self.current_cards = []
        self.controller = controller
        self.tk_image = None

        self.title_label = tk.Label(self, font=("Arial", 14))
        self.title_label.pack(pady=10)

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

        self.image_label = tk.Label(right_frame)
        self.image_label.pack(expand=True)

        self.return_button = tk.Button(
            self,
            command=lambda: controller.show_frame("HomeFrame")
        )
        self.return_button.pack(pady=10)

        self.refresh_ui()
        self.load_cards()

    def filter_cards(self, *args):
        """Controls the Search Box"""
        name = self.search_var.get()
        language = self.controller.current_language

        self.current_cards = search_cards(name = name, language=language)
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
    #after clicking a card which image was not previously fetched.

    #TODO: Maybe implement loading spinning wheel instead?

    def load_image_async(self, card_id):
        img_path = cache_image.get_card_image(card_id)

        if not img_path:
            return

        img = Image.open(img_path).resize((200, 300))
        tk_img = ImageTk.PhotoImage(img)

        self.after(0, self.update_image_label, tk_img)

    def update_image_label(self, tk_img):
        self.tk_image = tk_img  # Prevents Garbage Collection. Card won't show up if this is not here
        self.image_label.config(image=self.tk_image)

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t("card_list"))
        self.image_label.config(text=self.controller.t("select_card"))
        self.return_button.config(text=self.controller.t("return"))

    def load_cards(self, preserve_selection=False):
        #In case user knows the name only in the original version, allow to search for the card and preserve his selection.
        language = self.controller.current_language
        selected_card_id = None

        if preserve_selection:
            selection = self.searchable_list.curselection()
            if selection:
                selected_card_id = self.current_cards[selection[0]][0]

        self.current_cards = search_cards(language=language)
        self.searchable_list.delete(0, tk.END)

        new_index = None

        for index, card in enumerate(self.current_cards):
            self.searchable_list.insert(tk.END, card[1])

            if preserve_selection and card[0] == selected_card_id:
                new_index = index

        if new_index is not None:
            self.searchable_list.selection_set(new_index)
            self.searchable_list.see(new_index)