from web_app import app


@app.route('/')
def index():
    return 'Hello'


if __name__ == '__main__':
    from admin import admin
    app.run(debug=True, port=2357)
