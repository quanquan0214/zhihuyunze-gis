from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
from TPRFService import TPRFService
import json
from typing import List, Tuple
from http import HTTPStatus

app = Flask(__name__)

RT_analyzer = TPRFService()

# 温度与降水
@app.route('/api/RT/avg', methods=['GET'])
def yearly_monthly_avg():
    # Get query parameters
    year = request.args.get('year', type=int)
    data_type = request.args.get('data_type', type=str)

    # Validate required parameters
    if year is None or data_type is None:
        return jsonify({
            'error': 'Both year and data_type parameters are required'
        }), HTTPStatus.BAD_REQUEST

    try:
        result = RT_analyzer.get_yearly_monthly_avg(year, data_type)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/api/RT/geojson', methods=['POST'])
def geojson_yearly_monthly_stats():
    # Validate request has JSON data
    if not request.is_json:
        return jsonify({
            'error': 'Request must be JSON'
        }), HTTPStatus.BAD_REQUEST

    data = request.get_json()

    # Validate required fields
    if 'geojson' not in data or 'year' not in data or 'data_type' not in data:
        return jsonify({
            'error': 'geojson, year, and data_type are required fields'
        }), HTTPStatus.BAD_REQUEST

    # Get optional stats parameter
    stats = data.get('stats', 'mean')

    try:
        result = RT_analyzer.get_geojson_yearly_monthly_stats(
            data['geojson'], data['year'], data['data_type'], stats)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/RT/code', methods=['GET'])
def code_yearly_monthly_stats():
    # Get query parameters
    code = request.args.get('code', type=str)
    year = request.args.get('year', type=int)
    data_type = request.args.get('data_type', type=str)
    stats = request.args.get('stats', type=str, default='mean')
    try:
        result = RT_analyzer.get_code_yearly_monthly_stats(
            code, year, data_type, stats)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/RT/points', methods=['POST'])
def points_yearly_monthly_stats():
    # Validate request has JSON data
    if not request.is_json:
        return jsonify({
            'error': 'Request must be JSON'
        }), HTTPStatus.BAD_REQUEST

    data = request.get_json()

    # Validate required fields
    if 'points' not in data or 'year' not in data or 'data_type' not in data:
        return jsonify({
            'error': 'points, year, and data_type are required fields'
        }), HTTPStatus.BAD_REQUEST

    # Get optional stats parameter
    stats = data.get('stats', 'mean')
    try:
        result = RT_analyzer.get_points_yearly_monthly_stats(
            data['points'], data['year'], data['data_type'], stats)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@app.route('/api/RT/coodinate', methods=['GET'])
def point_yearly_monthly_values():
    # Get query parameters
    lon = request.args.get('lon', type=float)
    lat = request.args.get('lat', type=float)
    year = request.args.get('year', type=int)
    data_type = request.args.get('data_type', type=str)

    # Validate required parameters
    if None in (lon, lat, year, data_type):
        return jsonify({
            'error': 'lon, lat, year, and data_type parameters are required'
        }), HTTPStatus.BAD_REQUEST

    try:
        result = RT_analyzer.get_point_yearly_monthly_values(
            (lon, lat), year, data_type)
        return jsonify({'data': result}), HTTPStatus.OK
    except ValueError as e:
        return jsonify({'error': str(e)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6419)