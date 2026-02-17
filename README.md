# Yu-Gi-Oh! Offline Database v0.5

Offline application to view cards and duelist decks for the Yu-Gi-Oh Card TCG. Includes support for translation, currently working on PT-BR.
Cards and their images are obtained via public API from [YGOPRODeck](https://ygoprodeck.com/).
They are stored locally using SQLite after caching them with JSON.

## Please Note:

- While this is an offline database, you still need Internet connection on the first execution to download the data.
- As so, program may take a few seconds to load on your first execution.

## Python Dependecies
Check `requirements.txt` for:
- `requests` for the API requests to be made
- `Pillow` for the Images.

As mentioned, this project also uses `sqlite3` along with `tkinter`, do check if they came included with your Python installation as it should be.

## Technologies Used

- SQL, Python and JSON for card database creation
- HTML and CSS for docs

## How To Run

After cloning the repository, just run

`python main.py`and you're good to go.

## Some TODOS Here to Keep You Informed:

Currently, only 4 of Yugi's Decks are available, you can see which ones when you run the program. I may model the database with some diagram later, but you can check it out on database.py and how it's manipulated in models.py.

## Yu-Gi-Oh! Notes

Please read the Card Consistency File - CFF on the /docs folder. It explains some decisions as to why some decks are inconsistent with their Anime Counterparts, especially those in the First Toei Series or first seasons of the anime.

## Legal Disclaimer

This project is not affiliated with Konami or the Yu-Gi-Oh! IP. This is just a fan project, all images and rights belong to them.
