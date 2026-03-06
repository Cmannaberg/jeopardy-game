#!/usr/bin/env python3
"""
Simple terminal Jeopardy-style game.

Usage: run this script and follow prompts. Select questions by category number and value.
"""
import sys
import textwrap
import string


def normalize(s):
	s = s.strip().lower()
	# remove punctuation
	return s.translate(str.maketrans('', '', string.punctuation))


BOARD = {
	"History": {
		100: {"q": "Who was the first President of the United States?", "a": ["george washington", "washington"]},
		200: {"q": "In which year did World War II end?", "a": ["1945"]},
		300: {"q": "The ancient city of Rome was founded on which river?", "a": ["tiber"]},
		400: {"q": "Which empire was ruled by Genghis Khan?", "a": ["mongol empire", "mongols"]},
		500: {"q": "The Magna Carta was signed in which country?", "a": ["england"]},
	},
	"Science": {
		100: {"q": "What is the chemical symbol for water?", "a": ["h2o"]},
		200: {"q": "What force keeps us on the ground?", "a": ["gravity"]},
		300: {"q": "What planet is known as the Red Planet?", "a": ["mars"]},
		400: {"q": "What gas do plants absorb from the atmosphere?", "a": ["carbon dioxide", "co2"]},
		500: {"q": "What is the powerhouse of the cell?", "a": ["mitochondria", "mitochondrion"]},
	},
	"Literature": {
		100: {"q": "Who wrote 'Romeo and Juliet'?", "a": ["william shakespeare", "shakespeare"]},
		200: {"q": "'1984' is a novel by which author?", "a": ["george orwell", "orwell"]},
		300: {"q": "Which epic poem tells the story of Odysseus?", "a": ["odyssey", "the odyssey"]},
		400: {"q": "Who is the author of 'Pride and Prejudice'?", "a": ["jane austen", "austen"]},
		500: {"q": "In Arthurian legend, who pulls the sword from the stone?", "a": ["king arthur", "arthur"]},
	},
}


def print_board(board, asked):
	categories = list(board.keys())
	print('\nBoard:')
	for idx, cat in enumerate(categories, 1):
		print(f"{idx}. {cat}")
		values = []
		for v in sorted(board[cat].keys()):
			values.append(str(v) if (cat, v) not in asked else "---")
		print("   ", "  ".join(values))


def all_answered(board, asked):
	total = sum(len(vals) for vals in board.values())
	return len(asked) >= total


def main():
	asked = set()
	score = 0
	categories = list(BOARD.keys())

	print("Welcome to Jeopardy! (type 'quit' to exit)\n")

	while True:
		if all_answered(BOARD, asked):
			print(f"All questions answered. Final score: {score}")
			break

		print_board(BOARD, asked)

		choice = input("Pick a question by category number and value (e.g. '1 200'): ").strip()
		if not choice:
			continue
		if choice.lower() in ("quit", "q", "exit"):
			print(f"Goodbye. Final score: {score}")
			break

		parts = choice.split()
		if len(parts) != 2:
			print("Invalid input. Use format: <category-number> <value> (e.g. 2 300)")
			continue

		try:
			cat_idx = int(parts[0]) - 1
			val = int(parts[1])
			category = categories[cat_idx]
		except Exception:
			print("Invalid category number or value.")
			continue

		if category not in BOARD or val not in BOARD[category]:
			print("No such question.")
			continue

		if (category, val) in asked:
			print("That question has already been taken.")
			continue

		q = BOARD[category][val]["q"]
		answers = BOARD[category][val]["a"]

		print('\n' + textwrap.fill(q, width=70))
		user_ans = input("Your answer: ").strip()
		if user_ans.lower() in ("quit", "exit"):
			print(f"Goodbye. Final score: {score}")
			break

		asked.add((category, val))

		if normalize(user_ans) in [normalize(a) for a in answers]:
			score += val
			print(f"Correct! +{val} points. Total: {score}\n")
		else:
			score -= val
			print(f"Incorrect. The accepted answer(s): {', '.join(answers)}. -{val} points. Total: {score}\n")

	return 0


if __name__ == '__main__':
	sys.exit(main())

