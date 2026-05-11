
class RasterAnalyzer:
    def __init__(self, data_path):
        self.data_path = data_path

    def extract_region_statistics(self, geometry):
        return {'mean': 0.5, 'std': 0.1, 'count': 1000}

    def extract_multi_year_statistics(self, geometry, years):
        results = {}
        for year in years:
            results[year] = {'mean': 0.5, 'std': 0.1}
        return results

    def get_available_data(self):
        return {'data_path': self.data_path, 'status': 'test_mode'}
