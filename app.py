from flask import Flask, request, jsonify
from flask import render_template, send_from_directory, make_response
import time

from analyzer import StaticAnalyzer

from rq import Queue
from rq.job import Job
from rq import get_current_job
from redis import Redis

import random

NUMER_OF_QUEUES = 8

queues = [Queue(str(i), connection=Redis()) for i in range(8)]

app = Flask(__name__)
app.url_map.strict_slashes = False

def analyze_url(url):
	job = get_current_job()
	analyzer = StaticAnalyzer(url, job)
	analyzer.analyze()

	return analyzer.complete_report


@app.route('/')
@app.route('/result/<queue_id>')
@app.route('/wait')
def basic_pages(**kwargs):
	return make_response(open('templates/index.html').read())

@app.route("/api/analyzer/", methods=["POST"])
def analyzer_api():
	request_data = request.get_json(silent=True)
	if 'url' in request_data:
		url = request_data['url']
		q = random.choice(queues)
		job = q.enqueue_call(func = 'app.analyze_url', args=(url,), result_ttl=5000)
		data = {}
		data['status'] = 'processing'
		data['id'] = job.get_id()
		return jsonify(**data)
	else:
		data = {'status': 'error'}
		return jsonify(**data)

@app.route('/favicon.ico')
def favicon():
	return send_from_directory('static/img', 'favicon.ico')

@app.route('/api/result/<queue_id>', methods=["GET"])
def result(queue_id):
	job = Job.fetch(queue_id, connection=Redis())

	data = {}
	if job.is_finished:
		data['report'] = job.result
		data['status'] = 'success'
		return jsonify(**data)
	else:
		if job.meta.get('current_file', False):
			data['current_file'] = job.meta['current_file']
		data['status'] = 'processing'
		return jsonify(**data)


@app.errorhandler(404)
def not_found(e):
	return render_template('404.html'), 404

if __name__ == "__main__":
        app.debug = True
        app.run()