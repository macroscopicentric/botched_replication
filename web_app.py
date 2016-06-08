from flask import Flask, render_template, Markup,jsonify
import csv

app = Flask(__name__)

@app.route('/')
def index():
	with open('modified_library_of_babel.html', 'r') as f:
		current_text = f.read()
	return render_template('index.html', modified_text=Markup(current_text))

@app.route('/newest_change')
def fetch_newest_change():
	with open('modified_library_of_babel_changes.csv', 'r') as f:
		csvreader = csv.reader(f)
		rows = []
		for row in csvreader:
			rows.append(row)

	if len(rows) > 0:
		newest_change = rows[-1]
	else:
		newest_change = ''

	return jsonify(newest_change)

if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run(debug=True)
