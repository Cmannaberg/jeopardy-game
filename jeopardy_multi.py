#!/usr/bin/env python3
"""Simple multiplayer Jeopardy CLI game with dynamic category selection.

Run: python3 jeopardy_3.py
"""
import sys
import json
import os


def load_questions_db():
    """Load questions from the separate database file."""
    db_path = os.path.join(os.path.dirname(__file__), 'questions_db.json')
    try:
        with open(db_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error: Could not load questions from {db_path}")
        sys.exit(1)


def build_board(all_questions):
    """Build the board from all categories and their questions."""
    difficulty_to_value = {1: 100, 2: 200, 3: 300, 4: 400, 5: 500}
    board = {}
    
    for category, questions in all_questions.items():
        board[category] = []
        for q in questions:
            value = difficulty_to_value.get(q.get('difficulty', 1), 100)
            board[category].append({
                'clue': q['clue'],
                'answer': q['answer'],
                'value': value,
                'difficulty': q.get('difficulty', 1),
                'asked': False
            })
        board[category].sort(key=lambda x: x['value'])
    return board


def all_questions_asked(board):
    for cat in board.values():
        for q in cat:
            if not q['asked']:
                return False
    return True


def display_board(board):
    cats = list(board.keys())
    print('\nBoard:')
    for i, cat in enumerate(cats, 1):
        print(f"{i}. {cat}")
        row = []
        for q in board[cat]:
            row.append('X' if q['asked'] else str(q['value']))
        print('   ' + '  '.join(row))


def find_question(board, cat_idx, value):
    cats = list(board.keys())
    try:
        cat = cats[cat_idx]
    except IndexError:
        return None, None
    for q in board[cat]:
        if q['value'] == value:
            return cat, q
    return None, None


def normalize(s):
    return ''.join(ch for ch in s.lower() if ch.isalnum())


def check_answer(response, correct_answer):
    """Check if response matches correct answer(s). Handle both string and array formats."""
    if isinstance(correct_answer, list):
        answers = correct_answer
    else:
        # Split comma-separated answers
        answers = [ans.strip() for ans in correct_answer.split(',')]
    return any(normalize(response) == normalize(ans) for ans in answers)


def format_answer(answer):
    """Format answer for display. Show all options if array."""
    if isinstance(answer, list):
        return ' / '.join(answer)
    return answer


def ask_question(player, cat, q):
    print(f"\n{player}, for ${q['value']} in {cat}:")
    print(q['clue'])
    ans = input('Your answer: ').strip()
    return ans


def main():
    all_questions = load_questions_db()
    print('Welcome to multiplayer Jeopardy!')
    
    board = build_board(all_questions)
    
    # Ask for number of players
    num_players = 0
    while num_players < 1:
        try:
            num_players = int(input('How many players? '))
            if num_players < 1:
                print('Must have at least 1 player.')
                num_players = 0
        except ValueError:
            print('Please enter a valid number.')
    
    players = []
    for i in range(1, num_players + 1):
        name = input(f'Enter name for Player {i}: ').strip() or f'Player{i}'
        players.append({'name': name, 'score': 0})

    current = 0

    while not all_questions_asked(board):
        display_board(board)
        player = players[current]
        print(f"\n{player['name']}'s turn. Score: ${player['score']}")
        choice = input('Choose category number and difficulty ($value) (e.g. 1 100), or type quit: ').strip()
        if choice.lower() in ('quit', 'exit'):
            break
        parts = choice.split()
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            print('Invalid input. Try again.')
            continue
        cat_idx = int(parts[0]) - 1
        value = int(parts[1])
        cat, q = find_question(board, cat_idx, value)
        if q is None or q['asked']:
            print('That question is unavailable. Pick another.')
            continue

        response = ask_question(player['name'], cat, q)
        q['asked'] = True
        if check_answer(response, q['answer']):
            players[current]['score'] += q['value']
            print(f"Correct! +${q['value']}")
        else:
            players[current]['score'] -= q['value']
            print(f"Incorrect. The answer was: {format_answer(q['answer'])}. -${q['value']}")

        current = (current + 1) % len(players)

    print('\nGame over. Final scores:')
    for p in players:
        print(f"- {p['name']}: ${p['score']}")
    max_score = max(p['score'] for p in players)
    winners = [p['name'] for p in players if p['score'] == max_score]
    if len(winners) == 1:
        print(f"Winner: {winners[0]} 🎉")
    else:
        print('Tie between: ' + ', '.join(winners))


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nExiting. Goodbye!')
        sys.exit(0)
