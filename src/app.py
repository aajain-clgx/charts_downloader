from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import db

app = Flask(__name__)
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'images')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

@app.route('/api/charts')
def api_charts():
    ticker = request.args.get('ticker')
    date_start = request.args.get('date_start')
    date_end = request.args.get('date_end')
    
    tags_str = request.args.get('tags')
    tags = tags_str.split(',') if tags_str else None
    
    latest_per_ticker = request.args.get('latest_per_ticker') == 'true'
    tag_operator = request.args.get('tag_operator', 'OR')
    period = request.args.get('period')
    
    charts = db.get_charts(ticker, date_start, date_end, tags, latest_per_ticker, tag_operator, period)
    return jsonify(charts)

@app.route('/api/tags', methods=['POST'])
def api_add_tag():
    data = request.json
    chart_id = data.get('chart_id')
    tag_name = data.get('tag_name')
    
    if not chart_id or not tag_name:
        return jsonify({'error': 'Missing chart_id or tag_name'}), 400
        
    db.add_tag(chart_id, tag_name)
    return jsonify({'success': True})

@app.route('/api/tags', methods=['DELETE'])
def api_remove_tag():
    data = request.json
    chart_id = data.get('chart_id')
    tag_name = data.get('tag_name')
    
    if not chart_id or not tag_name:
        return jsonify({'error': 'Missing chart_id or tag_name'}), 400
        
    db.remove_tag(chart_id, tag_name)
    return jsonify({'success': True})

@app.route('/api/tags/cloud')
def api_tags_cloud():
    tags = db.get_all_tags()
    return jsonify(tags)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
