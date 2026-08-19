import tkinter as tk

from database.queries import get_all_duelists, get_duel_spirits_count
from ui.duelist_details_window import DuelistDetailsWindow
from frames.duelist_mosaic_frame import DuelistMosaicFrame, NavigationItem

class DuelistsFrame(DuelistMosaicFrame):
    def __init__(self, parent, controller):
        """List of all duelists by alphabetical order based on their display name available on the ui_text.py file"""
        super().__init__(parent,
                         controller,
                         title_key="select_duelist",
                         search_placeholder_key="search_duelist",
                         return_frame="HomeFrame"
                         )

        self.selected_media = tk.StringVar(value="all")
        self.media_options = {
            "all": "filter_all",
            "duel_monsters_anime": "duel_monsters_anime",
            "gx": "gx",
        }

        self.filter_container = tk.Frame(self.top_bar)
        self.filter_container.pack(side="right", anchor="e", padx=(0, 25))

        self.filters_label = tk.Label(
            self.filter_container,
            font=("Arial", 11, "bold"),
            anchor="w",
            justify="left"
        )
        self.filters_label.pack(anchor="w", pady=(0, 2))

        self.media_filter_button = tk.Menubutton(
            self.filter_container,
            relief="raised",
            borderwidth=2,
            cursor="hand2",
            font=("Arial", 10),
            padx=10,
            pady=2,
            width=18,
            indicatoron=False,
            bg="#f5f5f5",
            activebackground="#e2e2e2",
        )
        self.media_filter_button.menu = tk.Menu(self.media_filter_button,tearoff=0,)
        self.media_filter_button["menu"] = self.media_filter_button.menu
        self.media_filter_button.pack(anchor="w")

        self.duel_spirits_count = get_duel_spirits_count() # So it doesn't count everytime a filter is applied
        self.reload_duelists()
        self.refresh_ui()

    def load_duelists(self):
        return get_all_duelists()

    def get_navigation_duelists(self):
        return [
            NavigationItem(
                key="duel_spirits",
                img_path="images/duel_spirits.webp",
                target_frame="DuelSpiritsFrame",
                display_count=self.duel_spirits_count
            )
        ]

    def filter_real_duelists(self, duelists):
        selected_media = (self.selected_media.get())
        if selected_media == "all":
            return duelists

        return [duelist for duelist in duelists if duelist[3] == selected_media]

    def update_media_filter_text(self):
        translation_key = self.media_options[self.selected_media.get()]

        self.media_filter_button.config(text=f"{self.controller.t(translation_key)} ▼")

    def filter_by_media(self):
        self.filter_duelists(reset_page = True)
        self.update_media_filter_text()

    def on_duelist_click(self,duelist_id,duelist_key):
        DuelistDetailsWindow(self.controller,duelist_id,duelist_key)

    def sort_duelists(self):
        """Sorts duelist by Display name that is handled by the translation file. Navigation categories are last"""
        self.duelists.sort(
            key = lambda duelist: (
                self.is_navigation_duelist(duelist),
                self.controller.t(self.get_duelist_key(duelist)).casefold()
            )
        )

    def refresh_ui(self):
        super().refresh_ui()

        self.filters_label.config(text=self.controller.t("filter_by"))

        menu = self.media_filter_button.menu
        menu.delete(0, "end")

        for media_key, translation_key in self.media_options.items():
            menu.add_command(
                label=self.controller.t(translation_key),
                command=lambda value=media_key: (
                    self.selected_media.set(value),
                    self.filter_by_media()
                )
            )

        self.update_media_filter_text()