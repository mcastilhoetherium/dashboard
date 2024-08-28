import json
import geopandas as gpd

# Carregar o arquivo GeoJSON
gdf = gpd.read_file("barueri_edges.geojson")

# Converter GeoDataFrame para um formato JSON simples
def geojson_to_json(df):
    json_list = []
    for _, row in df.iterrows():
        geometry = row['geometry']
        if geometry.geom_type == 'Point':
            coords = {'longitude': geometry.x, 'latitude': geometry.y}
        elif geometry.geom_type == 'Polygon':
            coords = {'coordinates': list(geometry.exterior.coords)}
        elif geometry.geom_type == 'LineString':
            coords = {'coordinates': list(geometry.coords)}
        else:
            coords = None
        
        feature = {
            'type': 'Feature',
            'geometry': coords,
            'properties': row.drop('geometry').to_dict()
        }
        json_list.append(feature)
    
    return {'type': 'FeatureCollection', 'features': json_list}

# Converter o GeoDataFrame para JSON
json_data = geojson_to_json(gdf)

# Salvar o JSON em um arquivo
with open('barueri_data.json', 'w') as f:
    json.dump(json_data, f, indent=2)

print("JSON criado com sucesso!")
