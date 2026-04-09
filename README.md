# Yu-Gi-Oh! Desktop Companion App v0.9

The Yu-Gi-Oh! Desktop Companion App allows users to search for the most recent cards, browse duelists and their decks from the Yu-Gi-Oh! anime, games, novels and manga, and also create and share their decks with friends and fellow duelists. Includes support for translation, now working on PT-BR.

## How the App Works
<img width="1197" height="780" alt="image" src="https://github.com/user-attachments/assets/c9cbbcdd-6d10-4b69-b563-e905b73961da" />

When the app first starts, it will check for the latest list of all cards currently registered in the [YGOPRODeck](https://ygoprodeck.com/) API and for the user's Operating System language. It will then create a `yugi.db` database file and a `cache` folder where your app was downloaded to. The contents of this folder are:
- A `cards_en.json` file, that's the original card list, also used for fallback when cards are not translated on other languages. 
- A `cards_{language_code}.json` file if starting in a different language or if you decide to switch languages. Currently supported by the app is only Portuguese (`pt`) or the default English. The API also supports `fr` for French, `de` for German, `it` for Italian, so let me know if you want to help with the UI translations!
<img width="1200" height="774" alt="image" src="https://github.com/user-attachments/assets/6eca897a-1501-43f2-a3c7-956b23ca4788" />

- A `cards_info.json` that stores what is the current API card database version, when it was last checked, when it was last updated and if the created `yugi.db` file is synced to that. The app will automatically check for updates every day. The content of this file is the following .json structure:

```json
{
  "database_version": "144.86",
  "last_checked": "2026-04-09",
  "last_update": "2026-04-09",
  "database_offline_version": "144.86"
}
```

### The Database File
As mentioned, the app also creates a `yugi.db` file after parsing the JSON File, which allows easy querying and relationships to be formed, for example:
- Duelists and their decks
- Cards and their translations
- Deck and cards

<img width="1195" height="781" alt="image" src="https://github.com/user-attachments/assets/4144bc25-58b1-4948-83db-79485f566d80" />

The DB schema is the following:

<img width="1603" height="931" alt="schema" src="https://github.com/user-attachments/assets/9b28e422-471e-440f-9d9a-8cdff217b7ff" />


- `app_metadata` Table is for checking if there's has been a change on the database structure since the last version the app was released. If there was one, the app will run the migrations accordingly.
- `duelists` Table stores duelists ids, a key, the image path where their profile pictures are and a media column for use on future filters. The key is stored instead of the name because some duelists have to be translated, like Dark Magician Girl. As so, their names are handled by UI.
- `deck_categories` Table represents a deck category that is shared between duelists, like some that have a Battle City Deck.
- `deck_category_translations` Table has translations for the deck_categories. It has a language_code row that checks what is the name of that category in the desired language.
- `duelist_decks` Table has decks belonging to a duelist. They have an id, the associated duelist_id FK and the deck_category_id FK as well. The deck_category_id is NULL when a deck is unique to a duelist. It also has a key for translation and a order_index that controls what decks show up in which order when browsing deck on the app to try and preserve a chronological order of the anime.
- `duelist_deck_translations` Table handles the translation like `deck_categories_translations` does.
- `cards` Table represent the universal card type with details that aren't translated.
- `cards_translations` Table handles translation like the other translations Tables, adding also a description column for the card.
- `deck_contents` Table is for cards that are in a deck. It has both a card_id and deck_id FK, as well as a card_name and quantity. The card_name is also stored because there are some exclusive cards that weren't released by Konami and thus have no ID on the API.
- `user_decks` Table stores the custom user decks that can be shared among duelists. Apart from id and name columns, it also contains a is_used column that allows users to check inside the app if the deck was already used against another duelist. This helps for people that creates plenty of decks before trying them out.
- `user_deck_contents` Table follows the same principle of the deck_contents Table

## Browsing Duelists Decks

As mentioned, each duelist has a quantity of decks, represented by the numbers below their names.

<img width="893" height="824" alt="image" src="https://github.com/user-attachments/assets/95860de3-018e-422b-922a-cfcd28c23b2b" />

You can browse each dech deck individually and check their contents. This also includes a filter to hide/show exclusive cards and also an `Export Deck` button to share this particular deck you're seeing with other people or to import it on the app and tweak a few things, preserving the original Deck Structure.

## Card Searching and Deck Building

<img width="1194" height="774" alt="image" src="https://github.com/user-attachments/assets/44c5118e-5274-47be-a069-025575a0dc4e" />

By going to the `Check Available Cards` section, a user can check the complete list of available cards and can also filter them by name by typing the text in a searchbox. When the card is selected, the image is then fetched from the API, downloaded inside the `images` folder of the `cache` folder (it will be created if you don't already have one) and used in the app. This allows cards images to be downloaded and stored for future use only when needed instead of downloading it everytime or all at once. Currently, the API contains more than 14.000 cards. 

You can also check more details on the card. Particularly useful when searching for cards with a large description.

<img width="509" height="456" alt="image" src="https://github.com/user-attachments/assets/89db4c0d-3bb9-43f1-8c49-68f2ffa9ae2f" />

<img width="533" height="613" alt="image" src="https://github.com/user-attachments/assets/955fd783-761d-4f60-9507-c237ea3a636e" />

The card searching section is being worked on for future releases so that more filters can be added on the blank space on the right of the card image.

## User Decks
<img width="1194" height="782" alt="image" src="https://github.com/user-attachments/assets/587e9069-091d-452f-bf54-f2f350644b3e" />

In this section, you can View Custom Decks that were either your own creation or imported ones and mark them as used. You can also create and import new ones, export the selected deck in a `.json` file, edit the deck, rename and delete it.

<img width="1190" height="776" alt="image" src="https://github.com/user-attachments/assets/2f867942-04d7-421f-bd3a-75b46b7ef4b0" />

Inside each deck, you can edit it to your own liking, the card total will automatically reflect on how many cards you have so you keep track to now go over the limit. You can also remove one copy or remove all copies of the same card with just one click.

## How To Run

After cloning the repository, check `requirements.txt` for the Python dependencies needed to run the project. After that, just run `python main.py`and you're good to go.

## Please Note:
- Cards translations are not handled by the app, so if you see a card that is currently not translated, check it out later when the API updates
- You need Internet connection to open the app for the first time, since it needs to download the cards data. You also need it to download images from the API, but once downloaded and stored in your computer, the app uses that instead. You can use the rest of the app without any internet connection.
- Feel free to send me an e-mail for suggestions or open a Issue here on GitHub for any problem. I'll gladly help if I can do so.

## Technologies and Knowledge Used

- API Handling to check for cards and updates
- JSON file parsing to create a SQL Database.
- SQL to create relations between characters, decks and translations
- Python + Tkinter for UI and logic.
- HTML and CSS for the Card Consistency File
- Use of Upserts and Migrations to handle change of schema and data
- i18n
- Implementing a quasi-MVC model, where Frames and translations are handled by the Controller.

## Yu-Gi-Oh! Notes

Please read the Card Consistency File - CFF on the /docs folder. It explains some decisions as to why some decks are inconsistent with their Anime Counterparts, especially those in the First Toei Series or first seasons of the anime.

## Credits
* [AlanOC91](https://github.com/AlanOC91) for developing the YGOPRODeck API.
* [AlanMac95](https://www.deviantart.com/alanmac95) for the Millennium Puzzle Icon used on placeholder images.
* [Konami](https://www.yugioh.com/) for creating Yu-Gi-Oh! Trading Card Game and for character images.
* [Yu-Gi-Oh! Fandom](https://yugioh.fandom.com/wiki/Yu-Gi-Oh!_Wiki) for decks lists.
* DB Diagram for the Schema Builder.

## Legal Disclaimer

This project is not affiliated with Konami or the Yu-Gi-Oh! IP. This is just a fan project, all images and rights belong to the respective IP holders.