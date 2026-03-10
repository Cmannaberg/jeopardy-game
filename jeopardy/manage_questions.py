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
    add-photo-clue THEME CATEGORY --source /path/to/image --clue "..."
                                 # copy image into photos/, add photo clue entry,
                                 # and generate matching thumbnail
    refresh-thumbnails           # rebuild all thumbnails from photos/
    refresh-thumbnails --filename "kippah.jpeg"
                                 # rebuild one specific thumbnail
    remove-photo-clue THEME CATEGORY --index N [--delete-files]
                                 # remove one clue by 1-based index
    remove-photo-clue THEME CATEGORY --photo "name.jpeg" [--delete-files] [--all]
                                 # remove clue(s) by photo filename
    list-category THEME CATEGORY  # print indexed clues for one category

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
import shutil
import subprocess
import sys
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(__file__), 'questions_db.json')
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), 'photos')
THUMBS_DIR = os.path.join(os.path.dirname(__file__), 'thumbnails')


def ensure_media_dirs():
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    os.makedirs(THUMBS_DIR, exist_ok=True)


def load_db():
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def generate_thumbnail(filename, size=200):
    """Generate/update one thumbnail from photos/<filename>.

    Returns True on success, False otherwise.
    """
    src = os.path.join(PHOTOS_DIR, filename)
    dst = os.path.join(THUMBS_DIR, filename)
    if not os.path.exists(src):
        return False

    # Prefer macOS built-in sips for image resize.
    try:
        result = subprocess.run(
            ['sips', '-Z', str(size), src, '--out', dst],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0 and os.path.exists(dst):
            return True
    except FileNotFoundError:
        pass

    # Fallback to Pillow if sips is unavailable.
    try:
        from PIL import Image  # type: ignore

        with Image.open(src) as img:
            img.thumbnail((size, size))
            img.save(dst)
        return os.path.exists(dst)
    except Exception:
        return False


def refresh_thumbnails(filename=None, size=200):
    ensure_media_dirs()
    if filename:
        ok = generate_thumbnail(filename, size=size)
        if ok:
            print('Refreshed thumbnail:', filename)
        else:
            print('Failed to refresh thumbnail:', filename)
        return

    photo_files = sorted(
        [
            name
            for name in os.listdir(PHOTOS_DIR)
            if os.path.isfile(os.path.join(PHOTOS_DIR, name))
        ]
    )
    ok_count = 0
    fail_count = 0
    for name in photo_files:
        if generate_thumbnail(name, size=size):
            ok_count += 1
        else:
            fail_count += 1
            print('Failed:', name)
    print(f'Refreshed thumbnails: {ok_count}, Failed: {fail_count}')


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


def list_category(db, theme, category):
    if theme not in db:
        print('Theme does not exist:', theme)
        return
    if category not in db[theme]:
        print('Category does not exist under theme:', category)
        return

    qs = db[theme][category]
    if not isinstance(qs, list):
        print('Category has invalid structure:', category)
        return

    print(f'Theme: {theme}')
    print(f'Category: {category}')
    if not qs:
        print('  (no clues)')
        return

    for i, q in enumerate(qs, start=1):
        if not isinstance(q, dict):
            print(f'  {i}. <invalid clue entry>')
            continue
        clue = q.get('clue', '<no clue>')
        diff = q.get('difficulty', '?')
        if q.get('photo'):
            ans_or_photo = f"photo={q.get('photo')}"
        else:
            ans_or_photo = f"answer={q.get('answer', '<no answer>')}"
        print(f'  {i}. {clue} ({ans_or_photo}, difficulty={diff})')


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


def add_photo_clue(db, theme, category, source, clue, difficulty=1, filename=None):
    if theme not in db:
        print('Theme does not exist:', theme)
        return
    if category not in db[theme]:
        print('Category does not exist under theme:', category)
        return

    ensure_media_dirs()

    src_path = Path(source)
    if not src_path.exists() or not src_path.is_file():
        print('Source file does not exist:', source)
        return

    target_name = filename.strip() if filename else src_path.name
    target_path = Path(PHOTOS_DIR) / target_name

    if target_path.exists() and src_path.resolve() != target_path.resolve():
        print('Target photo filename already exists in photos/:', target_name)
        print('Use --filename to choose a different name.')
        return

    if src_path.resolve() != target_path.resolve():
        shutil.copy2(src_path, target_path)
        print('Copied photo to photos/:', target_name)
    else:
        print('Photo already in photos/:', target_name)

    entry = {
        'clue': clue.strip(),
        'photo': target_name,
        'difficulty': int(difficulty) if str(difficulty).isdigit() else 1,
    }
    db[theme][category].append(entry)
    save_db(db)
    print('Added photo clue to', category, 'in', theme)

    if generate_thumbnail(target_name):
        print('Generated thumbnail:', target_name)
    else:
        print('Warning: could not generate thumbnail for', target_name)


def remove_photo_clue(db, theme, category, index=None, photo=None, delete_files=False, remove_all=False):
    if theme not in db:
        print('Theme does not exist:', theme)
        return
    if category not in db[theme]:
        print('Category does not exist under theme:', category)
        return

    qs = db[theme][category]
    if not isinstance(qs, list):
        print('Category has invalid structure:', category)
        return

    to_remove = []
    if index is not None:
        idx = index - 1
        if idx < 0 or idx >= len(qs):
            print('Index out of range. Use 1-based index within category.')
            return
        to_remove = [idx]
    elif photo:
        for i, q in enumerate(qs):
            if isinstance(q, dict) and q.get('photo') == photo:
                to_remove.append(i)
        if not to_remove:
            print('No clue found with photo filename:', photo)
            return
        if (not remove_all) and len(to_remove) > 1:
            print('Multiple clues match this photo. Re-run with --all to remove all matches.')
            return
        if not remove_all:
            to_remove = [to_remove[0]]
    else:
        print('Specify either --index or --photo.')
        return

    removed_entries = []
    removed_photos = []
    for i in sorted(to_remove, reverse=True):
        entry = qs.pop(i)
        removed_entries.append(entry)
        if isinstance(entry, dict) and entry.get('photo'):
            removed_photos.append(entry['photo'])

    save_db(db)
    print(f'Removed clue entries: {len(removed_entries)}')
    for entry in removed_entries:
        if isinstance(entry, dict):
            print('  clue:', entry.get('clue', '<no clue>'))
            if entry.get('photo'):
                print('  photo:', entry.get('photo'))

    if delete_files:
        unique_photos = sorted(set(removed_photos))
        for filename in unique_photos:
            photo_path = os.path.join(PHOTOS_DIR, filename)
            thumb_path = os.path.join(THUMBS_DIR, filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)
                print('Deleted photo file:', filename)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
                print('Deleted thumbnail file:', filename)


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

    p4 = sub.add_parser('add-photo-clue', help='Add photo clue and copy image into photos/')
    p4.add_argument('theme')
    p4.add_argument('category')
    p4.add_argument('--source', required=True, help='Path to source image file')
    p4.add_argument('--clue', required=True, help='Clue text')
    p4.add_argument('--difficulty', type=int, default=1, help='Difficulty 1-5')
    p4.add_argument('--filename', help='Optional target filename inside photos/')

    p5 = sub.add_parser('refresh-thumbnails', help='Refresh thumbnails from photos/')
    p5.add_argument('--filename', help='Refresh just one thumbnail by filename')
    p5.add_argument('--size', type=int, default=200, help='Max thumbnail dimension')

    p6 = sub.add_parser('remove-photo-clue', help='Remove photo clue(s) and optionally matching media files')
    p6.add_argument('theme')
    p6.add_argument('category')
    p6.add_argument('--index', type=int, help='1-based index of clue in category list')
    p6.add_argument('--photo', help='Remove clue(s) by matching photo filename')
    p6.add_argument('--all', action='store_true', help='With --photo, remove all matching clues')
    p6.add_argument('--delete-files', action='store_true', help='Also delete matching files from photos/ and thumbnails/')

    p7 = sub.add_parser('list-category', help='List indexed clues for one category')
    p7.add_argument('theme')
    p7.add_argument('category')

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    db = load_db()
    if args.cmd == 'list':
        list_db(db)
    elif args.cmd == 'list-category':
        list_category(db, args.theme, args.category)
    elif args.cmd == 'add-theme':
        add_theme(db, args.theme)
    elif args.cmd == 'add-category':
        add_category(db, args.theme, args.category)
    elif args.cmd == 'add-clue':
        add_clue(db, args.theme, args.category)
    elif args.cmd == 'add-photo-clue':
        add_photo_clue(
            db,
            args.theme,
            args.category,
            source=args.source,
            clue=args.clue,
            difficulty=args.difficulty,
            filename=args.filename,
        )
    elif args.cmd == 'refresh-thumbnails':
        refresh_thumbnails(filename=args.filename, size=args.size)
    elif args.cmd == 'remove-photo-clue':
        remove_photo_clue(
            db,
            args.theme,
            args.category,
            index=args.index,
            photo=args.photo,
            delete_files=args.delete_files,
            remove_all=args.all,
        )


if __name__ == '__main__':
    main()
