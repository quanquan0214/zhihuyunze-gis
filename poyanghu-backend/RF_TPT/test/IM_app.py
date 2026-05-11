import sys
import os
import matplotlib

matplotlib.use('Agg')
from flask import Flask, jsonify
from flask_cors import CORS
from RegionCompare.ComparisonAnalyzer import ComparisonAnalyzer
from LCAnalyzer.land_cover_analyzer import LandCoverAnalyzer
from RF_TPT.test.Climate import ClimateDataService

# Get current directory and add Connect to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'Connect'))
sys.path.append(os.path.join(current_dir, 'AdditionalFunction'))
sys.path.append(os.path.join(current_dir, 'RegionCompare'))
sys.path.append(os.path.join(current_dir, 'LCAnalyzer'))
sys.path.append(os.path.join(current_dir, 'RF_TPT'))

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 禁用 ASCII 转义
app.config['SECRET_KEY'] = 'test'
CORS(app)

# Configuration for predict endpoint
DATA_DIR = 'D:/Google/RSEI_full'
PREDICT_YEARS = 5
RC_analyzer = ComparisonAnalyzer(data_directory=DATA_DIR)
LC_analyzer = LandCoverAnalyzer()
RT_analyzer = ClimateDataService()

@app.route('/api/im/trend', methods=['GET'])
def get_im_trend():
    """
    获取温度、降水、RSEI的年际趋势数据（用于趋势折线图）
    """
    try:
        # 获取时间序列数据
        rsei_series = RT_analyzer.get_time_series_data('rsei')  # 平均值趋势
        temperature_series = RT_analyzer.get_time_series_data('temperature')
        rainfall_series = RT_analyzer.get_time_series_data('rainfall')

        return jsonify({
            'success': True,
            'data': {
                'rsei': rsei_series,
                'temperature': temperature_series,
                'rainfall': rainfall_series
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取趋势数据失败: {str(e)}'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7891)


