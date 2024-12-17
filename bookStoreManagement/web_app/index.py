from web_app import app
from flask import render_template


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    from admin import admin
    app.run(debug=True, port=2357)
