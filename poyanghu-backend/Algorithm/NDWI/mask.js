// 定义函数
function getBinaryNDWI(date, roi) {
  var start = ee.Date(date).advance(-15, 'day');
  var end = ee.Date(date).advance(15, 'day');
  // 定义 Landsat 8 数据集合
  var landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .filterDate(start,end)
    .filterBounds(roi)
    .map(function(image) {
      // 去云
      var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
      var saturationMask = image.select('QA_RADSAT').eq(0);
      var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
      return image.addBands(opticalBands, null, true)
        .updateMask(qaMask)
        .updateMask(saturationMask);
    });

  var ndwil8=landsat8.map(function(image){
      var ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI');
      return image.addBands(ndwi);
  });
  
  // 定义 Sentinel-2 数据集合
  var sentinel2 = ee.ImageCollection("COPERNICUS/S2_SR")
    .filterDate(start,end)
    .filterBounds(roi)
    .map(function(image) {
      // 去云
      var qa = image.select('QA60');
      var cloudBitMask = 1 << 10;
      var cirrusBitMask = 1 << 11;
      var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
        .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
      return image.updateMask(mask).divide(10000);
    });

  var ndwisen2=sentinel2.map(function(image){
      var ndwi = image.normalizedDifference(['B3', 'B5']).rename('NDWI');
      return image.addBands(ndwi);
  });

  // 合并两个数据集合
  var ndwiCollection = ndwil8.merge(ndwisen2);

  // 计算平均值
  var meanNDWI = ndwiCollection.select('NDWI').mean();

  // 二值化分类
  var binaryNDWI = meanNDWI.gt(0.1); // 设定 NDWI 阈值为 0.1

  return binaryNDWI;
}


// 读取目标区域
var roi = ee.FeatureCollection("users/chenliyuan327/poyangRegion");
//2018-10-23
var timeList = table.aggregate_array('2018-10-23');
print(timeList);
//lenth = timeList.Length()
//for (var i = 0; i < timeList.length; i++){
// 设定日期
var date = '2020-09-15';//ee.String(timeList.get(i));
print(date)
// 调用函数获取二值化 NDWI 结果
var binaryResult = getBinaryNDWI(date, roi);

if (binaryResult) {   
  print(date,'had existed.')
  // 显示结果   
  Map.centerObject(roi, 8);
  //水体用蓝色表示，非水体用红色表示。
  //Map.addLayer(binaryResult.clip(roi), {palette: ['red', 'blue']}, 'Binary NDWI'); 
}

// 读取目标区域
var clip1 = ee.FeatureCollection("users/chenliyuan327/firstclip");
//Map.addLayer(clip1,{},"firstclip");

// 获取二值化后的binaryResult中NDWI值为1的部分
var ndwi = binaryResult.clip(clip1).eq(1);
Map.addLayer(ndwi, {palette: ['red', 'blue']}, 'NDWI = 1');

