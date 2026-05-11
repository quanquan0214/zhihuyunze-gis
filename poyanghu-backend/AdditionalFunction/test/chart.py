# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np
# from datetime import datetime
#
#
# def plot_trend_with_strength(df, trend_type, r_squared, predictions, title="趋势分析结果"):
#     # 准备数据
#     df['date'] = pd.to_datetime(df['date'])
#     df = df.sort_values('date')
#
#     # 可视化
#     plt.figure(figsize=(10, 6))
#     plt.plot(df['date'], df['value'], label='原始数据', marker='o')
#
#     # 绘制趋势线
#     pred_dates = pd.to_datetime([datetime.fromtimestamp(t['time']) for t in predictions])
#     pred_values = [t['predicted_value'] for t in predictions]
#     plt.plot(pred_dates, pred_values, label=f'{trend_type} 拟合', linestyle='--', color='orange')
#
#     # 可选：绘制置信区间
#     lower = [t['confidence_interval'][0] for t in predictions]
#     upper = [t['confidence_interval'][1] for t in predictions]
#     plt.fill_between(pred_dates, lower, upper, color='orange', alpha=0.2, label='±5% 置信区间')
#
#     # 趋势强度判断
#     if r_squared > 0.8:
#         strength = 'strong'
#     elif r_squared > 0.5:
#         strength = 'moderate'
#     elif r_squared > 0.3:
#         strength = 'weak'
#     else:
#         strength = 'no_trend'
#
#     # 标题与文本标注
#     plt.title(title)
#     plt.xlabel('年份')
#     plt.ylabel('值')
#     plt.legend()
#
#     # 文本标注
#     text = f"趋势类型: {trend_type}\nR² = {r_squared:.3f}\n趋势强度: {strength}"
#     plt.text(0.02, 0.95, text, transform=plt.gca().transAxes,
#              fontsize=10, verticalalignment='top',
#              bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
#
#     plt.tight_layout()
#     plt.grid(True)
#     plt.show()


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO
import base64


def plot_trend_with_strength(df, trend_type, r_squared, predictions, title="趋势分析结果", save_to_buffer=None):
    """
    Modified version to support both displaying and saving to buffer for Flask API

    Args:
        df: DataFrame with 'date' and 'value' columns
        trend_type: String describing the trend type
        r_squared: Float R-squared value
        predictions: List of prediction dictionaries
        title: Plot title
        save_to_buffer: If provided, saves plot to this buffer instead of showing
    """
    # Prepare data
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Create figure
    plt.figure(figsize=(10, 6))

    # Plot original data
    plt.plot(df['date'], df['value'], label='原始数据', marker='o')

    # Plot trend line - adjust for different prediction formats
    if isinstance(predictions, list) and len(predictions) > 0:
        if 'time' in predictions[0]:  # Original format with timestamp
            pred_dates = pd.to_datetime([datetime.fromtimestamp(t['time']) for t in predictions])
            pred_values = [t['predicted_value'] for t in predictions]
        else:  # New format with date objects
            pred_dates = [t['date'] for t in predictions]
            pred_values = [t['predicted_value'] for t in predictions]

        plt.plot(pred_dates, pred_values, label=f'{trend_type} 拟合', linestyle='--', color='orange')

        # Plot confidence interval if available
        if 'confidence_interval' in predictions[0]:
            lower = [t['confidence_interval'][0] for t in predictions]
            upper = [t['confidence_interval'][1] for t in predictions]
            plt.fill_between(pred_dates, lower, upper, color='orange', alpha=0.2, label='±5% 置信区间')

    # Determine trend strength
    if r_squared > 0.8:
        strength = '强'
    elif r_squared > 0.5:
        strength = '中等'
    elif r_squared > 0.3:
        strength = '弱'
    else:
        strength = '无趋势'

    # Add title and labels
    plt.title(title)
    plt.xlabel('年份')
    plt.ylabel('RSEI值')
    plt.legend()

    # Add info text
    text = f"趋势类型: {trend_type}\nR² = {r_squared:.3f}\n趋势强度: {strength}"
    plt.text(0.02, 0.95, text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    plt.tight_layout()
    plt.grid(True)

    # Handle output - either save to buffer or show
    if save_to_buffer:
        plt.savefig(save_to_buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        return None
    else:
        plt.show()
        return None


def plot_to_base64():
    """Helper function to convert current plot to base64 string"""
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')