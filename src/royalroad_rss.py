
from flask import Blueprint, render_template, request, send_file, url_for
blueprint = Blueprint('royalroad_rss', __name__)


from html_to_epub.RR_rss import load_datafile, getOldestNew, getChapters
from src.sendToKindle import main as sendToKindle

from .mongodb import mongodb_api

@blueprint.route('/RR_rss/<id>')
def RR_rss(id):

    # new, epub_file = load_datafile('./books/IR.yaml')
    db_api = mongodb_api.from_json("data/mongodb.json")
    data = db_api.findOne({'id': id})['document']
    if not data:
        return f"Unknown id {id}"
    from datetime import datetime
    from dateutil import parser as date_parser
    # https://www.royalroad.com/fiction/syndication/36299
    url = data.get('rss');
    lastTime = data.get('lastTime')
    if lastTime:
        lastTime = date_parser.parse(lastTime)

    oldestNew = getOldestNew(url, lastTime)
    if not oldestNew:
        return "No Updates!"

    epub_filename = f"/tmp/{id}-%date.epub"
    nowTime = datetime.now().isoformat(timespec='seconds') + '+0000'

    db_api.updateOne({'id': id}, {'$set': {"lastTime": nowTime}})


    data['epub_filename'] = epub_filename
    data['css_filename'] = "webbook_dl/kindle.css"

    epub_file = getChapters(oldestNew['link'], 
                          { 'cache': f'/tmp/{id}', 
                            'callbacks': 'webbook_dl.html_to_epub.callbacks.Callbacks',
                            'book': data });

    db_info = {
        "dataSource" : "NokoCluster",
        "database"   : "html_to_epub",
        "collection" : "rss-state"
    }

    rss_state_db_api = mongodb_api.from_json("data/mongodb.json", db_info)
    # with open("out/latest.txt", "w") as f:
    #     f.write(epub_file)
    rss_state_db_api.updateOne({'id': "latest"}, {'id': "latest", 'filepath': epub_file}, upsert=True);

    sendToKindle(epub_file)

    return f"""
    <html> <p>A new update was sent to the kindle <p>
    <a href="/{url_for('royalroad_rss.dl_latest_epub')}" target="blank"><button class='btn btn-default'>Download!</button></a>
    """

@blueprint.route('/dl-latest-epub')
def dl_latest_epub():
    db_info = {
        "dataSource" : "NokoCluster",
        "database"   : "html_to_epub",
        "collection" : "rss-state"
    }

    rss_state_db_api = mongodb_api.from_json("data/mongodb.json", db_info)
    data = rss_state_db_api.findOne({'id': "latest"})['document']

    epub_file = data['filepath']

    # with open("out/latest.txt", "r") as f:
    #     epub_file = f.read()
    # # epub_file = 'out/IR-2023-01-24.epub'
    # print(epub_file)

    return send_file(epub_file)

