# StudyPal – Spaced Repetition Flashcards

StudyPal is a command-line tool that lets you create, review, and manage flashcards using spaced repetition scheduling. It stores cards locally and provides practice sessions with scoring.

## How to Run

```bash
python studypal.py add "Question?" "Answer"
python studypal.py practice
python studypal.py stats
python studypal.py list
```


```python
from __future__ import annotations
import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import random

DECK_PATH = Path("studypal_deck.json")
DATE_FMT = "%Y-%m-%d"
NOW = lambda: datetime.now()

@dataclass
class Card:
    id: int
    question: str
    answer: str
    repetitions: int = 0
    interval: int = 0
    ease: float = 2.5
    due: str = datetime.now().strftime(DATE_FMT)
    created: str = datetime.now().strftime(DATE_FMT)
    last_review: Optional[str] = None

    def is_due(self, today: datetime) -> bool:
        try:
            due_date = datetime.strptime(self.due, DATE_FMT)
        except ValueError:
            return True
        return due_date.date() <= today.date()

@dataclass
class Deck:
    next_id: int
    cards: List[Card]

    @staticmethod
    def load(path: Path) -> 'Deck':
        if not path.exists():
            return Deck(next_id=1, cards=[])
        data = json.loads(path.read_text(encoding="utf-8"))
        cards = [Card(**c) for c in data.get("cards", [])]
        return Deck(next_id=data.get("next_id", len(cards)+1), cards=cards)

    def save(self, path: Path):
        data = {"next_id": self.next_id, "cards": [asdict(c) for c in self.cards]}
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add(self, q: str, a: str) -> Card:
        c = Card(id=self.next_id, question=q.strip(), answer=a.strip())
        self.cards.append(c)
        self.next_id += 1
        return c

    def due_cards(self, today: datetime) -> List[Card]:
        return [c for c in self.cards if c.is_due(today)]

def sm2_schedule(card: Card, quality: int, today: datetime) -> Card:
    q = max(0, min(5, quality))
    card.ease = max(1.3, card.ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))

    if q < 3:
        card.repetitions = 0
        card.interval = 1
    else:
        if card.repetitions == 0:
            card.interval = 1
            card.repetitions = 1
        elif card.repetitions == 1:
            card.interval = 6
            card.repetitions = 2
        else:
            card.interval = int(round(card.interval * card.ease))
            card.repetitions += 1

    next_due = today + timedelta(days=card.interval)
    card.due = next_due.strftime(DATE_FMT)
    card.last_review = today.strftime(DATE_FMT)
    return card

def cmd_add(deck: Deck, args):
    c = deck.add(args.question, args.answer)
    deck.save(DECK_PATH)
    print(f"[+] Added card #{c.id}")

def cmd_practice(deck: Deck, args):
    today = NOW()
    due = deck.due_cards(today)
    if not due:
        print("No cards due today.")
        return

    random.shuffle(due)
    total = len(due)
    correctish = 0

    print(f"Due today: {total} cards\n(Enter 'q' anytime to stop)\n")

    for c in due:
        print("-"*60)
        print(f"#{c.id} Q: {c.question}")
        input("Show answer (Enter)...")
        print(f"A: {c.answer}")
        while True:
            g = input("Grade 0..5: ").strip().lower()
            if g == 'q':
                deck.save(DECK_PATH)
                print("Saved. Bye!")
                return
            if g.isdigit() and 0 <= int(g) <= 5:
                g = int(g)
                break
            print("Please enter a number 0..5 or 'q'.")
        if g >= 3:
            correctish += 1
        sm2_schedule(c, g, today)
        deck.save(DECK_PATH)
    print("-"*60)
    acc = 100 * correctish / total if total else 0.0
    print(f"Session done. Accuracy (>=3): {acc:.1f}% • Reviewed: {total}")

def cmd_stats(deck: Deck, args):
    today = NOW().date()
    total = len(deck.cards)
    due = sum(1 for c in deck.cards if c.is_due(datetime.now()))
    learned = sum(1 for c in deck.cards if c.repetitions >= 2)
    avg_ease = (sum(c.ease for c in deck.cards) / total) if total else 0

    print("== StudyPal Stats ==")
    print(f"Total cards: {total}")
    print(f"Due today: {due}")
    print(f"Learned (rep>=2): {learned}")
    print(f"Average ease: {avg_ease:.2f}")

    buckets = {i: 0 for i in range(0, 8)}
    for c in deck.cards:
        try:
            d = datetime.strptime(c.due, DATE_FMT).date()
        except ValueError:
            continue
        delta = (d - today).days
        if 0 <= delta <= 7:
            buckets[delta] += 1
    print("\nReviews coming up (next 7 days):")
    for k in range(0, 8):
        label = "today" if k == 0 else f"+{k}d"
        bars = "█" * buckets[k]
        print(f"{label:>5}: {buckets[k]:3} {bars}")

def cmd_list(deck: Deck, args):
    if not deck.cards:
        print("No cards yet. Use 'add' to create one.")
        return
    for c in deck.cards:
        print(f"#{c.id} | due {c.due} | rep {c.repetitions} | ease {c.ease:.2f}\nQ: {c.question}\nA: {c.answer}\n")

def cmd_edit(deck: Deck, args):
    cid = args.id
    card = next((c for c in deck.cards if c.id == cid), None)
    if not card:
        print("Card not found.")
        return
    if args.question:
        card.question = args.question
    if args.answer:
        card.answer = args.answer
    deck.save(DECK_PATH)
    print(f"Edited card #{cid}.")

def cmd_delete(deck: Deck, args):
    cid = args.id
    before = len(deck.cards)
    deck.cards = [c for c in deck.cards if c.id != cid]
    if len(deck.cards) == before:
        print("Card not found.")
    else:
        deck.save(DECK_PATH)
        print(f"Deleted card #{cid}.")

def main():
    deck = Deck.load(DECK_PATH)

    ap = argparse.ArgumentParser(description="StudyPal – spaced repetition flashcards")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a new card")
    p_add.add_argument("question", type=str)
    p_add.add_argument("answer", type=str)
    p_add.set_defaults(func=cmd_add)

    p_pr = sub.add_parser("practice", help="Review due cards")
    p_pr.set_defaults(func=cmd_practice)

    p_stats = sub.add_parser("stats", help="Show deck statistics")
    p_stats.set_defaults(func=cmd_stats)

    p_list = sub.add_parser("list", help="List all cards")
    p_list.set_defaults(func=cmd_list)

    p_edit = sub.add_parser("edit", help="Edit a card by id")
    p_edit.add_argument("id", type=int)
    p_edit.add_argument("--question", type=str)
    p_edit.add_argument("--answer", type=str)
    p_edit.set_defaults(func=cmd_edit)

    p_del = sub.add_parser("delete", help="Delete a card by id")
    p_del.add_argument("id", type=int)
    p_del.set_defaults(func=cmd_delete)

    args = ap.parse_args()
    args.func(deck, args)

if __name__ == "__main__":
    main()

```
