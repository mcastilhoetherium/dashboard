import osmnx as ox
import geopandas as gpd

# Nome da cidade para a busca no OpenStreetMap
cidade = "Barueri, São Paulo, Brazil"

# Download dos dados geográficos de Barueri
graph = ox.graph_from_place(cidade, network_type='all')

# Convertendo o grafo para GeoDataFrame (nós e arestas)
nodes, edges = ox.graph_to_gdfs(graph)

# Salvando as arestas (ruas e caminhos) como um arquivo GeoJSON
edges.to_file("barueri_edges.geojson", driver='GeoJSON')

# Salvando os nós (interseções e pontos) como um arquivo GeoJSON
nodes.to_file("barueri_nodes.geojson", driver='GeoJSON')

print("GeoJSON criado com sucesso!")
