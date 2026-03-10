from flask import Flask, session, redirect, url_for, render_template, request, send_from_directory
import os, json, random
from PIL import Image

# helper to manage thumbnails
def ensure_thumbnail(filename):
    photos_dir = os.path.join(os.path.dirname(__file__), 'photos')
    thumbs_dir = os.path.join(os.path.dirname(__file__), 'thumbnails')
    os.makedirs(thumbs_dir, exist_ok=True)
    orig_path = os.path.join(photos_dir, filename)
    thumb_path = os.path.join(thumbs_dir, filename)
    if not os.path.exists(thumb_path) and os.path.exists(orig_path):
        try:
            img = Image.open(orig_path)
            img.thumbnail((200, 200))
            img.save(thumb_path)
        except Exception:
            pass
    return thumb_path


app = Flask(__name__)
app.secret_key = os.urandom(24)


def load_questions_db():
    db_path = os.path.join(os.path.dirname(__file__), 'questions_db.json')
    try:
        with open(db_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Could not load questions: {e}")


def build_board(all_questions):
    difficulty_to_value = {1: 100, 2: 200, 3: 300, 4: 400, 5: 500}
    board = {}
    for category, questions in all_questions.items():
        board[category] = []
        for q in questions:
            value = difficulty_to_value.get(q.get('difficulty', 1), 100)
            # if this is a photo clue, derive answer from filename and prepare thumbnail
            photo = q.get('photo')
            answer = q.get('answer', '')
            if photo:
                # use filename (without extension) as the answer
                answer = os.path.splitext(photo)[0]
                # ensure a thumbnail exists
                ensure_thumbnail(photo)
            entry = {
                'clue': q['clue'],
                'answer': answer,
                'value': value,
                'difficulty': q.get('difficulty', 1),
                'asked': False,
                'final': category == 'Final Jeopardy'
            }
            if photo:
                entry['photo'] = photo
            board[category].append(entry)
        board[category].sort(key=lambda x: x['value'])
        if category != 'Final Jeopardy' and board[category]:
            idx = random.randint(0, len(board[category]) - 1)
            board[category][idx]['daily_double'] = True
    return board


def normalize(s):
    return ''.join(ch for ch in s.lower() if ch.isalnum())


def check_answer(response, correct_answer):
    if isinstance(correct_answer, list):
        answers = correct_answer
    else:
        answers = [ans.strip() for ans in correct_answer.split(',')]
    return any(normalize(response) == normalize(ans) for ans in answers)


def all_regular_done(board):
    for cat, qs in board.items():
        if cat == 'Final Jeopardy':
            continue
        for q in qs:
            if not q['asked']:
                return False
    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    all_questions = load_questions_db()
    themes = list(all_questions.keys())
    if request.method == 'POST':
        theme = request.form.get('theme')
        if theme in all_questions:
            session['theme'] = theme
            return redirect(url_for('playersetup'))
    return render_template('setup.html', themes=themes)

@app.route('/playersetup', methods=['GET', 'POST'])
def playersetup():
    theme = session.get('theme')
    if not theme:
        return redirect(url_for('index'))
    all_questions = load_questions_db()
    if theme not in all_questions:
        session.pop('theme', None)
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            num = int(request.form['num_players'])
        except ValueError:
            num = 0
        names = []
        for i in range(num):
            name = request.form.get(f'name{i}')
            names.append(name or f'Player{i+1}')
        max_rounds = 0
        try:
            max_rounds = int(request.form.get('rounds', 0))
        except ValueError:
            max_rounds = 0
        
        theme_questions = all_questions.get(theme, {})
        if not theme_questions:
            return render_template('playersetup.html', theme=theme, error='No questions were found for this theme. Please go back and choose another theme.')
        session['board'] = build_board(theme_questions)
        session['players'] = [{'name': n, 'score': 0} for n in names]
        session['current'] = 0
        session['max_rounds'] = max_rounds
        session['rounds_played'] = 0
        session['total_questions'] = sum(len(qs) for cat, qs in session['board'].items() if cat != 'Final Jeopardy')
        return redirect(url_for('board'))
    return render_template('playersetup.html', theme=theme)

@app.route('/board')
def board():
    if 'board' not in session:
        return redirect(url_for('index'))
    
    board_state = session['board']
    if session['max_rounds'] > 0 and session['rounds_played'] >= session['max_rounds']:
        return redirect(url_for('final'))
    if all_regular_done(board_state):
        return redirect(url_for('final'))
    
    return render_template(
        'board.html',
        board=board_state,
        players=session['players'],
        current=session['current'],
        rounds_played=session['rounds_played'],
        max_rounds=session['max_rounds'],
        total_questions=session['total_questions'],
    )

@app.route('/question/<category>/<int:idx>', methods=['GET', 'POST'])
def question(category, idx):
    board = session['board']
    if category not in board or idx < 0 or idx >= len(board[category]):
        return redirect(url_for('board'))
    q = board[category][idx]
    if q['asked']:
        return redirect(url_for('board'))
    players = session['players']
    current = session['current']

    if request.method == 'POST':
        wager_input = request.form.get('wager', '')
        answer = request.form.get('answer', '')
        try:
            wager = int(wager_input)
        except ValueError:
            wager = q['value']
        score = players[current]['score']
        if q.get('daily_double') and score >= 100:
            wager = max(0, min(wager, score))
        else:
            wager = q['value']
        
        correct = check_answer(answer, q['answer'])
        if correct:
            players[current]['score'] += wager
        else:
            players[current]['score'] -= wager
        
        q['asked'] = True
        session['board'] = board
        session['players'] = players
        session['current'] = (current + 1) % len(players)
        session['rounds_played'] = session.get('rounds_played', 0) + 1
        
        # Format answer display
        if isinstance(q['answer'], list):
            correct_ans = ' / '.join(q['answer'])
        else:
            correct_ans = q['answer']
        
        photo = q.get('photo')
        return render_template('feedback.html', correct=correct, wager=wager, correct_answer=correct_ans, photo=photo)

    daily = q.get('daily_double') and players[current]['score'] >= 100
    return render_template('question.html', question=q, category=category, idx=idx, daily=daily, current_player=players[current])

@app.route('/final', methods=['GET', 'POST'])
def final():
    board = session['board']
    final_q = board.get('Final Jeopardy', [None])[0]
    if not final_q:
        return redirect(url_for('board'))
    players = session['players']
    if request.method == 'POST':
        results = []
        for i, p in enumerate(players):
            ans = request.form.get(f'answer{i}', '')
            try:
                wager = int(request.form.get(f'wager{i}', '0'))
            except ValueError:
                wager = 0
            max_wager = abs(p['score'])
            wager = max(0, min(wager, max_wager))
            correct = check_answer(ans, final_q['answer'])
            results.append((p, wager, correct))
            if correct:
                p['score'] += wager
            else:
                p['score'] -= wager
        
        # Format answer display
        if isinstance(final_q['answer'], list):
            correct_ans = ' / '.join(final_q['answer'])
        else:
            correct_ans = final_q['answer']
        
        session['players'] = players
        session['final_results'] = results
        session['final_correct_answer'] = correct_ans
        return redirect(url_for('finalfeedback'))
    
    return render_template('final.html', final_q=final_q, players=players)

@app.route('/finalfeedback')
def finalfeedback():
    results = session.get('final_results', [])
    correct_ans = session.get('final_correct_answer', '')
    return render_template('finalfeedback.html', results=results, correct_answer=correct_ans)


@app.route('/gameover')
def gameover():
    return render_template('gameover.html', players=session['players'])

@app.route('/editor')
def editor():
    return render_template('editor.html')

@app.route('/api/questions', methods=['GET', 'POST'])
def api_questions():
    if request.method == 'POST':
        try:
            new_db = request.get_json()
            # basic validation: ensure it's a dict
            if not isinstance(new_db, dict):
                return {'error': 'Invalid JSON structure'}, 400
            # save to file
            save_path = os.path.join(os.path.dirname(__file__), 'questions_db.json')
            with open(save_path, 'w') as f:
                json.dump(new_db, f, indent=2, ensure_ascii=False)
            return {'status': 'saved'}
        except Exception as e:
            return {'error': str(e)}, 500
    else:
        # GET: return current db
        try:
            db = load_questions_db()
            return db
        except Exception as e:
            return {'error': str(e)}, 500

# serve photos directory so images can be embedded
@app.route('/photos/<path:filename>')
def photo(filename):
    photos_dir = os.path.join(os.path.dirname(__file__), 'photos')
    return send_from_directory(photos_dir, filename)

@app.route('/thumbnails/<path:filename>')
def thumbnail(filename):
    thumbs_dir = os.path.join(os.path.dirname(__file__), 'thumbnails')
    return send_from_directory(thumbs_dir, filename)

@app.route('/quitgame')
def quitgame():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
