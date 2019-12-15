from flask import Flask, render_template, Markup,jsonify
from botched_replication import Corpus

import redis
import os

app = Flask(__name__)

r = redis.Redis()
# r = redis.from_url(os.environ.get('REDIS_URL'))
text = Corpus(r, 'library_of_babel.html')

@app.route('/')
def index():
	current_text = text.fetch_current_text()
	return render_template('index.html', modified_text=Markup(current_text))

@app.route('/newest_change')
def fetch_newest_change():
	newest_change = text.fetch_newest_change()
	return jsonify(newest_change)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    # app.run(debug=True)
