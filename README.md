# StudyPal
# StudyPal – Spaced Repetition Flashcards

StudyPal is a simple command-line tool for creating, reviewing, and managing flashcards with spaced repetition scheduling. It stores cards locally in JSON format and helps you study efficiently using proven review intervals.

## Features
- Add and edit flashcards from the terminal  
- Practice due cards each day with a 0–5 grading system  
- Automatic scheduling using the SM-2 algorithm  
- View deck statistics and upcoming review forecast  
- Lightweight and easy to use, all data stored in `studypal_deck.json`

## Installation
No external dependencies are required beyond Python 3.  

Clone or download this repository, then run commands directly with `python`.

## Usage

Add a new flashcard:
```bash
python studypal.py add "What is the Big-O of binary search?" "O(log n)"
```

Practice cards that are due today:
```bash
python studypal.py practice
```

View statistics:
```bash
python studypal.py stats
```

List all cards:
```bash
python studypal.py list
```

Edit a card:
```bash
python studypal.py edit 1 --question "Updated question"
```

Delete a card:
```bash
python studypal.py delete 1
```

## Data Storage
All flashcards and scheduling data are saved locally in `studypal_deck.json`.  
You can back up or share this file to transfer your deck.

---

Happy studying! 🚀
