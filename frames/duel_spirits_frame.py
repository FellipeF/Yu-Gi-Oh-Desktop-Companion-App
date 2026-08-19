from database.queries import get_all_duel_spirits
from frames.duelist_mosaic_frame import DuelistMosaicFrame
from ui.duelist_details_window import DuelistDetailsWindow

class DuelSpiritsFrame(DuelistMosaicFrame):
    def __init__(self, parent, controller):
        super().__init__(
            parent,
            controller,
            title_key="select_duel_spirit",
            search_placeholder_key="search_duel_spirit",
            return_frame="DuelistsFrame"
        )

        self.reload_duelists()
        self.refresh_ui()

    def load_duelists(self):
        return get_all_duel_spirits()

    def on_duelist_click(self, duelist_id, duelist_key):
        DuelistDetailsWindow(
            self.controller,
            duelist_id,
            duelist_key
        )