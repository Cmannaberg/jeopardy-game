#!/usr/bin/env python3
"""Utility for inspecting and editing the Jeopardy question database.

This is a very simple command‑line program you can modify and extend to suit
your workflow.  It reads and writes ``questions_db.json`` in the same
directory.

Currently supported actions:

    list                         # print all themes/categories/questions
    add-theme THEME              # add an empty theme if it doesn't exist
    add-category THEME CATEGORY  # add an empty category under a theme
    add-clue THEME CATEGORY      # interactively prompt for a clue/answer/difficulty

Feel free to expand the parsing or add a little web interface if you'd
like; the JSON format is left intentionally open, so anything that
constructs a dictionary with the same structure will be accepted by
:mod:`flask_app`.

The Flask application does **not** need to be modified when you update the
JSON file; it reads the file fresh when a new game starts.  Just restart
or reload the server if it is already running, and the new questions will
be available.
"""

import argparse
import json
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'questions_db.json')


def load_db():
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def list_db(db):
    for theme, cats in db.items():
        print(f'Theme: {theme}')
        for cat, qs in cats.items():
            print(f'  Category: {cat}')
            for q in qs:
                clue = q.get('clue')
                ans = q.get('answer', q.get('photo', '<no answer>'))
                diff = q.get('difficulty', '?')
                print(f'    - {clue} (answer: {ans}, difficulty: {diff})')
        print()


def add_theme(db, theme):
    if theme in db:
        print('Theme already exists:', theme)
    else:
        db[theme] = {}
        save_db(db)
        print('Added theme', theme)


def add_category(db, theme, category):
    if theme not in db:
        print('Theme does not exist, creating it:', theme)
        db[theme] = {}
    if category in db[theme]:
        print('Category already exists under theme:', category)
    else:
        db[theme][category] = []
        save_db(db)
        print('Added category', category, 'to theme', theme)


def add_clue(db, theme, category):
    if theme not in db:
        print('Theme does not exist:', theme)
        return
    if category not in db[theme]:
        print('Category does not exist under theme:', category)
        return
    clue = input('Clue text: ').strip()
    photo = input('Photo filename (leave blank if not an image): ').strip()
    if photo:
        entry = {'clue': clue, 'photo': photo}
        # answer will be derived from filename when the board is built
    else:
        answer = input('Answer (comma-separated for alternatives): ').strip()
        difficulty = input('Difficulty (1-5): ').strip()
        entry = {'clue': clue, 'answer': answer, 'difficulty': int(difficulty) if difficulty.isdigit() else 1}
    db[theme][category].append(entry)
    save_db(db)
    print('Added clue to', category, 'in', theme)


def main():
    parser = argparse.ArgumentParser(description='Manage Jeopardy question database')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('list', help='List all themes/categories/questions')
    p = sub.add_parser('add-theme', help='Add a new theme')
    p.add_argument('theme')
    p2 = sub.add_parser('add-category', help='Add a category to a theme')
    p2.add_argument('theme')
    p2.add_argument('category')
    p3 = sub.add_parser('add-clue', help='Interactively add a clue/question')
    p3.add_argument('theme')
    p3.add_argument('category')

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    db = load_db()
    if args.cmd == 'list':
        list_db(db)
    elif args.cmd == 'add-theme':
        add_theme(db, args.theme)
    elif args.cmd == 'add-category':
        add_category(db, args.theme, args.category)
    elif args.cmd == 'add-clue':
        add_clue(db, args.theme, args.category)


if __name__ == '__main__':
    main()
