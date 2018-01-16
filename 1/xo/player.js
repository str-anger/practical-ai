var express = require('express');
var app = express();
var bodyParser = require('body-parser');
var path = require('path');
app.use(bodyParser.text({type: '*/*'})); // for raw contents

var CODES = { OK : 200, UNAUTH : 401, FORBIDDEN : 403, TEAPOT : 418, BADREQ : 400, NOTFOUND : 404 };

var rooms = [];

var log = console.log;

function _throw(text, code) {
	var v = Error(text);
	v.code = code;
	throw v;
}

function auth(req) {
	var tok = req.headers["Authorization"] || req.headers["authorization"];
	if (!tok) 						_throw("No authentication token provided", CODES.UNAUTH);
	var parts = tok.split(' ');
	if (parts.length != 2)			_throw("Invalid auth format", CODES.UNAUTH);
	if (parts[0] != "Bearer") 		_throw("Wrong auth type. 'Bearer' expected, but found: " + parts[0], CODES.UNAUTH);
	if (parts[1] != "dummy_token")	_throw("Wrong token provided", CODES.FORBIDDEN);
}

function get_empty_field() { return "...\n...\n..."; }

function get_stats(field) {
	var lines = field.split('\n');
	var stats = [];
	stats['x'] = stats['o'] = stats['.'] = 0;
	for (var x in lines) {
		line = lines[x];
		if (line.length != 3) return false;
		for (var i = 0; i < 3; i++) {
			if (!stats[line[i]]) stats[line[i]] = 1;
			else stats[line[i]]++;
		}
	}
	return stats;
}

function is_valid_field(field) {
	var lines = field.split('\n');
	if (lines.length != 3) return false;
	var stats = get_stats(field);
	if ((stats['x'] + stats['o'] + stats['.']) != 9) return false;
	if ((stats['x'] - stats['o']) != 0 && (stats['x'] - stats['o'] != 1)) return false;
	return true;
}

function is_subfield(child, parent) {
	var diffs = 0;
	for (var i = 0; i < child.length; i++) {
		if (child[i] != parent[i] && parent[i] != '.') return false;
		if (child[i] != parent[i] && parent[i] == '.') diffs++;
	}
	return diffs == 1;
}

function i_won(field, i) {
	var wins = [[0, 4, 8], [1, 5, 9], [2, 6, 10], [0, 1, 2], [4, 5, 6], [8, 9, 10], [0, 5, 10], [2, 5, 8]];
	for (var wi in wins) {
		var win = wins[wi];
		if (field[win[0]] == i && field[win[1]] == i && field[win[2]] == i) return true;
	}
	return false;
}

function move(field) {
	var i = 0;
	var stats = get_stats(field);
	var me = stats['x'] > stats['o'] ? 'o' : 'x';
	while (i < field.length) {
		if (field[i] == '.') {
			var nf = field.substr(0, i) + me + field.substr(i+1);
			if (i_won(nf, me)) _throw("I won\n" + nf, CODES.TEAPOT);
			return nf;
		}
		i++;
	}
	_throw("I can't move", CODES.TEAPOT);
}

function validate_move(history, field) {
	var empty = get_empty_field();
	// first move is empty field - player passes the move server
	if (field == empty && history.length == 0) {
		return;
	// player moves first
	} else if (is_subfield(field, empty) && history.length == 0) {
		return;
	} else if (history.length == 0) {
		_throw("You started not from the beginning!", CODES.BADREQ);
	}
	// otherwise - move should be subfield of last move in history
	var prev = history[history.length - 1];
	if (is_subfield(field, prev)) {
		return;
	} else {
		_throw("Don't try to fool me! Last field is\n" + prev, CODES.BADREQ);
	}
}

function play(room, field) {
	// special case: empty move is equivalent to passing the move
	if (!field && !rooms[room]) field = get_empty_field();
	// field itself is valid
	if (!is_valid_field(field)) {
		_throw("Field is invalid", CODES.BADREQ);
	}
	// if no moves done yet - initialize history
	if (!rooms[room]) rooms[room] = [];
	validate_move(rooms[room], field);
	rooms[room].push(field);	
	var stats = get_stats(field);
	var enemy = stats['x'] > stats['o'] ? 'x' : 'o';
	if (i_won(field, enemy)) {
		_throw("You won. Congrats!", CODES.TEAPOT);
	}
	var answer = move(field);
	rooms[room].push(answer);
	return answer;
}
	
app.post("/api/v1/:room", (req, res) => {
	try {
	    auth(req);
		var room = req.params.room;
		var field = req.body;
	    res.send(play(room, field));
	} catch (e) {
		// game is over!
		if (e.code == CODES.TEAPOT) delete rooms[room];		
	    res.status(e.code).send(e.message);
	}
});

app.get("/", (req, res) => {
	res.status(CODES.NOTFOUND).send("I don't know this url");
});


app.get("*", (req, res) => {
	res.status(CODES.OK).send("I'm dummy XO bot");
});

function start(hostname, port) {
    try {
        var hn = hostname || "0.0.0.0";
        var p = port || 80;
        app.listen(p, hn, () => {
	    console.log("started ok @" + p);
        });
    } catch(e) {
        console.log('Error starting application: ' + e.message);
    }
}

start(null, parseInt(process.argv[2]));