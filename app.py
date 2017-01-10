from flask import Flask, request, jsonify
from flask import render_template, send_from_directory, make_response
import time

from analyzer import StaticAnalyzer

app = Flask(__name__)
app.url_map.strict_slashes = False

@app.route('/')
@app.route('/result')
@app.route('/wait')
def basic_pages(**kwargs):
	return make_response(open('templates/index.html').read())

@app.route("/api/analyzer/", methods=["POST"])
def analyzer_api():
	time.sleep(5)
	request_data = request.get_json(silent=True)
	if 'url' in request_data:
		url = request_data['url']
		analyzer = StaticAnalyzer(url)
		analyzer.analyze()
		data = {'status': 'success', 'url': url}
		return jsonify(**data)
	else:
		data = {'status': 'error'}
		return jsonify(**data)

@app.route('/favicon.ico')
def favicon():
	return send_from_directory('static/img', 'favicon.ico')

@app.errorhandler(404)
def not_found(e):
	return render_template('404.html'), 404

if __name__ == "__main__":
        app.debug = True
        app.run()