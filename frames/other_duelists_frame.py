from database.queries import get_all_other_duelists
from frames.duelist_mosaic_frame import DuelistMosaicFrame
from ui.duelist_details_window import DuelistDetailsWindow

class OtherDuelistsFrame(DuelistMosaicFrame):
    def __init__(self, parent, controller):
        super().__init__(
            parent,
            controller,
            title_key="select_duelist",
            search_placeholder_key="search_duelist",
            return_frame="DuelistsFrame"
        )

        self.reload_duelists()
        self.refresh_ui()

    def load_duelists(self):
        return get_all_other_duelists()

    def on_duelist_click(self, duelist_id, duelist_key):
        DuelistDetailsWindow(
            self.controller,
            duelist_id,
            duelist_key
        )