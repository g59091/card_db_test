from flask import Flask, redirect, render_template, url_for, request

app = Flask(__name__)

@app.route('/')
def welcome():
    return "Hello! Let us learn about importance of testing!"

@app.route('/success/<name>')
def success(name):
    #return 'welcome %s' % name
    return f'Welcome {name}'

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = request.form['nm']
        return redirect(url_for('success', name=user))
    else:
      return render_template('test.html')

# Start with flask web app, with debug as True,# only if this is the starting page
if __name__ == '__main__':
    app.run(debug=True)