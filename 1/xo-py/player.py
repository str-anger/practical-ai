import sys
from flask import Flask
from flask import request
from flask import Response
app = Flask(__name__)

CODES = { "OK" : 200, "UNAUTH" : 401, "FORBIDDEN" : 403, "TEAPOT" : 418, "BADREQ" : 400, "NOTFOUND" : 404 }

rooms = {}

log = print

def _throw(text, code):
    raise Exception(text, code)

def auth(request):
    tok = request.headers.get("Authorization") or request.headers.get("authorization")
    if not tok:
        _throw("No authentication token provided", CODES["UNAUTH"])
    parts = tok.split(' ')
    if len(parts) != 2:
        _throw("Invalid auth format", CODES["UNAUTH"])
    if parts[0] != "Bearer":
        _throw("Wrong auth type. 'Bearer' expected, but found: " + parts[0], CODES["UNAUTH"])
    if parts[1] != "dummy_token":
        _throw("Wrong token provided", CODES["FORBIDDEN"])

def get_empty_field():
    return "...\n...\n..."

def get_stats(field):
    lines = field.split('\n')
    stats = {}
    stats['x'] = stats['o'] = stats['.'] = 0
    for line in lines:
        if len(line) != 3:
            return False
        for i in range(3):
            if not stats[line[i]]:
                stats[line[i]] = 1
            else:
                stats[line[i]] += 1
    return stats

def is_valid_field(field):
    lines = field.split('\n')
    if len(lines) != 3:
        return False
    stats = get_stats(field)
    if (stats['x'] + stats['o'] + stats['.']) != 9:
        return False
    if (stats['x'] - stats['o']) != 0 and (stats['x'] - stats['o'] != 1):
        return False
    return True

def is_subfield(child, parent):
    diffs = 0
    for i in range(len(child)):
        if child[i] != parent[i] and parent[i] != '.':
            return False
        if child[i] != parent[i] and parent[i] == '.':
            diffs += 1
    return diffs == 1

def i_won(field, i):
    wins = [[0, 4, 8], [1, 5, 9], [2, 6, 10], [0, 1, 2], [4, 5, 6], [8, 9, 10], [0, 5, 10], [2, 5, 8]]
    for win in wins:
        if field[win[0]] == i and field[win[1]] == i and field[win[2]] == i:
            return True
    return False

def move(field):
    i = 0
    stats = get_stats(field)
    me = 'o' if stats['x'] > stats['o'] else 'x'
    while i < len(field):
        if field[i] == '.':
            nf = field[0:i] + me + field[i+1:]
            if i_won(nf, me):
                _throw("I won\n" + nf, CODES["TEAPOT"])
            return nf
        i += 1
    _throw("I can't move", CODES["TEAPOT"])

def validate_move(history, field):
    empty = get_empty_field()
    # first move is empty field - player passes the move server
    if field == empty and len(history) == 0:
        return
    # player moves first
    elif is_subfield(field, empty) and len(history) == 0:
        return
    elif len(history) == 0:
        _throw("You started not from the beginning!", CODES["BADREQ"])

    # otherwise - move should be subfield of last move in history
    prev = history[len(history) - 1]
    if is_subfield(field, prev):
        return
    else:
        _throw("Don't try to fool me! Last field is\n" + prev, CODES["BADREQ"])

def play(room, field):
    # special case: empty move is equivalent to passing the move
    if not field and not room in rooms:
        field = get_empty_field()
    # field itself is valid
    if not is_valid_field(field):
        _throw("Field is invalid", CODES["BADREQ"])

    # if no moves done yet - initialize history
    if not room in rooms:
        rooms[room] = []
    validate_move(rooms[room], field)
    rooms[room].append(field);
    stats = get_stats(field)
    enemy = 'x' if stats['x'] > stats['o'] else 'o'
    if i_won(field, enemy):
        _throw("You won. Congrats!", CODES["TEAPOT"])

    answer = move(field)
    rooms[room].append(answer)
    return answer

@app.route('/api/v1/<room>', methods=['POST'])
def api_v1_room(room):
    try:
        auth(request)
        field = request.get_data().decode()
        return play(room, field)
    except Exception as e:
        # game is over!
        if len(e.args) > 1 and e.args[1] == CODES["TEAPOT"]:
            del rooms[room]
        
        return Response(str(e), status=e.args[1] if len(e.args) > 1 else None)

@app.route('/')
def api_root():
    return Response("I don't know this url", status=CODES["NOTFOUND"])

@app.route('/<path:path>')
def catch_all(path):
    return Response("I'm dummy XO bot", status=CODES["OK"])

def start(hostname, port):
    try:
        hn = hostname or "0.0.0.0"
        p = port or 80
        app.run(host=hn, port=p)
        print("started ok @" + p)
    except Exception as e:
        print('Error starting application: ' + str(e))

if __name__ == '__main__':
    start(None, sys.argv[1] if len(sys.argv) > 1 else None)
