import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 原始数据
data_dict = {
    "annual_change_rates": {
        "建设用地": [
            {"change_rate": 0.186, "year": 2001},
            {"change_rate": 5.887, "year": 2002},
            {"change_rate": 2.664, "year": 2003},
            {"change_rate": 3.211, "year": 2004},
            {"change_rate": 2.706, "year": 2005},
            {"change_rate": 2.177, "year": 2006},
            {"change_rate": -1.094, "year": 2007},
            {"change_rate": 2.064, "year": 2008},
            {"change_rate": 3.957, "year": 2009},
            {"change_rate": 1.15, "year": 2010},
            {"change_rate": -0.429, "year": 2011},
            {"change_rate": -0.849, "year": 2012},
            {"change_rate": 0.603, "year": 2013},
            {"change_rate": -0.234, "year": 2014},
            {"change_rate": -0.98, "year": 2015},
            {"change_rate": -1.639, "year": 2016},
            {"change_rate": -0.352, "year": 2017},
            {"change_rate": 0.433, "year": 2018},
            {"change_rate": -2.176, "year": 2019},
            {"change_rate": -3.826, "year": 2020},
            {"change_rate": 0.197, "year": 2021},
            {"change_rate": 1.851, "year": 2022}
        ],
        "水体": [
            {"change_rate": -4.927, "year": 2001},
            {"change_rate": -12.552, "year": 2002},
            {"change_rate": -9.901, "year": 2003},
            {"change_rate": -6.209, "year": 2004},
            {"change_rate": -15.244, "year": 2005},
            {"change_rate": -9.866, "year": 2006},
            {"change_rate": -1.539, "year": 2007},
            {"change_rate": -1.853, "year": 2008},
            {"change_rate": -3.717, "year": 2009},
            {"change_rate": -3.37, "year": 2010},
            {"change_rate": 6.024, "year": 2011},
            {"change_rate": 1.615, "year": 2012},
            {"change_rate": 5.356, "year": 2013},
            {"change_rate": -0.279, "year": 2014},
            {"change_rate": 0.168, "year": 2015},
            {"change_rate": -0.615, "year": 2016},
            {"change_rate": -3.995, "year": 2017},
            {"change_rate": 0.645, "year": 2018},
            {"change_rate": -0.058, "year": 2019},
            {"change_rate": 5.186, "year": 2020},
            {"change_rate": 5.651, "year": 2021},
            {"change_rate": -0.157, "year": 2022}
        ],
        "湿地": [
            {"change_rate": -18.063, "year": 2001},
            {"change_rate": 25.227, "year": 2002},
            {"change_rate": 25.59, "year": 2003},
            {"change_rate": 5.491, "year": 2004},
            {"change_rate": 34.658, "year": 2005},
            {"change_rate": -13.225, "year": 2006},
            {"change_rate": -24.736, "year": 2007},
            {"change_rate": -13.084, "year": 2008},
            {"change_rate": 7.527, "year": 2009},
            {"change_rate": -0.167, "year": 2010},
            {"change_rate": -32.22, "year": 2011},
            {"change_rate": -13.793, "year": 2012},
            {"change_rate": -28.286, "year": 2013},
            {"change_rate": -3.187, "year": 2014},
            {"change_rate": -6.584, "year": 2015},
            {"change_rate": 14.537, "year": 2016},
            {"change_rate": 25.769, "year": 2017},
            {"change_rate": -5.505, "year": 2018},
            {"change_rate": -9.061, "year": 2019},
            {"change_rate": -18.861, "year": 2020},
            {"change_rate": -6.14, "year": 2021},
            {"change_rate": 5.14, "year": 2022}
        ],
        "耕地": [
            {"change_rate": 4.78, "year": 2001},
            {"change_rate": -10.111, "year": 2002},
            {"change_rate": -5.706, "year": 2003},
            {"change_rate": -10.183, "year": 2004},
            {"change_rate": -9.751, "year": 2005},
            {"change_rate": -2.477, "year": 2006},
            {"change_rate": 13.397, "year": 2007},
            {"change_rate": -4.804, "year": 2008},
            {"change_rate": -19.57, "year": 2009},
            {"change_rate": -4.917, "year": 2010},
            {"change_rate": 7.847, "year": 2011},
            {"change_rate": 6.532, "year": 2012},
            {"change_rate": -3.066, "year": 2013},
            {"change_rate": 1.922, "year": 2014},
            {"change_rate": 7.031, "year": 2015},
            {"change_rate": 7.963, "year": 2016},
            {"change_rate": 1.971, "year": 2017},
            {"change_rate": -2.8, "year": 2018},
            {"change_rate": 12.414, "year": 2019},
            {"change_rate": 16.809, "year": 2020},
            {"change_rate": -3.839, "year": 2021},
            {"change_rate": -6.002, "year": 2022}
        ],"草地": [
        {
          "change_rate": 0,
          "year": 2001
        },
        {
          "change_rate": 0,
          "year": 2002
        },
        {
          "change_rate": 0,
          "year": 2003
        },
        {
          "change_rate": 0,
          "year": 2004
        },
        {
          "change_rate": 0,
          "year": 2005
        },
        {
          "change_rate": 200,
          "year": 2006
        },
        {
          "change_rate": 66.667,
          "year": 2007
        },
        {
          "change_rate": -60,
          "year": 2008
        },
        {
          "change_rate": 0,
          "year": 2009
        },
        {
          "change_rate": -50,
          "year": 2010
        },
        {
          "change_rate": -100,
          "year": 2011
        },
        {
          "change_rate": 0,
          "year": 2012
        },
        {
          "change_rate": 0,
          "year": 2013
        },
        {
          "change_rate": 0,
          "year": 2014
        },
        {
          "change_rate": 0,
          "year": 2015
        },
        {
          "change_rate": 100,
          "year": 2016
        },
        {
          "change_rate": -75,
          "year": 2017
        },
        {
          "change_rate": 0,
          "year": 2018
        },
        {
          "change_rate": 300,
          "year": 2019
        },
        {
          "change_rate": 100,
          "year": 2020
        },
        {
          "change_rate": -25,
          "year": 2021
        },
        {
          "change_rate": -33.333,
          "year": 2022
        }
      ],
      "裸地": [
        {
          "change_rate": 0,
          "year": 2001
        },
        {
          "change_rate": -100,
          "year": 2002
        },
        {
          "change_rate": 0,
          "year": 2003
        },
        {
          "change_rate": 0,
          "year": 2004
        },
        {
          "change_rate": 0,
          "year": 2005
        },
        {
          "change_rate": 0,
          "year": 2006
        },
        {
          "change_rate": -100,
          "year": 2007
        },
        {
          "change_rate": 0,
          "year": 2008
        },
        {
          "change_rate": 0,
          "year": 2009
        },
        {
          "change_rate": 0,
          "year": 2010
        },
        {
          "change_rate": 0,
          "year": 2011
        },
        {
          "change_rate": 0,
          "year": 2012
        },
        {
          "change_rate": 0,
          "year": 2013
        },
        {
          "change_rate": 0,
          "year": 2014
        },
        {
          "change_rate": 0,
          "year": 2015
        },
        {
          "change_rate": 0,
          "year": 2016
        },
        {
          "change_rate": 0,
          "year": 2017
        },
        {
          "change_rate": 0,
          "year": 2018
        },
        {
          "change_rate": -100,
          "year": 2019
        },
        {
          "change_rate": 0,
          "year": 2020
        },
        {
          "change_rate": 0,
          "year": 2021
        },
        {
          "change_rate": 0,
          "year": 2022
        }
      ],
      "针叶林": [
        {
          "change_rate": 14.286,
          "year": 2001
        },
        {
          "change_rate": 0,
          "year": 2002
        },
        {
          "change_rate": -25,
          "year": 2003
        },
        {
          "change_rate": 0,
          "year": 2004
        },
        {
          "change_rate": 0,
          "year": 2005
        },
        {
          "change_rate": 0,
          "year": 2006
        },
        {
          "change_rate": 0,
          "year": 2007
        },
        {
          "change_rate": 0,
          "year": 2008
        },
        {
          "change_rate": 0,
          "year": 2009
        },
        {
          "change_rate": 50,
          "year": 2010
        },
        {
          "change_rate": -22.222,
          "year": 2011
        },
        {
          "change_rate": 0,
          "year": 2012
        },
        {
          "change_rate": 0,
          "year": 2013
        },
        {
          "change_rate": 0,
          "year": 2014
        },
        {
          "change_rate": -14.286,
          "year": 2015
        },
        {
          "change_rate": 0,
          "year": 2016
        },
        {
          "change_rate": 16.667,
          "year": 2017
        },
        {
          "change_rate": 28.571,
          "year": 2018
        },
        {
          "change_rate": 11.111,
          "year": 2019
        },
        {
          "change_rate": -40,
          "year": 2020
        },
        {
          "change_rate": 0,
          "year": 2021
        },
        {
          "change_rate": 0,
          "year": 2022
        }
      ],
      "阔叶林": [
        {
          "change_rate": -2.424,
          "year": 2001
        },
        {
          "change_rate": -1.863,
          "year": 2002
        },
        {
          "change_rate": -6.962,
          "year": 2003
        },
        {
          "change_rate": 0,
          "year": 2004
        },
        {
          "change_rate": -0.68,
          "year": 2005
        },
        {
          "change_rate": 0,
          "year": 2006
        },
        {
          "change_rate": 1.37,
          "year": 2007
        },
        {
          "change_rate": -3.378,
          "year": 2008
        },
        {
          "change_rate": 0,
          "year": 2009
        },
        {
          "change_rate": -0.699,
          "year": 2010
        },
        {
          "change_rate": -1.408,
          "year": 2011
        },
        {
          "change_rate": 0,
          "year": 2012
        },
        {
          "change_rate": 0,
          "year": 2013
        },
        {
          "change_rate": 3.571,
          "year": 2014
        },
        {
          "change_rate": -1.379,
          "year": 2015
        },
        {
          "change_rate": 4.196,
          "year": 2016
        },
        {
          "change_rate": 4.027,
          "year": 2017
        },
        {
          "change_rate": 6.452,
          "year": 2018
        },
        {
          "change_rate": -1.212,
          "year": 2019
        },
        {
          "change_rate": -0.613,
          "year": 2020
        },
        {
          "change_rate": -3.086,
          "year": 2021
        },
        {
          "change_rate": -1.911,
          "year": 2022
        }
      ]
    }
}

# 提取数据并转换为DataFrame（修正版）
df = pd.DataFrame()
for category in data_dict["annual_change_rates"]:
    # 1. 提取当前地类的数据（例如："建设用地"）
    data_list = data_dict["annual_change_rates"][category]

    # 2. 转换为DataFrame（列为"year"和"change_rate"）
    temp_df = pd.DataFrame(data_list)

    # 3. 重置列名：将"change_rate"改为当前地类名称（如"建设用地"）
    temp_df = temp_df.rename(columns={"change_rate": category})

    # 4. 以"year"为索引，与全局DataFrame合并
    if df.empty:
        df = temp_df.set_index("year")
    else:
        df = df.join(temp_df.set_index("year"))

# 最终结果：行为年份，列为地类，值为变化率
# print(df.head())

# 绘制热力图
plt.figure(figsize=(12, 6))
sns.heatmap(
    df,                  # 直接使用修正后的DataFrame（索引为year，列为地类）
    cmap="coolwarm",     # 红蓝渐变色
    vmin=-20, vmax=40,   # 颜色范围（根据数据极值调整）
    annot=True,          # 显示数值
    fmt=".2f",           # 保留两位小数
    linewidths=0.5,      # 单元格边框
    cbar_kws={"shrink": 0.8}  # 压缩色条比例
)
plt.title("土地利用类型年变化率热力图（2001-2022）", fontsize=14)
plt.xlabel("地类", fontsize=12)
plt.ylabel("年份", fontsize=12)
plt.xticks(rotation=0)  # 横向显示地类名称
plt.show()