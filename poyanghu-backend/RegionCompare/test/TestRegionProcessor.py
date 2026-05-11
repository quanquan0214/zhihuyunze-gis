
class RegionProcessor:
    def __init__(self):
        self.regions = {}

    def add_region_from_points(self, points, region_name, region_id=None, crs='EPSG:4326'):
        if region_id is None:
            region_id = f"region_{len(self.regions)}"

        self.regions[region_id] = {
            'name': region_name,
            'geometry': f'test_geometry_{region_id}',
            'area_km2': 1000.0,
            'bounds': [115.0, 28.0, 116.0, 29.0]
        }
        return region_id

    def add_region_from_vector(self, vector_data, region_name, region_id=None):
        return self.add_region_from_points([], region_name, region_id)

    def get_all_regions(self):
        return self.regions

    def get_region(self, region_id):
        return self.regions.get(region_id)
