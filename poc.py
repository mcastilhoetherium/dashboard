import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from dash.dependencies import Output, State, Input, ALL
import folium
from folium import plugins
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import logging
from io import BytesIO 
import base64
import math
from dash import dash_table
import webbrowser
from dash import no_update
import plotly.express as px
from flask import Flask, render_template,request, jsonify, redirect, url_for



server = Flask(__name__)
flag = 0 


def create_tabs(access_type):
    print (access_type)
    tabs = []
    # Aba Dashboard (visível para todos)
    tabs.append(dbc.Tab(label="Dashboard", tab_id="dashboard", tab_style={"height": "100%", "font-size": "20px"}))
    tabs.append(dbc.Tab(label="Mapa", tab_id="maps", tab_style={"height": "100%", "font-size": "20px"}))

    # Aba Relatórios (visível para 'full', 'adm', e 'relatorio')
    if access_type in ['full', 'adm', 'relatorio']:
        tabs.append(dbc.Tab( label="Relatório",tab_id="totals", tab_style={"height": "100%", "font-size": "20px"}))

    # Aba Processos (visível para todos)
    tabs.append(dbc.Tab(label="Processos", tab_id="protocols", tab_style={"height": "100%", "font-size": "20px"}))

    # Aba Configuração (visível para 'full' e 'adm')
    if access_type in ['full', 'adm']:
        tabs.append(dbc.Tab(label="Configuração", tab_id="settings", tab_style={"height": "100%", "font-size": "20px"}))

    # Aba Parâmetros (visível apenas para 'full')
    if access_type == 'full':
        tabs.append(dbc.Tab(label="Parâmetros", tab_id="parametros", tab_style={"height": "100%", "font-size": "20px"}))

    return tabs



def verificar_token():
    endpoint = "http://127.0.0.1:5000/validar_token"
    try:
        response = requests.get(endpoint)
        response.raise_for_status()  # Lança uma exceção para erros HTTP
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get('status') == 'sim':  # Verifica se o status é 'Sim'
                return True
            else:
                logging.warning(f"Token inválido. Status: {json_data.get('status')}")
                return False
        else:
            logging.warning(f"Requisição falhou com status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao fazer requisição para {endpoint}: {e}")
        return False
    except ValueError as e:
        logging.error(f"Erro ao decodificar JSON: {e}")
        return False    
app = dash.Dash(__name__, server=server, url_base_pathname='/dashboard/',external_stylesheets=[
        dbc.themes.MATERIA, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.5.0/font/bootstrap-icons.min.css"], suppress_callback_exceptions=True) # Claro


def get_open_calls():
    # Aqui você deve substituir esta função pela função real que obtém os chamados abertos do servidor
    return [
        {"id": 1, "title": "Chamado 1", "description": "Descrição do chamado 1", "status": "Aberto"},
        {"id": 2, "title": "Chamado 2", "description": "Descrição do chamado 2", "status": "Aberto"},
        {"id": 3, "title": "Chamado 3", "description": "Descrição do chamado 3", "status": "Aberto"},
    ]

# Função para criar os cards dos chamados abertos
def create_open_calls():
    calls = get_open_calls()
    call_cards = []
    for call in calls:
        call_card = dbc.Card(
            dbc.CardBody([
                html.H4(call["title"], className="card-title"),
                html.P(f"Descrição: {call['description']}"),
                html.P(f"Status: {call['status']}"),
                dbc.Button("Detalhes", id={"type": "open-call-button", "index": call["id"]}, className="mr-2", color="#9b559c", outline=True),
            ])
        )
        call_cards.append(call_card)
    return call_cards


def create_offcanvas_content(call_type):
    # Aqui você deve substituir esta lógica pela lógica real para obter os detalhes do chamado com base no tipo
    if call_type == "chamado1":
        content = "Detalhes do Chamado 1..."
    elif call_type == "chamado2":
        content = "Detalhes do Chamado 2..."
    elif call_type == "chamado3":
        content = "Detalhes do Chamado 3..."
    else:
        content = "Tipo de chamado não reconhecido"
    return dbc.Card(
        dbc.CardBody([
            html.H4("Detalhes do Chamado", className="card-title"),
            html.P(content),
        ]),
        className="mt-3",
    )
def get_data_from_api():
    url = 'http://127.0.0.1:5000/ocorrencia_priorizada'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Converter a lista de listas para a lista de dicionários
        formatted_data = [{'label': item[0], 'value': item[0]} for item in data]
        return formatted_data
    else:
        return []
    
    


def get_ocorrencias():
    url = "http://127.0.0.1:5000/ocorrencias"  # Substitua pela URL da sua API
    response = requests.get(url)
    
    if response.status_code == 200:
        ocorrencia = response.json()  # Assumindo que o retorno é um JSON com a lista de ocorrências
        options = [{"label": occ["nome"], "value": occ["id"]} for occ in ocorrencia]
        return options
    else:
        return []
    
    
def get_coordenadas():
    endpoint = "http://127.0.0.1:5000/coordenadas"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def get_car_location_data():
    
    endpoint = "http://127.0.0.1:5000/dados_localizacao_carro"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def create_generic_map():
    # Definindo o layout do mapa
    map_layout = go.Layout(
        mapbox_style="open-street-map",  # Estilo do mapa
        margin={"l": 0, "r": 0, "t": 0, "b": 0},  # Margens do layout
        mapbox=dict(
            center=dict(lat=-23.48474866666667, lon=-46.86931466666667),  # Centro do mapa
            zoom=10  # Zoom inicial
        )
    )

    # Criando a figura do mapa
    map_figure = go.Figure(layout=map_layout)

    # Adicionando um marcador no centro do mapa
    map_figure.add_trace(go.Scattermapbox(
        lat=[0],  # Latitude do marcador
        lon=[0],  # Longitude do marcador
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=14,
            color='red',
            opacity=0.7
        ),
        text='Centro do Mapa'
    ))

    # Configurando o tamanho do mapa
    map_figure.update_layout(height=400)

    return dcc.Graph(
        id='generic-map',
        figure=map_figure,
        
    )




def create_generic_map2():
    # Definindo o layout do mapa
    map_layout = go.Layout(
        mapbox_style="open-street-map",  # Estilo do mapa
        margin={"l": 0, "r": 0, "t": 0, "b": 0},  # Margens do layout
        mapbox=dict(
            center=dict(lat=-23.48474866666667, lon=-46.86931466666667),  # Centro do mapa
            zoom=15 # Zoom inicial
        )
    )

    # Criando a figura do mapa
    map_figure = go.Figure(layout=map_layout)

    # Adicionando um marcador no centro do mapa
    map_figure.add_trace(go.Scattermapbox(
        lat=[0],  # Latitude do marcador
        lon=[0],  # Longitude do marcador
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=14,
            color='red',
            opacity=0.7
        ),
        text='Centro do Mapa'
    ))

    # Configurando o tamanho do mapa
    map_figure.update_layout(height=500)

    return dcc.Graph(id='generic-map', figure=map_figure)
def create_car_location_map(data):
    coordinates = [eval(item["coordenada"]) for item in data]
    latitudes = [coord[0] for coord in coordinates]
    longitudes = [coord[1] for coord in coordinates]

    map_card = dbc.Card(
        dbc.CardBody([
            html.H4("Mapa da Localização do Carro", className="card-title"),
            dcc.Graph(
                id="car-location-map",
                figure={
                    "data": [{
                        "type": "scattermapbox",
                        "lat": latitudes,
                        "lon": longitudes,
                        "mode": "lines+markers",
                        "marker": {
                            "size": 10,
                            "opacity": 0.7,
                            "color": "#00cc96"
                        },
                        "hoverinfo": "text",
                        "hovertext": ["Data: " + item["data"] for item in data]
                    }],
                    "layout": {
                        "mapbox": {
                            "style": "open-street-map",
                            "zoom": 10,
                            "center": {"lat": latitudes[0], "lon": longitudes[0]}
                        },
                        "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
                        "height": 335
                    }
                }
            )
        ]),
        className="mt-3",
        style={'marginTop': '0'}
    )

    return map_card

# Layout do mapa
def create_map(data):
    # Criação dos marcadores no mapa com informações de intercorrência
    markers = []
    for item in data:
        tipo = item[0]
        coordenadas = eval(item[1])
        imagem = item[2]  # Obtém a URL da imagem

        # Adiciona um marcador com informações de hover
        markers.append(
            dict(
                lat=coordenadas[0],
                lon=coordenadas[1],
                hoverinfo="text",
                hovertext=f"Tipo: {tipo}",
                imagem=f"https://urbanai.meumunicipio.online/{imagem}"  # Inclui a URL da imagem nos dados do marcador
            )
        )

    map_card = dbc.Card(
        dbc.CardBody([
            html.H4("Mapa de Intercorrências", className="card-title"),
           
            dcc.Graph(
                id="mapa",
                figure={
                    "data": [{
                        "type": "scattermapbox",
                        "lat": [marker['lat'] for marker in markers],
                        "lon": [marker['lon'] for marker in markers],
                        "mode": "markers",
                        "marker": {
                            "size": 10,
                            "opacity": 0.7,
                            "color": [marker.get('color', '#9a559c') for marker in markers],  
                        },
                        "hoverinfo": "text",
                        "hovertext": [marker['hovertext'] for marker in markers],
                        "customdata": [marker['imagem'] for marker in markers],  # Passa a URL da imagem para customdata
                    }],
                    "layout": {
                        "mapbox": {
                            "style": "open-street-map",
                            "zoom": 16,
                            "center": {"lat": -23.48474866666667, "lon": -46.86931466666667}
                        },
                        "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
                        "height": 970
                    }
                }
            )
        ]),
        className="mt-3",
        style={'marginTop': '0'}
    )

    return map_card
    
def get_car_location_data():
    endpoint = "http://127.0.0.1:5000/dados_localizacao_carro"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Modifique a função create_map para criar o novo mapa com base nos dados de localização do carro
def create_car_location_map(data):
    if not data:
        raise ValueError("Os dados de localização do carro estão vazios ou não foram encontrados")

    try:
        coordinates = [json.loads(item["coordenada"]) for item in data]  # Use json.loads para converter coordenadas em listas
        print("Coordenadas:", coordinates)  # Depuração: Verificar coordenadas

        if not all(isinstance(coord, (list, tuple)) and len(coord) >= 2 for coord in coordinates):
            raise ValueError("Formato de coordenadas inválido")

        latitudes = [coord[0] for coord in coordinates]
        longitudes = [coord[1] for coord in coordinates]

        map_card = dbc.Card(
            dbc.CardBody([
                html.H4("Mapa da Localização do Carro", className="card-title"),
                dcc.Graph(
                    id="car-location-map",
                    figure={
                        "data": [{
                            "type": "scattermapbox",
                            "lat": latitudes,
                            "lon": longitudes,
                            "mode": "lines+markers",
                            "marker": {
                                "size": 10,
                                "opacity": 0.7,
                                "color": "#00cc96"
                            },
                            "hoverinfo": "text",
                            "hovertext": ["Data: " + item["data"] for item in data]
                        }],
                        "layout": {
                            "mapbox": {
                                "style": "open-street-map",
                                "zoom": 15,
                                "center": {"lat": latitudes[0], "lon": longitudes[0]}  # Centraliza no primeiro ponto
                            },
                            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
                            "height": 335
                        }
                    }
                )
            ]),
            className="mt-3",
            style={'marginTop': '0'}
        )

        return map_card
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Erro ao processar os dados de localização do carro: {e}")
        return html.Div("Erro ao processar os dados de localização do carro.")

def get_images():
    endpoint = "http://127.0.0.1:5000/imagens"
    response = requests.get(endpoint)
    if response.status_code == 200: 
        return response.json()
    else:
        return []

def get_numero_intercorrencia():
    endpoint = "http://127.0.0.1:5000/total_intercorrencias"
    response = requests.get(endpoint)
    if response.status_code == 200:
        total_intercorrencias = response.json()["total"]
        return f" {total_intercorrencias}"
    else:
        return "Erro ao obter o total de intercorrências"

def get_ruas_percorridas():
    endpoint = "http://127.0.0.1:5000/total_ruas"
    response = requests.get(endpoint)
    if response.status_code == 200:
        total_ruas = response.json()["total"]
        return f" {total_ruas}"
    else:
        return "Erro ao obter o total de ruas"

def get_bairros_percorridos():
    endpoint = "http://127.0.0.1:5000/total_bairros"
    response = requests.get(endpoint)
    if response.status_code == 200:
        total_bairros = response.json()["total"]
        return f" {total_bairros}"
    else:
        return "Erro ao obter o total de bairros"
    
def get_total_requerementos():
    endpoint = "http://127.0.0.1:5000/total_requerimentos"
    response = requests.get(endpoint)
    if response.status_code == 200:
        total_requerimentos = response.json()["total_requerimentos"]
        return f" {total_requerimentos}"
    else:
        return "Erro ao obter o total de requirementos"

def get_distancia_percorrida():
    endpoint = "http://127.0.0.1:5000/distancia_total"
    response = requests.get(endpoint)
    if response.status_code == 200:
        distancia = response.json()["distancia_total_km"]
        return f" {distancia}"
    else:
        return "Erro ao obter a quilometragem"


def get_total_intercorrencias_por_tipo():
    endpoint = "http://127.0.0.1:5000/total_intercorrencias_por_tipo"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Estilo da sidebar direita
sidebar_right_style = {
    'background-color': 'blue',
    'color': 'black',
    'min-height': '96%',
    'width': '13%',
    'position': 'absolut',
    'top': '0',
    'right': '0',
    'padding': '20px',
    'border-radius': '15px',
    'margin-top': '1.5%',
    'border': '1px solid #d2d2d2',
    'margin-right': '25px',
    'background': 'blue',
}

def content_style():
    return {
        'marginLeft': '15%',  # Adiciona a largura da barra lateral ao valor da margem esquerda
        'marginTop': '1.5%',  # Adiciona um pequeno espaço acima
        'height': 'calc(100vh - 20px)',  # Ocupa a altura total da tela, menos a barra superior
        'width': 'calc(85% - 40px)'  # Ocupa 85% do espaço disponível, menos a largura da barra lateral e da margem esquerda e direita
    }

sidebar_left_style = {
    'min-height': '100%',
    'width': '15%',
    'position': 'fixed',
    'top': '0',
    'left': '0',
    'padding': '20px',
    'border-right': '4px solid #ffffff40',
      # Alterado para uma cor mais clara*/-+
}
# Layout do chat
# Criando o card que contém o carrossel de cards
feed_cards = [
    dbc.Card([
        dbc.CardBody("Foram abertos 5 novos chamados")
    ]),
    html.Br(),
    dbc.Card([
        dbc.CardBody("Chamado refente a Secretaria de Obras em andamento")
    ]),
    html.Br(),
    dbc.Card([
        dbc.CardBody("Foram concluídos 3 chamados referentes a buraco")
    ]),
    html.Br(),
    dbc.Card([
        dbc.CardBody("Carro online")
    ]),
    html.Br(),
    dbc.Card([
        dbc.CardBody("Priorização: Número elevados de placas danificadas, chamado aberto")
    ]),
]


# Função para renderizar os cards do feed com um intervalo de tempo
def render_feed_cards(n):
    if n >= len(feed_cards):
        return None
    return feed_cards[:n+1]


feed_content = dbc.CardBody([
    html.Div(id="feed-content", children=[])
])

chat_content = dbc.CardBody([
    html.Div(id="chat-content", style={'overflowY': 'scroll-bar', 'height': '250px'}),

])

# Abas
tabs = dbc.Tabs(
    [
        dbc.Tab(feed_content, label="Feed"),
        dbc.Tab(chat_content, label="Insights"),
    ]
)

# Card com abas
chat_layout = html.Div([
    dbc.Card(
        [
            dbc.CardHeader(
                [
                    
                    tabs
                ]
            ),
            dbc.Collapse(
                dbc.CardBody([
                  
                ]),
                id="collapse",
                is_open=True,
            ),
        ],
        style={"position": "fixed", "bottom": "10px", "right": "10px", "width": "300px", "zIndex": 999}
    )
])

@app.callback(
    Output('feed-content', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_feed(n_intervals):
    return render_feed_cards(n_intervals)


@app.callback(
    Output("collapse", "is_open"),
    [Input("chat-header", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("chat-content", "children"),
    [Input("chat-input", "value")]
)
def update_chat(message):
    if message:
        return [html.P(message)]
    else:
        return []
def create_carousel(items):
    carousel_items = []
    for item in items:
        carousel_items.append({
            "key": item["path"],
            "src": item["path"],
            "caption": "",
            "content": [
                dbc.CardBody([
                    html.P(f"Tipo: {item['tipo']}"),
                    html.P(f"Rua: {item['rua']}"),
                    html.P(f"Bairro: {item['bairro']}")
                ])
            ]
        })
    return dbc.Carousel(
        items=carousel_items,
        ride="carousel",  # Para avançar automaticamente
        interval=3000,  # Defina o intervalo de troca de imagens em milissegundos (3 segundos)
        variant="dark"
    )


def get_top_ruas_intercorrencias():
    endpoint = "http://127.0.0.1:5000/top_ruas_intercorrencias"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()[1:]  # Removendo o primeiro item da lista que é null
    else:
        return []

def create_top_ruas_intercorrencias_chart(data):
    ruas = [item[1] for item in data]  # Obtém o nome da rua a partir do segundo elemento da tupla
    quantidades = [item[0] for item in data]  # Obtém a quantidade a partir do primeiro elemento da tupla

    fig = go.Figure(go.Funnelarea(
        text=ruas,  # Utiliza os nomes das ruas como texto
        values=quantidades  # Utiliza as quantidades como valores
    ))
    fig.update_layout(title="",paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    return dcc.Graph(figure=fig, style={'height': '40vh'})



def get_top_bairros_intercorrencias():
    endpoint = "http://127.0.0.1:5000/top_bairros_intercorrencias"
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()[1:]  # Removendo o primeiro item da lista que é null
    else:
        return []

def create_top_bairros_intercorrencias_chart(data):
    bairros = [item[1] for item in data]  # Obtém o nome da rua a partir do segundo elemento da tupla
    quantidades = [item[0] for item in data]  # Obtém a quantidade a partir do primeiro elemento da tupla

    fig = go.Figure(go.Funnelarea(
        text=bairros,  # Utiliza os nomes das ruas como texto
        values=quantidades  # Utiliza as quantidades como valores
    ))
    fig.update_layout(title="",paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',showlegend=False)

    return dcc.Graph(figure=fig, style={'height': '40vh'})



'''sidebar_left = dbc.Col(
    style=sidebar_left_style,
    xs=12, sm=6, md=5, lg=4, xl=3,
    children=[
        html.Div(
            style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'height': '100%'},
            children=[
                html.Img(src="dashboard/assets/logo.png", height="auto", style={'max-height': '100%', 'max-width': '100%', 'vertical-align': 'middle'})
            ]
        ),
        html.Br(),
        html.Div([
            dbc.Label("Ocorrências:"),
            dbc.DropdownMenu(
                label="Asfalto",
                toggle_style={
                    "color": "#717171",
                    "background": "#fff",
                    "width": "100%",
                    "textTransform": "none",
                    "text-align": 'left'
                },
                children=[
                    dbc.Checklist(
                        options=[
                            {"label": "Afundamento", "value": "Afundamento"},
                            {"label": "Buraco", "value": "Buraco"},
                            {"label": "Corrugação", "value": "Corrugação"},
                            {"label": "Desgaste", "value": "Desgaste"},
                            {"label": "Desnível", "value": "Desnível"},
                            {"label": "Fissura", "value": "Fissura"},
                            {"label": "Remendo", "value": "Remendo"},
                            {"label": "Trinca bloco", "value": "Trinca bloco"},
                            {"label": "Trinca bordo", "value": "Trinca bordo"},
                            {"label": "Trinca fadiga", "value": "Trinca fadiga"},
                            {"label": "Trinca isolada", "value": "Trinca isolada"},
                        ],
                        id="asfalto-checklist",
                    ),
                ],
                style={"width": "100%"}
            ),
            html.Br(),
            dbc.DropdownMenu(
                label="Sinalização",
                toggle_style={
                    "color": "#717171",
                    "background": "#fff",
                    "width": "100%",
                    "textTransform": "none",
                    "text-align": 'left'
                },
                children=[
                    dbc.Checklist(
                        options=[
                            {"label": "Alerta de pavimentação danificado", "value": "Alerta de pavimentação danificado"},
                            {"label": "Faixa pedestre", "value": "Faixa pedestre"},
                            {"label": "Faixa pedrestre danificada", "value": "Faixa pedrestre danificada"},
                            {"label": "Placa de trânsito", "value": "Placa de trânsito"},
                            {"label": "Placa de trânsito danificada", "value": "Placa de trânsito danificada"},
                            {"label": "Placa de trânsito encoberta", "value": "Placa de trânsito encoberta"},
                            {"label": "Semáforo", "value": "Semáforo"},
                        ],
                        id="sinalizacao-checklist",
                        inline=False
                    ),
                ],
                style={"width": "100%"}
            ),
            html.Br(),
            dbc.DropdownMenu(
                label="Vias Públicas",
                toggle_style={
                    "color": "#717171",
                    "background": "#fff",
                    "width": "100%",
                    "textTransform": "none",
                    "text-align": 'left'
                },
                children=[
                    dbc.Checklist(
                        options=[
                            {"label": "Arbusto em fiação", "value": "Arbusto em fiação"},
                            {"label": "Guard rail", "value": "Guard rail"},
                            {"label": "Guard rail danificado", "value": "Guard rail danificado"},
                            {"label": "Lixo", "value": "Lixo"},
                            {"label": "Mato alto", "value": "Mato alto"},
                            {"label": "Veículo estacionado irregularmente", "value": "Veículo estacionado irregularmente"},
                            {"label": "Veículo irregular", "value": "Veículo irregular"},
                        ],
                        id="vias-publicas-checklist",
                        inline=False
                    ),
                ],
                style={"width": "100%"}
            ),
            html.Br(),
            dbc.DropdownMenu(
                label="Outros",
                toggle_style={
                    "color": "#717171",
                    "background": "#fff",
                    "width": "100%",
                    "textTransform": "none",
                    "text-align": 'left'
                },
                children=[
                    dbc.Checklist(
                        options=[
                            {"label": "Bueiro", "value": "Bueiro"},
                            {"label": "Pedestre", "value": "Pedestre"},
                            {"label": "Placa de veículo", "value": "Placa de veículo"},
                        ],
                        id="outros-checklist",
                        inline=False
                    ),
                ],
                style={"width": "100%"}
            ),
            html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),html.Br(),
        ]),
    ]
)'''


sidebar_left = dbc.Col(
    style=sidebar_left_style,
    xs=12, sm=6, md=5, lg=4, xl=3,
    children=[
        html.Div(
            style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'height': '100%'},
            children=[
                html.Img(src="dashboard/assets/logo.png", height="auto", style={'max-height': '100%', 'max-width': '100%', 'vertical-align': 'middle'})
            ]
        ),
        html.Br(),
        
    ]
)


@app.callback(
    
    Output('results-div', 'children'),
    [Input('asfalto-checklist', 'value'),
     Input('sinalizacao-checklist', 'value'),
     Input('vias-publicas-checklist', 'value'),
     Input('outros-checklist', 'value')]
)
def update_results(asfalto, sinalizacao, vias_publicas, outros):
    # Make API call here
    filters = {
        'asfalto': asfalto,
        'sinalizacao': sinalizacao,
        'vias_publicas': vias_publicas,
        'outros': outros
    }
    

    print("Filters:", filters)
    # Example API call
    response = requests.post('http://127.0.0.1:5000/filtro', json=filters)
    data = response.json()
    
    # Process the data and create the results to display
    results = []
    for item in data:
        results.append(html.Div(f"{item['type']}: {item['description']}"))
    
    return results
# Função para criar um card
# Função para criar um card
def create_card(title, *contents):
    card_body = html.Div([
        html.H4(title, className="card-title")
    ])
    for content in contents:
        card_body.children.append(content)
    return dbc.Card(
        dbc.CardBody(card_body),
        className="mt-3",
        style={'marginBottom': '20px', 'borderRadius': '15px'}  # Remover a cor da borda
    )

def create_feed(title, content, progress_value):
    progress_bar = dbc.Progress(value=progress_value, striped=True, className="mt-3")
    content_with_progress = html.Div([
        html.H4(title, className="card-title"),
        content,
        progress_bar
    ])
    return dbc.Card(
        dbc.CardBody(content_with_progress),
        className="mt-3",
        style={'marginBottom': '20px', 'borderRadius': '15px', 'border':'1px solid #d2d2d2', 'height': '615%'}  # Remover a cor da borda
    )
# Função para criar um gráfico de barras
def create_bar_chart(data):
    tipo_intercorrencias = [item[0] for item in data]
    quantidade_intercorrencias = [item[1] for item in data]

    data = [go.Bar(
        x=tipo_intercorrencias,
        y=quantidade_intercorrencias
    )]
    layout = go.Layout(title="",paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return dcc.Graph(
        figure={'data': data, 'layout': layout},
        style={'height': '40vh', 'background-color': 'rgba(0, 0, 0, 0)'}  # Adiciona estilo para remover o fundo branco
    )
# Função para criar um gráfico de área
def create_map_card(map_url):
    return dbc.Card(
        dbc.CardBody([
            html.Iframe(src=map_url, width="100%", height="350")
        ]),
        className="mt-3",
        style={'marginTop': '0', 'height': '40vh'}
    )

def create_area_chart():
    id =   'pie-chart'
    labels = ['Buraco', 'Placa Quebrada', 'Veiculos Estacionados Irregularmente','Árvore em Fiação']
    values = [4500, 2500, 1053, 500]
    
    data = [go.Pie(
        labels=labels,
        values=values,
        hole=0.3
    )]
    layout = go.Layout(title="",paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return dcc.Graph(figure={'data': data, 'layout': layout}, style={'height': '40vh', 'margin-top':'-45px'})

def create_card_with_button(title, content, button_text, button_callback):
    card_body = html.Div([
        html.H4(title, className="card-title"),
        content,
        dbc.Button(button_text, id="open-offcanvas-scrollable", color="#9b559c", className="mr-2", style={'background-color': 'white', 'color': '#4a4a4a', 'border':'1px solid #4a4a4a'})

    ])
    return dbc.Card(
        dbc.CardBody(card_body),
        className="mt-3",
        style={'marginBottom': '20px', 'borderRadius': '15px'}
    )

def create_speed_chart():
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=50,  # Defina o valor inicial aqui
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge=dict(
            axis=dict(range=[0, 100]),  # Defina o intervalo desejado aqui
            bar=dict(color="black"),
            steps=[
                {'range': [0, 25], 'color': 'red'},
                {'range': [25, 50], 'color': 'yellow'},
                {'range': [50, 75], 'color': 'lightgreen'},
                {'range': [75, 100], 'color': 'green'},
            ],
            threshold=dict(
                line=dict(color="black", width=4),
                thickness=0.75,
                value=50
            )
        )
    ))
    fig.update_layout(height=335, width=230)  
    return dcc.Graph(figure=fig)

mapa = go.Figure(go.Scattermapbox(
    mode='markers',
    marker=dict(size=10, color='blue'),
    text=['']
))

mapa.update_layout(
    mapbox_style="open-street-map",  # ou "carto-positron", "carto-darkmatter", etc.
    showlegend=False,
    autosize=True,
    margin=dict(l=0, r=0, t=0, b=0)  # Ajustar margens conforme necessário
)


def create_totals_layout():
    return html.Div([
        dbc.Row([
            # Card de Relatório
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4("Relatório", className="card-title"),
                    dbc.Row([
                        dbc.Col(dbc.Input(id='input-date', placeholder="Data", type="date", style={'width': '100%'}), xs=12, md=3, className="mb-2"),
                        dbc.Col(dbc.Input(id='input-rua', placeholder="Rua", type="text", style={'width': '100%'}), xs=12, md=3, className="mb-2"),
                        dbc.Col(dbc.Input(id='input-bairro', placeholder="Bairro", type="text", style={'width': '100%'}), xs=12, md=3, className="mb-2"),
                        dbc.Col(html.Div([
                            dbc.Button(html.I(className="bi bi-search"), id='search-button', style={'margin-right': '2%'}, color='#9b559c', className="btn-icon"),
                            dbc.Button(html.I(className="bi bi-file-earmark-pdf"), id='pdf-button', style={'margin-right': '2%'}, color='white', className="btn-icon"),
                            dbc.Button(html.I(className="bi bi-file-earmark-excel"), color='white', className="btn-icon"),
                        ]), xs=12, md=3, className="mb-2"),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H4("Histórico de Ocorrências", className="card-title"),
                                    dbc.Table([
                                        html.Thead(html.Tr([
                                            html.Th("Ocorrências"),
                                            html.Th("Rua"),
                                            html.Th("Bairro"),
                                            html.Th("Data"),
                                            html.Th("Ações")
                                        ])),
                                        html.Tbody(id='table-body', style={'height': '100%'}),
                                    ])
                                ]),
                                className="h-100",
                                style={"max-height": "calc(90vh - 160px)", "overflow-y": "auto"}
                            ),
                            xs=12, md=12, className="h-100"
                        ),
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col(
                            dbc.Pagination(id='pagination', max_value=5, fully_expanded=False, first_last=True, previous_next=True),
                            width={"size": 12, "offset": 5},
                            className="mb-2"
                        )
                    ]),
                ]),
            ], className="h-100", style={"max-height": "calc(100vh - 100px)", "overflow": "hidden"}), width=8),  # Ajuste a largura da coluna para 8

            # Card de Mapa
            dbc.Col(html.Div(
                [
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Mapa", className="card-title"),
                            dcc.Graph(id='mapa', config={'responsive': True}, style={'height': '500px', 'width': '100%'}, className="card-map"),  # Altura fixa, largura 100%
                        ], className="card-map-container"),
                    ], className="h-100"),
                    html.Br(),
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Carousel(
                                id='carousel-images',
                                items=[],  # Os itens serão carregados dinamicamente
                                controls=True,
                                indicators=True,
                                interval=3000,
                                ride="carousel",
                                style={'height': '455px'}
                            )
                        ]),
                    ], className="h-100"),
                ],
                id='map-container',  # Identificador para a visibilidade condicional
                style={'display': 'none'}  # Inicialmente escondido
            ), width=4)  # Ajuste a largura da coluna para 4
        ]),
        dcc.Store(id='store', storage_type='memory'),  # Armazenamento temporário dos dados
        dcc.Download(id="download-pdf")
    ], className="container-fluid")

@app.callback(
    [Output('table-body', 'children'),
     Output('mapa', 'figure'),
     Output('pagination', 'max_value'),
     Output('map-container', 'style'),
     Output('carousel-images', 'items')],
    [Input('search-button', 'n_clicks'),
     Input('pagination', 'active_page'),
     Input({'type': 'btn-doc', 'index': ALL}, 'n_clicks')],
    [State('input-date', 'value'),
     State('input-rua', 'value'),
     State('input-bairro', 'value'),
     State({'type': 'btn-doc', 'index': ALL}, 'id')]
)
def update_table_and_map(search_n_clicks, active_page, doc_clicks, date_value, rua_value, bairro_value, doc_ids):
    # Dados padrão para o carregamento inicial
    if search_n_clicks is None and active_page is None:
        active_page = 1
        date_value = date_value or '2024-01-01'
        rua_value = rua_value or ''
        bairro_value = bairro_value or ''

    filtered_id = None
    if doc_clicks:
        ctx = dash.callback_context
        if ctx.triggered:
            filtered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            filtered_id = filtered_id.split(':')[1] if filtered_id else None

    if filtered_id:
        api_url = f"http://127.0.0.1:5000/filtro/{filtered_id}"
        page_size = 1  # Somente uma ocorrência
    else:
        api_url = "http://127.0.0.1:5000/filtro"
        page_size = 36

    data = {
        'date': date_value,
        'rua': rua_value,
        'bairro': bairro_value,
        'page': active_page or 1,
        'page_size': page_size
    }

    response = requests.post(api_url, json=data)

    if response.status_code == 200:
        data = response.json()
        total_records = data.get('total', 0)
        rows = []
        markers = []
        carousel_items = []

        for idx, ocorrencia in enumerate(data['records']):
            rows.append(html.Tr([
                html.Td(ocorrencia.get('ocorrencia', '')),
                html.Td(ocorrencia.get('rua', '')),
                html.Td(ocorrencia.get('bairro', '')),  
                html.Td(ocorrencia.get('data', '')),
                html.Td(ocorrencia.get('id', ''), style={'display': 'none'}),
                html.Td(html.Div([
                    dbc.Button(html.I(className="bi bi-card-list"), id=f'btn-doc-{idx}', color="link", className="btn-icon"),
                    dbc.Button(
                        html.I(className="bi bi-images"),
                        id=f'btn-img-{idx}',
                        color="link",
                        className="btn-icon",
                        href=f"https://carros.meumunicipio.online/{ocorrencia.get('imagem', '')}"
                    ),
                ], className="d-flex justify-content-around"))
            ]))

            coordenadas = eval(ocorrencia.get('coordenadas', ''))
            if coordenadas:
                markers.append(dict(
                    lat=coordenadas[0],
                    lon=coordenadas[1],
                    name=ocorrencia.get('ocorrencia', ''),
                    marker=dict(size=12)
                ))
            if 'imagem' in ocorrencia and ocorrencia['imagem']:
                if isinstance(ocorrencia['imagem'], str):
                    img_urls = ocorrencia['imagem'].split(',')
                elif isinstance(ocorrencia['imagem'], list):
                    img_urls = ocorrencia['imagem']
                else:
                    img_urls = []

                for idx, img_url in enumerate(img_urls):
                    carousel_items.append({
                        'key': f"carousel-img-{idx}-{img_url}",
                        'src': f"https://carros.meumunicipio.online/{img_url}",
                        'alt': f"Imagem {idx}",
                    })
        map_layout = go.Layout(
            height=1000,
            mapbox=dict(
                style="open-street-map",
                zoom=10,
                center=dict(
                    lat=markers[0]['lat'] if markers else -23.5505,
                    lon=markers[0]['lon'] if markers else -46.6333
                ),
            ),
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        map_figure = go.Figure(layout=map_layout)

        if markers:
            map_figure.add_trace(go.Scattermapbox(
                lat=[marker['lat'] for marker in markers],
                lon=[marker['lon'] for marker in markers],
                mode='markers',
                marker=dict(size=14, color='red', opacity=0.7),
                text=[marker['name'] for marker in markers]
            ))

        total_pages = math.ceil(total_records / page_size) if not filtered_id else 1
        return rows, map_figure, total_pages, {'display': 'block'}, carousel_items

    else:
        return [html.Tr([html.Td("Erro ao buscar dados", colSpan=5)])], go.Figure(), 1, {'display': 'none'}, []

def create_settings_layout():
    options = get_ocorrencias()
    mid = len(options) // 2
    options_col1 = options[:mid]
    options_col2 = options[mid:]

    modal = html.Div(
        [
            dbc.Button("Editar", id="open-centered"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Ocorrências Priorizadas"), close_button=True),
                    dbc.ModalBody(
                        [
                            dbc.Label("Selecione 3 ocorrências nas quais deseja priorizar"),
                            dbc.Select(
                                id="select1",
                                placeholder="Selecione a primeira ocorrência",
                                options=options,
                            ),
                            html.Br(),
                            dbc.Select(
                                id="select2",
                                placeholder="Selecione a segunda ocorrência",
                                options=options,
                            ),
                            html.Br(),
                            dbc.Select(
                                id="select3",
                                placeholder="Selecione a terceira ocorrência",
                                options=options,
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Priorizar",
                            id="close-centered",
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id="modal-centered",
                centered=True,
                is_open=False,
                className="custom-modal"
            ),
        ]
    )

    return html.Div([
        dbc.Row([
            dbc.Col(
                create_card("Priorização",
                            dbc.Label('Percurso'),
                            dbc.Checklist(
                                options=[
                                    {"label": "Rotas definidas", "value": 1, "disabled": True},
                                    {"label": "Arrecadação de IPTU", "value": 2, "disabled": True},
                                    {"label": "Algoritmo Urban", "value": 3,"disabled": False},
                                ],
                                value=[3],
                                id="switches-input",
                                switch=True,
                            ),
                            html.Br(),

                            dbc.Label("Ocorrências"),
                            dbc.ListGroup(
                                    [
                                        dbc.ListGroupItem(
                                            item['label'],
                                            id=f"item-{item['value']}"
                                        ) for item in get_data_from_api()
                                    ],
                                    id="list-group-col1"
                                ),
                            html.Br(),
                            modal
                ),
                width={"size": 4, "order": 1, "offset": 0}
            ),
            dbc.Col(
                create_card("Itens Ativos",
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Checklist(
                                            options=options_col1,
                                            value=[1],
                                            id="switches-input-col1",
                                            switch=True,
                                        ),
                                        width=6  # Metade da largura da linha
                                    ),
                                    dbc.Col(
                                        dbc.Checklist(
                                            options=options_col2,
                                            value=[1],
                                            id="switches-input-col2",
                                            switch=True,
                                        ),
                                        width=6  # Metade da largura da linha
                                    ),
                                ]
                            )
                ),
                width={"size": 8, "order": 2, "offset": 0}
            ),
        ]),
        dbc.Row([
            dbc.Col(
                create_card("Adicionar Nova Rota",
                            dbc.Label("Adicionar nova rota:"),
                            dbc.Col([
                                create_generic_map2(),  # Mapa ocupando 10 colunas
                                html.Br(),
                                html.Br(),
                                dbc.Row([
                                    dbc.Col(html.Div([html.Button("Adicionar nova Rota", id="meu-botao", className="btn btn-  text-center")]), width={"size": 2, "offset": 5})  # Botão ocupando 2 colunas e alinhado ao centro
                                ])
                            ], width=12)
                ),
            ),
        ]),
       
        # Para controlar o layout
        html.Div(id='page-content')
    ])

def create_parametros_layout():
    options = get_ocorrencias()
    mid = len(options) // 2
    options_col1 = options[:mid]
    options_col2 = options[mid:]

    modal = html.Div(
        [
            dbc.Button("Editar", id="open-centered"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Ocorrências Priorizadas"), close_button=True),
                    dbc.ModalBody(
                        [
                            dbc.Label("Selecione 3 ocorrências nas quais deseja priorizar"),
                            
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Priorizar",
                            id="close-parametros",
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id="modal-parametros",
                centered=True,
                is_open=False,
                className="custom-modal"
            ),
        ]
    )

    return html.Div([
        dbc.Row([
            dbc.Col(
                create_card("Priorização",
                            dbc.Label('Percurso'),
                            dbc.Checklist(
                                options=[
                                    {"label": "Rotas definidas", "value": 1, "disabled": True},
                                    {"label": "Arrecadação de IPTU", "value": 2, "disabled": True},
                                    {"label": "Algoritmo Urban", "value": 3,"disabled": False},
                                ],
                                value=[3],
                                id="switches-input",
                                switch=True,
                            ),
                            html.Br(),

                            dbc.Label("Ocorrências"),
                            dbc.ListGroup(
                                [
                                    dbc.ListGroupItem("1 - Buraco"),
                                    dbc.ListGroupItem("2 - Mato Alto"),
                                    dbc.ListGroupItem("3 - Árvore em fiação"),
                                ],
                                flush=True,
                            ),
                            html.Br(),
                            modal
                ),
                width={"size": 4, "order": 1, "offset": 0}
            ),
            dbc.Col(
                create_card("Itens Ativos",
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Checklist(
                                            options=options_col1,
                                            value=[1],
                                            id="switches-input-col1",
                                            switch=True,
                                        ),
                                        width=6  # Metade da largura da linha
                                    ),
                                    dbc.Col(
                                        dbc.Checklist(
                                            options=options_col2,
                                            value=[1],
                                            id="switches-input-col2",
                                            switch=True,
                                        ),
                                        width=6  # Metade da largura da linha
                                    ),
                                ]
                            )
                ),
                width={"size": 8, "order": 2, "offset": 0}
            ),
        ]),
        dbc.Row([
            dbc.Col(
                create_card("Adicionar Nova Rota",
                            dbc.Label("Adicionar nova rota:"),
                            dbc.Col([
                                create_generic_map2(),  # Mapa ocupando 10 colunas
                                html.Br(),
                                html.Br(),
                                dbc.Row([
                                    dbc.Col(html.Div([html.Button("Adicionar nova Rota", id="meu-botao", className="btn btn-  text-center")]), width={"size": 2, "offset": 5})  # Botão ocupando 2 colunas e alinhado ao centro
                                ])
                            ], width=12)
                ),
            ),
        ]),
       
        # Para controlar o layout
        html.Div(id='page-content')
    ])

def create_maps_layout():
    return html.Div([
        dbc.Row([
            dbc.Col(
                                create_map(get_coordenadas()),  # Mapa ocupando 10 colunas
                                
                            
            ),
        ]),
       
        # Para controlar o layout
        html.Div(id='page-content')
    ])


def create_card_chamados(title, content=None):
    def create_kanban_column(title, items):
        # Definindo as cores com base no título
        if title == "Aguardando":
            header_style = {"backgroundColor": "#cd2b2329","font-size": "18px"}  # Vermelho
        elif title == "Em Andamento":
            header_style = {"backgroundColor": "#ffbf0026", "font-size": "18px"}  # Amarelo
        elif title == "Finalizados":
            header_style = {"backgroundColor": "#007bff14", "font-size": "18px"}  # Azul
        elif title == "Concluídos":
            header_style = {"backgroundColor": "#4caf503b", "font-size": "18px"}  # Verde
        return dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        title,
                        style={
                            **header_style,
                            "borderTopLeftRadius": "10px",
                            "borderTopRightRadius": "10px"
                        }
                    ),
                    dbc.CardBody(
                        [html.Div(item, className="kanban-item") for item in items],
                        className="kanban-column-body h-100"
                    ),
                ],
                className="kanban-column rounded-card h-100",
                style={"marginTop": "15px"}  # Aqui você adiciona a margem superior
            ),
            width=3,
            style={"height": "80vh"},
        )
    kanban_content = dbc.Row(
        [
            create_kanban_column("Aguardando", ["Chamado 1", "Chamado 2"]),
            create_kanban_column("Em Andamento", ["Chamado 3"]),
            create_kanban_column("Finalizados", ["Chamado 4", "Chamado 5"]),
            create_kanban_column("Concluídos", ["Chamado 6", "Chamado 7"])
        ],
        className="kanban-board h-100"
    )

    card_content = kanban_content if content is None else content
                                
    return card_content
def create_responsaveis_table():
    data = [
        {"Nome": "João Silva", "Departamento": "TI", "Contato": "joao.silva@example.com"},
        {"Nome": "Maria Souza", "Departamento": "Financeiro", "Contato": "maria.souza@example.com"},
        {"Nome": "Carlos Oliveira", "Departamento": "RH", "Contato": "carlos.oliveira@example.com"},
    ]

    columns = [
        {"name": "Nome", "id": "Nome"},
        {"name": "Departamento", "id": "Departamento"},
        {"name": "Contato", "id": "Contato"},
    ]

    # Cabeçalhos das colunas como um card separado
    header_card = dbc.Card(
        dbc.Row([
            dbc.Col(html.Div(columns[0]["name"], className="custom-header-text first-column-margin")),
            *[dbc.Col(html.Div(col["name"], className="custom-header-text")) for col in columns[1:]]
        ]),
        className="table-card mb-2 border-0",
        style={"height": "50px"}
    )

    # Linhas de dados como um único card
    data_rows = []
    for row in data:
        data_row = dbc.Row([
            dbc.Col(html.Div(row[col["id"]], className="card-row-table")) for col in columns
        ])
        data_rows.append(data_row)

    data_card = dbc.Card(
        dbc.CardBody(data_rows, className="border-0"),
        className="card-body-table mb-2 border-0"
    )

    return html.Div([header_card, data_card], className="mb-2")
def create_new_cadastro_modal():
    modal = html.Div(
        [
            dbc.Button("Novo Cadastro", id="open-modal", color="#9b559c", className="ml-8"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Novo Cadastro")),
                    dbc.ModalBody(
                        [
                            dbc.Row([
                                dbc.Col([
                                    dbc.Input(type="text", id="input-setor", placeholder="Informe o setor"),
                                ]),
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Input(type="text", id="input-nome", placeholder="Informe o nome"),
                                ]),
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Input(type="text", id="input-documento", placeholder="Informe o documento (CPF/CNPJ)"),
                                ]),
                            ]),
                            dbc.Row([    
                                dbc.Col([
                                    dbc.Input(type="email", id="input-contato", placeholder="Informe o email"),
                                ]),
                            ]),
                            html.Div(
                                [
                                    dbc.Label("Selecione o tipo de acesso"),
                                    dbc.RadioItems(
                                        options=[
                                            {"label": "Administração", "value": "admin"},
                                            {"label": "Relatório", "value": "relatorio"},
                                        ],
                                        id="radio-options",
                                        inline=True,
                                    ),
                                ],
                                id="additional-options",
                                style={"display": "none"},  # Inicialmente oculto
                            ),
                            html.Br(),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Selecione a(s) ocorrência(s)"), 
                                ]),
                            ]),
                            dbc.Row([
                                dbc.Col(
                                    dbc.Checklist(
                                        options=get_data_from_api(),
                                        value=[1],
                                        id="switches-input-col1",
                                        switch=True,
                                    ),
                                ),        
                            ]),
                        ]
                    ),
                    html.Br(),
                    dbc.ModalFooter([
                        dbc.Button("Salvar", id="close-modal", className="ms-auto")
                    ]),
                ],
                id="modal",
                is_open=False,
                className="custom-modal"
            ),
        ]
    )

    return modal

def create_protocol_layout():
    options = [
        {"label": "Afundamento", "value": 1},
        {"label": "Alerta de Pavimentação Danificado", "value": 2},
        {"label": "Arbusto em Fiação", "value": 3},
        {"label": "Bueiro", "value": 4},
        {"label": "Buraco", "value": 5},
        {"label": "Corrugação", "value": 6},
        {"label": "Desgaste", "value": 7},
        {"label": "Desnível", "value": 8},
        {"label": "Faixa pedestre", "value": 9},
        {"label": "Faixa pedestre danificada", "value": 10},
        {"label": "Fissura", "value": 11},
        {"label": "Guard rail", "value": 12},
        {"label": "Guard rail danificado", "value": 13},
        {"label": "Lixo", "value": 14},
        {"label": "Mato alto", "value": 15},
        {"label": "Pedestre", "value": 16},
        {"label": "Placa de trânsito", "value": 17},
        {"label": "Placa de trânsito danificada ", "value": 18},
        {"label": "Placa de trânsito encoberta", "value": 19},
        {"label": "Placa veículo", "value": 20},
        {"label": "Remendo", "value": 21},
        {"label": "Semáforo", "value": 22},
        {"label": "Trinca bloco", "value": 23},
        {"label": "Trinca bordo", "value": 24},
        {"label": "Trinca fadiga", "value": 25},
        {"label": "Trinca isolada", "value": 26},
        {"label": "Veículo estacionado irregularmente", "value": 27},
        {"label": "Veículo irregular", "value": 28},
    ]

    mid = len(options) // 2
    options_col1 = options[:mid]
    options_col2 = options[mid:]

    modal = html.Div(
        [
            dbc.Button("Editar", id="open-centered"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Ocorrências Priorizadas"), close_button=True),
                    dbc.ModalBody(
                        [
                            dbc.Label("Selecione as ocorrências nas quais deseja priorizar"),
                            dbc.Select(
                                id="select1",
                                placeholder="Selecione a primeira ocorrência",
                                options=options,
                            ),
                            html.Br(),
                            dbc.Select(
                                id="select2",
                                placeholder="Selecione a segunda ocorrência",
                                options=options,
                            ),
                            html.Br(),
                            dbc.Select(
                                id="select3",
                                placeholder="Selecione a terceira ocorrência",
                                options=options,
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Priorizar",
                            id="close-centered",
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id="modal-centered",
                centered=True,
                is_open=False,
            ),
        ]
    )
    print (return_acesso())
    if return_acesso()== 'adm' or return_acesso()=='full':
        print(request.json.get('access_type', 'externo'))
        return dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(create_card_chamados("Chamados"), label="Quadro de Chamados", tab_style={"height": "100%"}),
                                    dbc.Tab(
                                        html.Div(
                                                [
                                                    create_responsaveis_table(),
                                                    create_new_cadastro_modal()  # Adiciona o modal e o botão aqui
                                                    
                                                ]
                                            ), label="Responsáveis", tab_style={"height": "100%"}
                                    ),
                                ],
                            ),
                            html.Br(),
                            html.Br(),  # Adiciona uma quebra de linha aqui
                            html.Div(id="kanban-or-table-content")  # Div para o conteúdo do Kanban ou Tabela
                        ]
                    ),
                    style={"height": "90vh"}
                ),
                width={"size": 12, "order": 1, "offset": 0}
            ),
            style={"height": "90vh"}
        )

                
    else:
        return dbc.Row(
    dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.Tabs(
                        [
                            dbc.Tab(create_card_chamados("Chamados"), label="Quadro de Chamados", tab_style={"height": "100%"}),    
                        ],
                    ),
                    html.Br(),
                    html.Br(),  # Adiciona uma quebra de linha aqui
                    html.Div(id="kanban-or-table-content")  # Div para o conteúdo do Kanban ou Tabela
                ]
            ),
            style={"height": "90vh"}
        ),
        width={"size": 12, "order": 1, "offset": 0}
    ),
    style={"height": "90vh"}
)

        


            

def create_reporter_layout():

    print ('caiu aqui')
    return html.Div([
       
                html.H4("Mensagem", className="card-title"),
                html.P("Oi", className="card-text")
        ], className="mt-4")
  
# Callback para atualizar o layout dinamicamente
@app.callback(
    Output('page-content', 'children'),
    Input('radioitems-input', 'value')
)
def update_output(selected_theme):
    # Atualiza o layout para refletir o novo tema
    return dbc.Container(
        html.Div([
            html.H1('Tema atualizado para: {}'.format(selected_theme)),
            html.P('Esta página está usando o tema {}'.format(selected_theme))
        ]),
        className="p-5",
        app = dash.Dash(__name__, external_stylesheets=[
        dbc.themes.DARKLY, ], suppress_callback_exceptions=True) # Claro
    )

# Callback para atualizar o tema dinamicamente
@app.callback(
    Output('theme', 'href'),
    Input('radioitems-input', 'value')
)
def update_theme(selected_theme):
    print(selected_theme)
    return selected_theme

# Adiciona um link de estilo ao layout inicial para aplicar o tema


@app.callback(
    Output('salvar-rota-feedback', 'children'),
    [Input('salvar-rota-button', 'n_clicks')],
    [State('mapa', 'selected_routes')]
)
def salvar_rota_no_banco_de_dados(n_clicks, selected_routes):
    if n_clicks > 0 and selected_routes:
        # Aqui você deve implementar a lógica para salvar as coordenadas da rota no banco de dados
        # Por exemplo, você pode usar SQLAlchemy ou outra biblioteca ORM para interagir com o banco de dados
        # Depois de salvar as coordenadas, você pode retornar uma mensagem de confirmação para o usuário
        # Exemplo:
        # save_route_to_database(selected_routes)
        # return html.Div('Rota selecionada foi salva no banco de dados.')
        pass  # Remova isso após implementar a lógica de salvamento

# Substitua "save_route_to_database" pela função real que salva a rota no banco de dados

# Callback para atualizar o mapa com a rota selecionada
@app.callback(
    Output('mapa-visualizacao', 'children'),
    [Input('salvar-rota-button', 'n_clicks')],
    [State('mapa', 'selected_routes')]
)
def atualizar_mapa(n_clicks, selected_routes):
    m = folium.Map(location=[-23.5505, -46.6333], zoom_start=10)  # Coordenadas de São Paulo

    # Adiciona a funcionalidade de seleção de rota ao mapa
    route_plugin = plugins.MeasureControl(primary_length_unit='kilometers')
    m.add_child(route_plugin)

    # Verifica se há uma rota selecionada e a desenha no mapa
    if selected_routes:
        for route in selected_routes:
            folium.PolyLine(locations=route['geometry']['coordinates'], color='blue').add_to(m)

    return html.Iframe(srcdoc=m._repr_html_(), width='100%', height='600')


def create_speed_chart2():
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=270,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Speed"}
    ))
    fig.update_layout(height=500, width=270)  
    return dcc.Graph(figure=fig)

def create_table(rows, columns):
    table_header = [
        html.Th(f'Col {col}') for col in range(1, columns + 1)
    ]
    
    table_body = []
    for row in range(1, rows + 1):
        table_row = html.Tr([
            html.Td(f'Row {row}, Col {col}') for col in range(1, columns + 1)
        ])
        table_body.append(table_row)

    return dbc.Table(
        html.Thead(html.Tr(table_header)),
        html.Tbody(table_body)
    )

def create_table_figure():
    fig = go.Figure(data=[go.Table(
        header=dict(values=['A Scores', 'B Scores'],
                    line_color='darkslategray',
                    fill_color='lightskyblue',
                    align='left'),
        cells=dict(values=[[100, 90, 80, 90], [95, 85, 75, 95]], 
                   line_color='darkslategray',
                   fill_color='lightcyan',
                   align='left'))
    ])
    return dcc.Graph(figure=fig, style={'height': '100%'})

# URLs de incorporação dos mapas do Google Maps
map_url_1 = "https://www.google.com/maps/embed/v1/place?q=Green+Valley+Office+Park+-+Avenida+Andrômeda+-+Alphaville,+Barueri+-+SP,+Brasil&key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8"
map_url_2 = "https://www.google.com/maps/embed/v1/place?q=Green+Valley+Office+Park+-+Avenida+Andrômeda+-+Alphaville,+Barueri+-+SP,+Brasil&key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8"


# Layout das colunas de cards
def create_card_with_link(title, content, link_id):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                html.P(dbc.Button(content, id=link_id, className="no-link-button", n_clicks=0)),
            
            ]
        )
    )

def create_modal(modal_id, title, content):
    return dbc.Modal(
        [
            dbc.ModalHeader(title),
            dbc.ModalBody(content),
            dbc.ModalFooter(
                dbc.Button("Fechar", id=f"close-{modal_id}", className="ml-auto", n_clicks=0)
            ),
        ],
        id=modal_id,
        size="lg",
        className="custom-modal"
    )

def create_dash_metabase():
    metabase_dashboard_url = "http://127.0.0.1:3000/public/dashboard/57c0888c-38a5-46b5-b488-ea44a32557ba"  # Substitua com a URL do seu dashboard
    return html.Div([
        html.Iframe(
            src=metabase_dashboard_url,
            style={
                "width": "100%",
                "height": "120vh",  # Ajustado para não ocupar toda a altura
                "border": "0",
                "position": "relative",  # Corrigido para permitir layout em colunas
                "overflow": "scroll",    # Adiciona o scroll ao iframe
                "-webkit-scrollbar": "10px",  # Customiza a largura do scroll (apenas para navegadores que suportam Webkit)
            },
        ),
    ], style={"position": "relative", "width": "100%", "height": "100vh"})

    # Div também ocupando a tela toda
def create_dashboard_tab_content():
    return html.Div([
        dbc.Row([
            dbc.Col(create_card_with_link("Intercorrências", get_numero_intercorrencia(), "link-intercorrencias"), xs=6, md=6, lg=3),
            dbc.Col(create_card_with_link("Ruas", get_ruas_percorridas(), "link-ruas"), xs=6, md=6, lg=3),
            dbc.Col(create_card_with_link("Bairros", get_bairros_percorridos(), "link-bairros"), xs=6, md=6, lg=3),
            dbc.Col(create_card_with_link("Quilometragem", ' 10', "link-quilometragem"), xs=6, md=6, lg=3),
            #dbc.Col(create_card_with_link("Chamados Abertos", get_total_requerementos(), "link-chamados-abertos"), xs=6, md=6, lg=2),
            #dbc.Col(create_card_with_link("Resolvidos", ' 10', "link-resolvidos"), xs=6, md=6, lg=2),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(create_card_with_button("Chamados Abertos", create_area_chart(), "Saiba Mais", "saiba-mais-button"), md=6),
                        dbc.Col(create_card("Tipo de Intercorrências", create_bar_chart(get_total_intercorrencias_por_tipo())), md=6),
                    ])
                ])
            ),
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Offcanvas(
                    html.P("Detalhes sobre processos abertos"),
                    id="offcanvas-scrollable",
                    title="Saiba mais",
                    is_open=False,
                    style={'width': '100%', 'background': '#f3f3f3'}
                )
            ),
        ]),
        dbc.Row([
            dbc.Col(create_map(get_coordenadas()), xs=12, md=12, lg=12),
        ]),
        dbc.Row([
            dbc.Col(create_card("Ruas com Maior Número de Intercorrências", create_top_ruas_intercorrencias_chart(get_top_ruas_intercorrencias())), xs=12, md=6, lg=6),
            dbc.Col(create_card("Bairros com Maior Número de Intercorrências", create_top_bairros_intercorrencias_chart(get_top_bairros_intercorrencias())), xs=12, md=6, lg=6),        ]),
        # Adicionando modais
        create_modal("modal-intercorrencias", "Detalhes sobre Intercorrências",fetch_data_from_endpoint()),
        create_modal("modal-ruas", "Detalhes sobre Ruas", exibeRuas()),
        create_modal("modal-bairros", "Detalhes sobre Bairros", exibeBairros()),
        create_modal("modal-quilometragem", "Detalhes sobre Quilometragem", "Aqui estão mais informações sobre quilometragem..."),
        create_modal("modal-chamados-abertos", "Detalhes sobre Chamados Abertos", "Aqui estão mais informações sobre chamados abertos..."),
        create_modal("modal-resolvidos", "Detalhes sobre Resolvidos", "Aqui estão mais informações sobre resolvidos..."),


        dbc.Modal(
    [
        dbc.ModalBody(html.Img(id="modal-image", style={"width": "100%"})),
        
    ],
    id="modal-image-display",
    size="xl",  # Define o tamanho como extra grande
    centered=True,
    is_open=False,  # Inicialmente fechado
    backdrop=True,  # Torna o fundo fosco
    style={"max-width": "100%", "height": "100vh"},
     # Ocupa a tela toda
)

        ], className="mt-3 custom-backdrop")

layout = None


def get_logged_in_user():
    return "Prefeitura Hipotética"

# URL da foto do usuário
user_photo_url = "https://upload.wikimedia.org/wikipedia/commons/2/22/Bras%C3%A3o_Santana_de_Parna%C3%ADba.png"  # substitua pelo URL da foto do usuário


@app.callback(
    Output("tab-content", "children"),
    Input("tabs-container", "active_tab"),
)


def render_tab_content(active_tab):
    if active_tab == "totals":
        layout = create_totals_layout()
        return layout
    elif active_tab == "settings":
        layout = create_settings_layout()
        return layout
    elif active_tab == "parametros":
        layout = create_parametros_layout()
        return layout
    elif active_tab == "maps":
        layout = create_maps_layout()
        return layout
    elif active_tab =='reporter':
       layout = create_reporter_layout()
    elif active_tab == "protocols":
        layout = create_protocol_layout()
        return layout
    else:
        layout = create_dash_metabase()
        
        flag = 1
        return layout
    
if flag == 1:
    display_loading("dashboard")
    
    
edit_profile_modal = dbc.Modal(
    [
        dbc.ModalBody(
            [
                dbc.Row(
                    dbc.Col(
                        html.Img(src=user_photo_url, className="img-fluid rounded-circle", style={"width": "300px", "height": "300px"}),
                        width={"size": 4, "offset": 4}
                    ),
                    className="mb-3"
                ),
                dbc.Row(
                    dbc.Col(
                        [
                            dbc.Label(get_logged_in_user()),
                            html.Br(),
                            dbc.Button("Mudar Senha", id="open-change-password-fade", color="primary"),
                        ],
                        width=12,
                        style={"textAlign": "center"}
                    )
                ),
                dbc.Fade(
                    [
                        dbc.Label("Nova Senha"),
                        dbc.InputGroup(
                            [
                                dbc.Input(id="new-password-input", type="password"),
                                dbc.InputGroupText(
                                    dbc.Button("Mostrar", id="toggle-new-password-visibility", color="secondary", outline=True, size="sm"),
                                ),
                            ]
                        ),
                        dbc.Label("Confirmar Senha"),
                        dbc.InputGroup(
                            [
                                dbc.Input(id="confirm-password-input", type="password"),
                                dbc.InputGroupText(
                                    dbc.Button("Mostrar", id="toggle-confirm-password-visibility", color="secondary", outline=True, size="sm"),
                                ),
                            ]
                        ),
                        html.Div(id="password-validation-message", style={"color": "red"}),
                        dbc.Button("Fechar", id="close-change-password-fade", className="ml-auto")
                    ],
                    id="change-password-fade",
                    is_in=False,
                ),
            ]
        ),
        dbc.ModalFooter(
            dbc.Button("Fechar", id="close-edit-profile-modal", className="ml-auto")
        ),
    ],
    id="edit-profile-modal",
    size="lg",
    className="custom-modal"
)



app.layout = html.Div(
    className="row col-12",
    children=[
        # Sidebar
        html.Script(src='/_dash-component-suites/dash/dcc/async-graph.js'),
        html.Div(
            className="col-2",  
            children=[
                sidebar_left, 
                dcc.Store(id='access-type-store'),
                dcc.Store(id='selected-coordinates-store')
            ]
        ),
        # Conteúdo principal
        html.Div(
            className="col-10",  
            children=[
                dbc.Row(
                    [dbc.Col(
                        dbc.Tabs(
                            dbc.Tabs(id='tabs-container'),  # Aba ativa padrão
                        ),
                        width="11"
                    ),
                    dbc.Col(
        dbc.Tabs(
            [
                dbc.Tab(label="Perfil", tab_style={"height": "100%", "font-size": "20px", "margin-left": "46%"}, children=[
                    dbc.Button("Editar Perfil", id="open-edit-profile-modal", n_clicks=0),
                ]),
            ],
            id="profile-tab",
            active_tab=None,  # Nenhuma aba ativa por padrão
        ),
                    )],
                    align="right",
                ),
                dcc.Loading(id="loading", type="default", children=[html.Div(id="loading-output")]),
                # Espaçamento entre o Row e as Tabs
                html.Div(
                    id="tab-content",
                    children=[
                        html.Div(className="col-10", children=layout),  # layout ocupando 100% da largura
                    ]
                ),
            
            ]
        ),
        # Modals
        edit_profile_modal,
        
        # Script JavaScript para capturar cliques nos botões
        html.Script('''
        document.addEventListener('DOMContentLoaded', function() {
            function addClickEvent(buttonId) {
                document.getElementById(buttonId).onclick = function() {
                    var row = this.closest('tr');
                    var data = {
                        ocorrencia: row.cells[0].innerText,
                        rua: row.cells[1].innerText,
                        bairro: row.cells[2].innerText,
                        data: row.cells[3].innerText
                    };
                    fetch('http://127.0.0.1:5000/endpoint', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => response.json())
                    .then(result => console.log('Success:', result))
                    .catch(error => console.error('Error:', error));
                }
            }

            document.querySelectorAll('[id^=btn-doc-]').forEach(function(button) {
                addClickEvent(button.id);
            });
        });
        '''),
 dbc.Offcanvas(
        children=[

            html.Img(id='imagem_modal', src='', style={'width': '100%','height':'100%', 'display': 'block'})
        ],
        id="imagem_offcanvas",
        is_open=False,  # Inicialmente fechado
        placement="bottom",  # Lado direito
        scrollable=True,
        style={"width": "50%", "height": "50vh"} 
    )
])

# Callback para abrir e fechar o painel lateral
@app.callback(
    [Output("imagem_offcanvas", "is_open"),
     Output("imagem_modal", "src")],
    [Input("mapa", "clickData")],
    [State("imagem_offcanvas", "is_open")],
)
def toggle_offcanvas(clickData, is_open):
    if clickData:
        # Pega a URL da imagem dos dados do marcador clicado
        imagem_url = clickData['points'][0]['customdata']
        # Abre o painel lateral
        return True, imagem_url
    return is_open, ''
@app.callback(
    Output('tabs-container', 'children'),   
    Input('access-type-store', 'data')
)
def update_tabs(access_type):
    # Cria abas com base no tipo de acesso
    tabs = create_tabs(access_type = request.cookies.get('access_type'))
    print (tabs)
    return tabs

# Rota para definir o tipo de acesso no store
@server.route('/set_access_type', methods=['POST'])
def set_access_type():
    access_type = request.json.get('access_type', 'externo')
    # Atualiza o tipo de acesso no dcc.Store
    return jsonify({'status': 'success'}), 200



@app.callback(
    Output("edit-profile-modal", "is_open"),
    [Input("open-edit-profile-modal", "n_clicks"), Input("close-edit-profile-modal", "n_clicks")],
    [State("edit-profile-modal", "is_open")],
)
def toggle_modal(open_click, close_click, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == "open-edit-profile-modal":
        return True
    elif button_id == "close-edit-profile-modal":
        return False
    return is_open

@app.callback(
    Output("change-password-fade", "is_in"),
    [Input("open-change-password-fade", "n_clicks"), Input("close-change-password-fade", "n_clicks")],
    [State("change-password-fade", "is_in")],
)
def toggle_change_password_fade(n1, n2, is_in):
    if n1 or n2:
        return not is_in
    return is_in

@app.callback(
    Output("password-validation-message", "children"),
    [Input("new-password-input", "value"), Input("confirm-password-input", "value")],
)
def validate_password(new_password, confirm_password):
    if new_password and confirm_password:
        if new_password != confirm_password:
            return "As senhas não coincidem."
        else:
            return ""
    return ""

@app.callback(
    Output("new-password-input", "type"),
    [Input("toggle-new-password-visibility", "n_clicks")],
    [State("new-password-input", "type")],
)
def toggle_new_password_visibility(n, current_type):
    if n:
        return "text" if current_type == "password" else "password"
    return dash.no_update

@app.callback(
    Output("confirm-password-input", "type"),
    [Input("toggle-confirm-password-visibility", "n_clicks")],
    [State("confirm-password-input", "type")],
)
def toggle_confirm_password_visibility(n, current_type):
    if n:
        return "text" if current_type == "password" else "password"
    return dash.no_update

@app.callback(
    [Output('modal', 'is_open'),
    Output('additional-options', 'style')],
    [Input('open-modal', 'n_clicks'),
    Input('close-modal', 'n_clicks'),
    Input('input-contato', 'value')],
    [State('modal', 'is_open'),
    State('input-setor', 'value'),
    State('input-nome', 'value'),
    State('input-documento', 'value'),
    State('switches-input-col1', 'value'),
    State('radio-options', 'value')]
)
def handle_modal_and_save(open_clicks, close_clicks, contato, is_open, setor, nome, documento, ocorrencias, access_type):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Lógica para abrir e fechar o modal
    if triggered_id == "open-modal":
        return True, {'display': 'none'}  # Abre o modal e oculta as opções adicionais
    
    if triggered_id == "close-modal":
        if close_clicks:
            # Determina o tipo de acesso com base no email de contato
            tipo_acesso = access_type if access_type else "Administração"  # Padrão se não selecionado
            acesso = "prefeitura" if contato.endswith('@acaruiy.com.br') else "externo"
            
            # Prepare os dados para enviar para a API
            payload = {
                "setor": setor,
                "nome": nome,
                "documento": documento,
                "contato": contato,
                "ocorrencias": ocorrencias,
                "acesso": acesso,
                "tipo_acesso": tipo_acesso
            }
            
            print(payload)
            # Enviar dados para a API
            response = requests.post("http://127.0.0.1:5000/convidar", json=payload)
            
            if response.status_code == 200:
                print("Dados enviados com sucesso")
            else:
                print(f"Erro ao enviar dados: {response.status_code}")

        return False, {'display': 'none'}  # Fecha o modal e oculta as opções adicionais

    # Lógica para mostrar/ocultar opções adicionais
    if triggered_id == 'input-contato':
        if contato and contato.endswith('@acaruiy.com.br'):
            return is_open, {'display': 'block'}
        return is_open, {'display': 'none'}

    raise dash.exceptions.PreventUpdate
@app.callback(
    Output("table", "data"),
    [Input("save-button", "n_clicks")],
    [State("input-nome", "value"),
    State("input-departamento", "value"),
    State("input-contato", "value"),
    State("table", "data")],
)
def save_data(n_clicks, nome, departamento, contato, rows):
    if n_clicks:
        new_row = {"Nome": nome, "Departamento": departamento, "Contato": contato}
        rows.append(new_row)
    return rows

@app.callback(
    Output("modal-intercorrencias", "is_open"),
    [Input("link-intercorrencias", "n_clicks"), Input("close-modal-intercorrencias", "n_clicks")],
    [State("modal-intercorrencias", "is_open")],
)
def toggle_modal_intercorrencias(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("table-container-intercorrencias", "children"),
    Input("modal-intercorrencias", "is_open")
)
def update_table_intercorrencias(is_open):
    if is_open:
        return fetch_data_from_endpoint()
    return html.P("Clique no link para ver os detalhes.")

@app.callback(
    Output("modal-image-display", "is_open"),
    Output("modal-image", "src"),
    [Input({"type": "image-click", "index": dash.dependencies.ALL}, "n_clicks")],
    [State("modal-image-display", "is_open")]
)
def display_image_modal(n_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, ""
    
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    triggered_index = triggered_id.split(":")[1].strip('}"')
    image_src = f"https://carros.meumunicipio.online/{triggered_index}.png"
    return not is_open, image_src

@app.callback(
    Output("modal-ruas", "is_open"),
    [Input("link-ruas", "n_clicks"), Input("close-modal-ruas", "n_clicks")],
    [State("modal-ruas", "is_open")],
)
def toggle_modal_ruas(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal-bairros", "is_open"),
    [Input("link-bairros", "n_clicks"), Input("close-modal-bairros", "n_clicks")],
    [State("modal-bairros", "is_open")],
)
def toggle_modal_bairros(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal-quilometragem", "is_open"),
    [Input("link-quilometragem", "n_clicks"), Input("close-modal-quilometragem", "n_clicks")],
    [State("modal-quilometragem", "is_open")],
)
def toggle_modal_quilometragem(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal-chamados-abertos", "is_open"),
    [Input("link-chamados-abertos", "n_clicks"), Input("close-modal-chamados-abertos", "n_clicks")],
    [State("modal-chamados-abertos", "is_open")],
)
def toggle_modal_chamados_abertos(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal-resolvidos", "is_open"),
    [Input("link-resolvidos", "n_clicks"), Input("close-modal-resolvidos", "n_clicks")],
    [State("modal-resolvidos", "is_open")],
)
def toggle_modal_resolvidos(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output('output-div', 'children'),
    [
        Input('asfalto-checklist', 'value'),
        Input('sinalizacao-checklist', 'value'),
        Input('vias-publicas-checklist', 'value'),
        Input('outros-checklist', 'value'),
    ]
)
def update_output(asfalto_values, sinalizacao_values, vias_publicas_values, outros_values):
    selected_values = []
    if asfalto_values:
        selected_values.extend(asfalto_values)
    if sinalizacao_values:
        selected_values.extend(sinalizacao_values)
    if vias_publicas_values:
        selected_values.extend(vias_publicas_values)
    if outros_values:
        selected_values.extend(outros_values)

    return html.Div([
        html.H4("Selected Values:"),
        html.Pre(str(selected_values))
    ])

@app.callback(
    Output('selected-data', 'children'),
    Input('generic-map', 'selectedData')
)
def display_selected_data(selectedData):
    if selectedData is None:
        return "No data selected"
    return json.dumps(selectedData, indent=2)

@app.callback(
    Output('interval-component', 'disabled'),
    Input('selected-coordinates-store', 'data'),
    State('selected-coordinates-store', 'data')
)
def trigger_alert(new_data, old_data):
    if new_data and new_data != old_data:
        coordinates_str = ', '.join([f"Lat: {lat}, Lon: {lon}" for lat, lon in new_data])
        alert_script = f'alert("Selected Coordinates: {coordinates_str}");'
        return False, dash.no_update, alert_script
    return True, dash.no_update, dash.no_update



def fetch_data_from_endpoint():    
    response = requests.get("http://127.0.0.1:5000/ocorrencia")
    if response.status_code == 200:
        data = response.json()
        table_header = html.Thead(html.Tr([
            html.Th("Ocorrência", className="card-body-table first-column-margin"),
            html.Th("Rua", className="card-body-table"),
            html.Th("Bairro", className="card-body-table"),
            html.Th("Data", className="card-body-table"),
        ]))
        
        table_body = html.Tbody([
            html.Tr([
                html.Td(row[1]),
                html.Td(row[5]),
                html.Td(row[6]),
                html.Td(row[4]),
                
            ]) for row in data
        ])
        
        table = dbc.Table([table_header, table_body], bordered=True, hover=True, striped=True, responsive=True)
        return table
    return html.P("Erro ao carregar dados do endpoint.")


def exibeRuas():    
    response = requests.get("http://127.0.0.1:5000/ruas")
    if response.status_code == 200:
        data = response.json()
        table_header = html.Thead(html.Tr([
            html.Th("Rua", className="card-body-table"),
            html.Th("Bairro", className="card-body-table"),
            html.Th("Número de Ocorrências", className="card-body-table"),
        ]))
        
        table_body = html.Tbody([
            html.Tr([
                html.Td(row['ruaIntercorrencia']),
                html.Td(row['bairroIntercorrencia']),
                html.Td(row['count(tipoIntercorrencia)']),
                
            ]) for row in data
        ])
        
        table = dbc.Table([table_header, table_body], bordered=True, hover=True, striped=True, responsive=True)
        return table
    return html.P("Erro ao carregar dados do endpoint.")

def exibeBairros():    
    response = requests.get("http://127.0.0.1:5000/bairros")
    if response.status_code == 200:
        data = response.json()
        table_header = html.Thead(html.Tr([
            html.Th("Bairro", className="card-body-table"),
            html.Th("Número de Ruas", className="card-body-table"),
            html.Th("Número de Ocorrências", className="card-body-table"),
        ]))
        
        table_body = html.Tbody([
            html.Tr([
                
                html.Td(row['bairroIntercorrencia']),
                html.Td(row['count(distinct (ruaIntercorrencia))']),
                html.Td(row['count(tipoIntercorrencia)']),
                
            ]) for row in data
        ])
        
        table = dbc.Table([table_header, table_body], bordered=True, hover=True, striped=True, responsive=True)
        return table
    return html.P("Erro ao carregar dados do endpoint.")


@app.callback(
Output("modal-centered", "is_open"),
[Input("open-centered", "n_clicks"), Input("close-centered", "n_clicks")],
[State("modal-centered", "is_open"), State("select1", "value"), State("select2", "value"), State("select3", "value")],
)
def toggle_modal(n_open, n_close, is_open, value1, value2, value3):
    if n_close:  # If the close button is clicked
        # Prepare data to be sent to the API
        data = {
            "select1": value1,
            "select2": value2,
            "select3": value3
        }

        # Send data to the API
        response = requests.post("http://127.0.0.1:5000/priorizacao", json=data)

        # Check if the request was successful
        if response.status_code == 200:
            print("Data successfully sent to API.")
        else:
            print("Failed to send data to API.")

        # Close the modal
        return False

    if n_open:  # If the open button is clicked
        return not is_open

    return is_open

@app.callback(
    Output("modal-parametros", "is_open"),
    [Input("open-parametros", "n_clicks"), Input("close-parametros", "n_clicks")],
    [State("modal-parametros", "is_open"), State("select1", "value"), State("select2", "value"), State("select3", "value")],
)
def toggle_modal(n_open, n_close, is_open, value1, value2, value3):
    if n_close:  # If the close button is clicked
        # Prepare data to be sent to the API
        data = {
            "select1": value1,
            "select2": value2,
            "select3": value3
        }

        # Send data to the API
        response = requests.post("http://127.0.0.1:5000/priorizacao", json=data)

        # Check if the request was successful
        if response.status_code == 200:
            print("Data successfully sent to API.")
        else:
            print("Failed to send data to API.")

        # Close the modal
        return False

    if n_open:  # If the open button is clicked
        return not is_open

    return is_open


app.clientside_callback(
    """
    function(n_clicks, data) {
        if(n_clicks) {
            document.querySelectorAll("[id^='btn-doc']").forEach(button => {
                button.onclick = function() {
                    var row = button.closest('tr');
                    var imageLink = row.querySelector('a').href;  // Captura o link da imagem
                    var data = {
                        ocorrencia: row.cells[0].innerText,
                        rua: row.cells[1].innerText,
                        bairro: row.cells[2].innerText,
                        data: row.cells[3].innerText,
                        imagem: imageLink,  // Inclui o link da imagem no objeto data
                        id:row.cells[4].innerText
                    };

                    console.log('data:', data);  // Imprime o data no console

                    fetch('http://127.0.0.1:5000/action', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    })
                    .then(response => response.json())
                    .then(result => console.log('Success:', result))
                    .catch(error => console.error('Error:', error));
                }
            });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('store', 'data'),
    Input('table-body', 'children'),
    State('store', 'data')
)

@server.route('/dashboard')
def dashboard():
    # Recuperar cookies
    token = request.cookies.get('token')
    global access_type
    access_type = request.cookies.get('access_type')

    if not token or not access_type:
        return 'http://127.0.0.1:8052/'

    # Verificar e usar o token e o tipo de acesso
    if validate_token(token):
        return app.index()
    else:
        return "Token inválido, por favor faça login novamente.", 401
   

def validate_token(token):
    # Função para validar o token
    # Adicione aqui a lógica real de validação do token
    return True  # Simulando que o token é sempre válido para o exemplo

@server.route('/')
def index():
    return render_template('index.html')

# Rota Flask para renderizar o Dash

def return_acesso():
    return request.cookies.get('access_type')
if __name__ == "__main__":
    app.run(debug=False)
    
    

    

