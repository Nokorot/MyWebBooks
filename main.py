from flask import Flask, jsonify, send_file
import os, sys

sys.path.insert(0, './html_to_epub')

from html_to_epub.RR_rss import load_datafile

from sendToKindle import main as sendToKindle

app = Flask(__name__)

if not os.path.exists('./out'):
    os.makedirs("./out")


@app.route('/RR_rss')
def RR_rss():
    new, epub_file = load_datafile('./books/IR.yaml')
    if not new:
        return "No updates!"

    # epub_file = 'out/IR-2023-01-24.epub'
    with open("out/latest.txt", "w") as f:
        f.write(epub_file)

    sendToKindle(epub_file)

    return """
    <html> <p>A new update was sent to the kindle <p>
    <a href="/dl-latest-epub" target="blank"><button class='btn btn-default'>Download!</button></a>
    """
    

    # return jsonify({"new": new, "data": data})
    # return send_file(epub_file, as_attachment=True, attachment_filename=epub_file)

@app.route('/dl-latest-epub')
def dl_latest_epub():
    with open("out/latest.txt", "r") as f:
        epub_file = f.read()
    # epub_file = 'out/IR-2023-01-24.epub'

    return send_file(epub_file, as_attachment=True, attachment_filename=epub_file)


@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
