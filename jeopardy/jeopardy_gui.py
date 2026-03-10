#!/usr/bin/env python3
"""Simple GUI Jeopardy game using tkinter.

Run: python3 jeopardy_gui.py
"""
import sys
import json
import os
import tkinter as tk
from tkinter import simpledialog, messagebox
import random


def load_questions_db():
    """Load questions from the separate database file."""
    db_path = os.path.join(os.path.dirname(__file__), 'questions_db.json')
    try:
        with open(db_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        messagebox.showerror('Error', f'Could not load questions from {db_path}')
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
                'asked': False,
                'final': category == 'Final Jeopardy'
            })
        board[category].sort(key=lambda x: x['value'])
        # Mark one random question as daily double (except final)
        if category != 'Final Jeopardy' and board[category]:
            idx = random.randint(0, len(board[category]) - 1)
            board[category][idx]['daily_double'] = True
    return board


def normalize(s):
    return ''.join(ch for ch in s.lower() if ch.isalnum())


def check_answer(response, correct_answer):
    """Check if response matches correct answer(s)."""
    if isinstance(correct_answer, list):
        answers = correct_answer
    else:
        answers = [ans.strip() for ans in correct_answer.split(',')]
    return any(normalize(response) == normalize(ans) for ans in answers)


class JeopardyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Jeopardy!')
        self.all_questions = load_questions_db()
        self.board = build_board(self.all_questions)
        self.players = []
        self.current = 0
        self.total_questions = sum(len(questions) for cat, questions in self.board.items() if cat != 'Final Jeopardy')

        self.ask_players()
        self.ask_rounds()
        self.create_widgets()
        self.update_scoreboard()

    def ask_players(self):
        num = 0
        while num < 1:
            num = simpledialog.askinteger('Players', 'How many players?', parent=self.root)
            if num is None:
                sys.exit(0)
            if num < 1:
                messagebox.showwarning('Warning', 'Must have at least 1 player.')
                num = 0
        for i in range(1, num + 1):
            name = simpledialog.askstring('Player Name', f'Enter name for Player {i}', parent=self.root)
            if not name:
                name = f'Player{i}'
            self.players.append({'name': name, 'score': 0})

    def ask_rounds(self):
        while True:
            self.max_rounds = simpledialog.askinteger('Rounds', 'How many rounds (questions) to play? (0 for all)', parent=self.root)
            if self.max_rounds is None:
                self.max_rounds = 0
                break
            if self.max_rounds >= 0:
                break
            messagebox.showwarning('Invalid Input', 'Please enter 0 or a positive number.')
        self.rounds_played = 0

    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(side='top', fill='x')

        self.score_frame = tk.Frame(top_frame)
        self.score_frame.pack(side='left', padx=10, pady=10)

        self.board_frame = tk.Frame(top_frame)
        self.board_frame.pack(side='right', padx=10, pady=10)

        self.question_buttons = {}

        # categories row
        cats = [cat for cat in self.board.keys() if cat != 'Final Jeopardy']
        for col, cat in enumerate(cats):
            lbl = tk.Label(self.board_frame, text=cat, bg='blue', fg='white', width=15)
            lbl.grid(row=0, column=col, padx=2, pady=2)
            for row, q in enumerate(self.board[cat], start=1):
                btn = tk.Button(
                    self.board_frame,
                    text=str(q['value']),
                    width=15,
                    command=lambda c=cat, qi=row - 1: self.on_question_click(c, qi),
                    bg='navy',
                    fg='blue'
                )
                btn.grid(row=row, column=col, padx=2, pady=2)
                self.question_buttons[(cat, row - 1)] = btn

    def update_scoreboard(self):
        # clear previous
        for widget in self.score_frame.winfo_children():
            widget.destroy()
        tk.Label(self.score_frame, text='Scoreboard', font=('Helvetica', 14, 'bold')).pack()
        total = self.max_rounds if self.max_rounds > 0 else self.total_questions
        tk.Label(self.score_frame, text=f'Question {self.rounds_played} of {total}', font=('Helvetica', 12, 'italic')).pack()
        for idx, p in enumerate(self.players, start=1):
            txt = f"{idx}. {p['name']}: ${p['score']}"
            lbl = tk.Label(self.score_frame, text=txt, font=('Helvetica', 12))
            lbl.pack(anchor='w')
        turn = self.players[self.current]['name']
        self.turn_label = tk.Label(self.score_frame, text=f"Current: {turn}", font=('Helvetica', 12, 'italic'))
        self.turn_label.pack(anchor='w', pady=(5,0))
        # Quit button
        quit_btn = tk.Button(self.score_frame, text="Quit Game", command=self.quit_game, bg='red', fg='white')
        quit_btn.pack(pady=5)

    def on_question_click(self, category, q_index):
        q = self.board[category][q_index]
        if q['asked']:
            return
        wager = q['value']
        if q.get('daily_double') and self.players[self.current]['score'] >= 100:
            wager = simpledialog.askinteger('Daily Double!', f"{self.players[self.current]['name']}, how much do you wager? (0 to {self.players[self.current]['score']})", parent=self.root)
            if wager is None:
                wager = q['value']
            wager = max(0, min(wager, self.players[self.current]['score']))
        ans = simpledialog.askstring('Question', f"{q['clue']}\n\nYour answer:", parent=self.root)
        q['asked'] = True
        btn = self.question_buttons[(category, q_index)]
        btn.config(text='X', state='disabled', bg='gray')
        if ans and check_answer(ans, q['answer']):
            self.players[self.current]['score'] += wager
            messagebox.showinfo('Correct', f"Correct! +${wager}")
        else:
            self.players[self.current]['score'] -= wager
            correct = q['answer'] if isinstance(q['answer'], str) else ' / '.join(q['answer'])
            messagebox.showinfo('Incorrect', f"Incorrect. The answer was: {correct}. -${wager}")
        self.current = (self.current + 1) % len(self.players)
        self.rounds_played += 1
        self.update_scoreboard()
        if self.max_rounds > 0:
            if self.rounds_played >= self.max_rounds:
                self.do_final_jeopardy()
        elif self.all_regular_done():
            self.do_final_jeopardy()

    def do_final_jeopardy(self):
        final_q = None
        for cat, questions in self.board.items():
            if cat == 'Final Jeopardy':
                final_q = questions[0]
                break
        if not final_q:
            self.end_game()
            return
        final_q['asked'] = True
        # Collect wagers and answers
        results = []
        for p in self.players:
            max_wager = abs(p['score'])
            wager = simpledialog.askinteger('Final Jeopardy Wager', f"{p['name']}, how much do you wager? (0 to {max_wager})", parent=self.root)
            if wager is None:
                wager = 0
            wager = max(0, min(wager, max_wager))
            ans = simpledialog.askstring('Final Jeopardy', f"{p['name']}, the clue is: {final_q['clue']}\n\nYour answer:", parent=self.root)
            results.append((p, wager, ans))
        # Check answers and update scores
        for p, wager, ans in results:
            if ans and check_answer(ans, final_q['answer']):
                p['score'] += wager
            else:
                p['score'] -= wager
        self.update_scoreboard()
        self.end_game()

    def quit_game(self):
        if messagebox.askyesno('Quit Game', 'Are you sure you want to quit?'):
            self.end_game()

    def end_game(self):
        scores = [(p['score'], p['name']) for p in self.players]
        scores.sort(reverse=True)
        top_score = scores[0][0]
        winners = [name for score, name in scores if score == top_score]
        if len(winners) == 1:
            msg = f"Winner: {winners[0]} 🎉"
        else:
            msg = "Tie between: " + ', '.join(winners)
        messagebox.showinfo('Game Over', msg)
        self.root.quit()


if __name__ == '__main__':
    root = tk.Tk()
    try:
        app = JeopardyGUI(root)
        root.mainloop()
    except (KeyboardInterrupt, SystemExit):
        pass
