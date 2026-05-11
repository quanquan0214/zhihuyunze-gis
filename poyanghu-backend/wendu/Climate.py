import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize


def parse_date_from_filename(filename):
    # 假设文件名中包含年月，如 temp_200001.tif
    # 你根据实际文件名格式改这里
    basename = os.path.basename(filename)
    # 示例： temp_200001.tif -> '200001'
    date_str = basename.split('.')[0]
    year = int(date_str[:4])
    month = int(date_str[4:6])
    return year, month


def load_images_to_array(image_folder):
    file_list = sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith('.tif')])

    data_list = []
    time_list = []

    for fpath in file_list:
        with rasterio.open(fpath) as src:
            img = src.read(1)  # 读取第一波段
            data_list.append(img)
            year, month = parse_date_from_filename(fpath)
            time_list.append((year, month))

    data_stack = np.stack(data_list)  # 形状: (288, H, W)
    return data_stack, time_list


def get_global_min_max(data_stack):
    global_min = np.nanmin(data_stack)
    global_max = np.nanmax(data_stack)
    return global_min, global_max


def normalize_data(data_stack, vmin, vmax):
    # 归一化到0-1之间，clip防止超出范围
    norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
    normalized = norm(data_stack)
    return normalized


def apply_colormap(normalized_data, cmap_name='viridis'):
    # normalized_data 形状 (288, H, W), 0-1浮点
    cmap = cm.get_cmap(cmap_name)
    # 映射到RGBA，返回shape (288, H, W, 4)
    colored = cmap(normalized_data)
    return colored


def save_to_npz(output_path, data_array, time_list):
    # 保存归一化后的数据和时间戳
    np.savez_compressed(output_path, data=data_array, time=np.array(time_list))
    print(f"数据已保存到 {output_path}")


def main():
    folder = "D:/Google/temperture/data"  # 影像文件夹
    output_file = "D:/Google/temperture/temperature_288.npz"

    # 1. 读取所有影像 → 转为数组 + 时间戳
    data_stack, time_list = load_images_to_array(folder)
    print(f"读入数据形状: {data_stack.shape}")

    # 2. 统计全局 min/max
    vmin, vmax = get_global_min_max(data_stack)
    print(f"全局温度范围: min={vmin}, max={vmax}")

    # 3. 归一化
    normalized_data = normalize_data(data_stack, vmin, vmax)

    # 4. 可选：映射为颜色（RGBA）用于渲染预览（不一定必须保存）
    # colored_data = apply_colormap(normalized_data, cmap_name='viridis')

    # 5. 按时间排序 已经file_list按文件名排序，一般是时间顺序，可确认

    # 6. 保存结果（这里存npz方便后续加载）
    save_to_npz(output_file, normalized_data, time_list)


if __name__ == "__main__":
    main()
