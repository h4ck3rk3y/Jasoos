from flask import Flask, request, jsonify
from flask import render_template, send_from_directory, make_response

from util import clean_dict
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


# :param url the url of the git repository
# :return A report object
def analyze_url(url):
	job = get_current_job()
	analyzer = StaticAnalyzer(url, job)
	analyzer.analyze()

	return analyzer.complete_report


# A function to serve basic webpages
@app.route('/')
@app.route('/result/<queue_id>')
@app.route('/wait')
@app.route('/about')
def basic_pages(**kwargs):
	return make_response(open('templates/index.html').read())

# API end that takes in the GitHub url for processing
@app.route("/api/analyzer/", methods=["POST"])
def analyzer_api():
	request_data = request.get_json(silent=True)
	if 'url' in request_data:
		url = request_data['url']
		q = random.choice(queues)
		job = q.enqueue_call(func = 'app.analyze_url', args=(url,), result_ttl=5000, ttl=10000, timeout=10000)
		data = {}
		data['status'] = 'processing'
		job.meta['current_file'] = 'still cloning'
		job.save()
		data['id'] = job.get_id()
		clean_dict(data)
		return jsonify(**data)
	else:
		data = {'status': 'error'}
		clean_dict(data)
		return jsonify(**data)

@app.route('/favicon.ico')
def favicon():
	return send_from_directory('static/img', 'favicon.ico')

# API end to query the status of the analysis
@app.route('/api/result/<queue_id>', methods=["GET"])
def result(queue_id):
	job = Job.fetch(queue_id, connection=Redis())

	data = {}
	if job.is_finished:
		data['report'] = job.result
		data['status'] = 'success'
		clean_dict(data)
		return jsonify(**data)
	else:
		data['current_file'] = job.meta['current_file']
		data['status'] = 'processing'
		if job.meta.get('error', False):
			data['status'] = 'error'
			data['error'] = job.meta['error']
		clean_dict(data)
		return jsonify(**data)


@app.errorhandler(404)
def not_found(e):
	return render_template('404.html'), 404

if __name__ == "__main__":
        app.debug = True
        app.run()