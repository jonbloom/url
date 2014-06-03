import sqlite3
from flask import Flask, request, redirect, render_template, g
from datetime import time
import base62 as b62

# configuration
DATABASE = '/var/www/url/url.sqlite'
DEBUG = True
SECRET_KEY = 'secret'
USERNAME = 'jonbloom'
PASSWORD = 'password'
app = Flask(__name__)
app.config.from_object(__name__)

#errors
not_exist = "The link you followed was either incorrect or mistyped. Please try again."

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
	g.db = connect_db()
	g.db.row_factory = sqlite3.Row
@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

@app.route("/", methods=["GET","POST"])
def index():
	if request.method == "GET":
		return render_template('index.html')
	else:
		long_url = request.form['url']
		short_url = request.url_root + get_short_link(long_url)
		return render_template('index.html', short_url=short_url,long_url=long_url)

@app.route('/<id>')
def forward(id):
	db_check = check_id(b62.decode(id))
	if db_check is None:
		return render_template('index.html',error=not_exist), 404
	else:
		g.db.cursor().execute('update urls set hits = hits + 1 where id = ?',[id])
		return redirect(db_check[0])

@app.route('/<id>/+')
def stats(id):
	if check_id(id) is not None:
		db_query = g.db.cursor().execute('select url,hits from urls where id = ?',[id]).fetchone()
		short_url = request.url_root + id
		long_url = db_query[0]
		hits = db_query[1]
		return render_template('index.html',short_url=short_url,long_url=long_url,hits=hits)

def check_id(id):
	return g.db.cursor().execute('select url from urls where id = ?',[id]).fetchone()

def check_url(url):
	return g.db.cursor().execute('select id from urls where url = ?',[url]).fetchone()

def get_short_link(url):
	if check_url(url) is None:
		g.db.cursor().execute('insert into urls values(null,?,0);',[url])
		id = check_url(url)[0]
		return b62.encode(id)
	else:
		id = g.db.cursor().execute('select id from urls where url = ?',[url]).fetchone()[0]
		return b62.encode(int(id))



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)