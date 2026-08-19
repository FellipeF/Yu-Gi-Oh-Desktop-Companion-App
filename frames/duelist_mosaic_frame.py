import tkinter as tk
from dataclasses import dataclass
from PIL import Image, ImageTk

from utils.resource_path import resource_path
from utils.search_bar import SearchBar

@dataclass(frozen=True)
class NavigationItem:
    key: str
    img_path: str
    target_frame: str
    display_count: int | None = None #How many Duel Spirits are there

class DuelistMosaicFrame(tk.Frame):
    def __init__(
        self,
        parent,
        controller,
        title_key,
        search_placeholder_key,
        return_frame,
        duelists_per_page=8
    ):
        super().__init__(parent)

        self.controller = controller

        self.title_key = title_key
        self.search_placeholder_key = search_placeholder_key
        self.return_frame = return_frame

        self.all_duelists = [] # From database
        self.duelists = [] # Final visible mosaic (DB + Navigation)

        self.search_var = tk.StringVar()
        self.last_search_text = ""

        self.current_page = 0
        self.duelists_per_page = duelists_per_page

        self.header_container = tk.Frame(self)
        self.header_container.pack(fill="x",padx=10,pady=(10, 5))

        self.title_label = tk.Label(self.header_container,font=("Arial", 16))
        self.title_label.pack(pady=(0, 10))

        self.top_bar = tk.Frame(self.header_container)
        self.top_bar.pack(fill="x")

        self.search_container = tk.Frame(self.top_bar)
        self.search_container.pack(side="left",anchor="w")

        self.search_bar = SearchBar(
            self.search_container,
            textvariable=self.search_var,
            placeholder=self.controller.t(
                self.search_placeholder_key
            ),
            on_change=self.filter_duelists,
            width=25
        )

        self.search_bar.pack(side="left")

        self.container = tk.Frame(self,width=self.controller.app_width,height=505)

        self.container.pack(fill="both",expand=True)

        self.container.pack_propagate(False)

        for column in range(4):
            self.container.columnconfigure(column,weight=1,uniform="col")

        self.footer = tk.Frame(self)
        self.footer.pack(side="bottom",fill="x")

        self.footer.columnconfigure(0, weight=1)
        self.footer.columnconfigure(1, weight=1)
        self.footer.columnconfigure(2, weight=1)

        self.prev_button = tk.Button(
            self.footer,
            text="←",
            font=("Tahoma", 12),
            command=self.prev_page
        )

        self.prev_button.grid(row=0,column=0,sticky="w",padx=20)

        self.return_button = tk.Button(self.footer,font=("Tahoma", 12),command=self.return_to_previous_frame)

        self.return_button.grid(row=0,column=1,pady=2)

        self.next_button = tk.Button(
            self.footer,
            text="→",
            font=("Tahoma", 12),
            command=self.next_page
        )

        self.next_button.grid(row=0,column=2,sticky="e",padx=20)

    def load_duelists(self):
        """
        Must be implemented by the child frame.
        Should return:
            (id, key, img_path, media, deck_count)
        """
        raise NotImplementedError

    def get_navigation_duelists(self):
        """
        Returns virtual navigation items.

        Child frames can override this method when they need
        virtual entries such as Duel Monsters or Other Duelists.
        """

        return []

    def filter_real_duelists(self, duelists):
        """
        Hook for child frames that need additional filtering.

        DuelistsFrame, for example, overrides this method
        to filter by anime/media.
        """
        return duelists

    def on_duelist_click(self, duelist_id, duelist_key):
        """Must be implemented by the child frame."""
        raise NotImplementedError

    def reload_duelists(self):
        self.all_duelists = self.load_duelists()
        self.filter_duelists(force_refresh=True)

    def is_navigation_duelist(self, duelist):
        return isinstance(duelist, NavigationItem)

    def get_duelist_key(self, duelist):
        if self.is_navigation_duelist(duelist):
            return duelist.key

        return duelist[1]

    def get_duelist_image_path(self, duelist):
        if self.is_navigation_duelist(duelist):
            return duelist.img_path

        return duelist[2]

    def get_duelist_display_count(self, duelist):
        if self.is_navigation_duelist(duelist):
            return duelist.display_count # If duelist, return deck qty. If other, return qty of duelists inside

        return duelist[4]

    def filter_duelists(self, event=None, reset_page=False, force_refresh=False):
        search_text = self.search_bar.get_text().casefold()

        search_changed = (search_text != self.last_search_text)

        # Prevents app reloading when it triggered an out of focus because of a duelist decks window being created
        if not search_changed and not reset_page and not force_refresh:
            return

        self.last_search_text = search_text

        real_duelists = self.all_duelists.copy()
        real_duelists = self.filter_real_duelists(real_duelists)

        navigation_duelists = (self.get_navigation_duelists())
        duelists = (real_duelists + navigation_duelists)

        if search_text:
            duelists = [duelist
                        for duelist in duelists
                        if search_text in self.controller.t(self.get_duelist_key(duelist))
                        .casefold()
                        ]

        self.duelists = duelists

        if search_changed or reset_page:
            self.current_page = 0

        self.sort_duelists()
        self.render_page()

    def sort_duelists(self):
        self.duelists.sort(
            key=lambda duelist:
            self.controller.t(self.get_duelist_key(duelist)).casefold()
        )

    def render_page(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        start = (self.current_page* self.duelists_per_page)

        end = start + self.duelists_per_page

        page_duelists = self.duelists[start:end]

        row = 0
        col = 0

        for duelist in page_duelists:
            self.render_duelist(duelist,row,col)

            col += 1

            if col == 4:
                col = 0
                row += 1

        self.update_pagination_buttons()

    def render_duelist(self,duelist,row,col):

        duelist_key = self.get_duelist_key(duelist)
        img_path = self.get_duelist_image_path(duelist)
        display_count = self.get_duelist_display_count(duelist)

        img = Image.open(resource_path(img_path)).convert("RGBA")

        frame_width = 220
        frame_height = 260

        img.thumbnail((200, 240),Image.LANCZOS)

        background = Image.new("RGBA",(frame_width, frame_height),(235, 235, 235, 255))

        x = (frame_width - img.width) // 2

        y = (frame_height - img.height) // 2

        background.paste(img,(x, y),img)

        tk_img = ImageTk.PhotoImage(background)

        cell = tk.Frame(
            self.container,
            width=240,
            height=320,
            bg="#dcdcdc",
            highlightbackground="#b0b0b0",
            highlightthickness=1
        )

        cell.grid(row=row,column=col, padx=25,pady=25,sticky="n")
        cell.grid_propagate(False)

        duelist_button = tk.Button(
            cell,
            image=tk_img,
            command=lambda d = duelist: self.handle_duelist_click(d),
            cursor="hand2"
        )

        duelist_button.image = tk_img
        duelist_button.pack()

        display_name = self.controller.t(duelist_key)
        if display_count is not None:
            label_text = (f"{display_name}\n"
                          f"({display_count})")
        else:
            label_text = display_name

        name_label = tk.Label(
            cell,
            text=label_text,
            font=("Arial", 15),
            wraplength=220,
            height=3,
            justify="center"
        )

        name_label.pack(fill="x")

    def handle_duelist_click(self, duelist):
        if self.is_navigation_duelist(duelist):
            self.controller.show_frame(duelist.target_frame)
            return

        duelist_id = duelist[0]
        duelist_key = duelist[1]

        self.on_duelist_click(duelist_id, duelist_key)

    def update_pagination_buttons(self):
        self.prev_button.config(state=("disabled" if self.current_page == 0 else "normal"))

        is_last_page = ((self.current_page + 1)* self.duelists_per_page >= len(self.duelists))

        self.next_button.config(state=("disabled" if is_last_page else "normal"))

    def next_page(self):
        if (self.current_page + 1)* self.duelists_per_page< len(self.duelists):
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def return_to_previous_frame(self):
        self.controller.show_frame(
            self.return_frame
        )

    def refresh_ui(self):
        self.title_label.config(text=self.controller.t(self.title_key))

        self.return_button.config(text=self.controller.t("return"))

        self.search_bar.placeholder = (self.controller.t(self.search_placeholder_key))

        if self.search_bar.placeholder_active:
            self.search_bar.set_placeholder()

        self.filter_duelists(force_refresh=True)