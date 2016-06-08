from flask import Flask, render_template, Markup

app = Flask(__name__)

@app.route('/')
def index():
	with open('modified_library_of_babel.html', 'r') as f:
		current_text = f.read()
	return render_template('index.html', modified_text=Markup(current_text))

if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run(debug=True)
