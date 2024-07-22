from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import mysql.connector
from geopy.geocoders import Nominatim 
import googlemaps
from geopy.distance import geodesic
import requests
import os
import json

UPLOAD_FOLDER = r'C:\Users\milena.castilho\Desktop'
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Chave da API do Google Maps
google_maps_api_key = "AIzaSyBKx5VFEjGbTnIP0JJCwfUF-RMLbDNX_YE"

# Inicialização do cliente do Google Maps
gmaps = googlemaps.Client(key=google_maps_api_key)

# Função para 
# conectar ao banco de dados
token_info = {
    'token': None,
    'valid': False
}
token = None

@app.route('/total_requerimentos', methods=['GET'])
def total_requerimentos():
    try:
        url = "https://gatewayqa.sigcorp.com.br/processos/cajamar/requerimento/all"
        payload = json.dumps({"fluxoId": 12})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.get(url, headers=headers, data=payload, verify=False)
        
        print("Response status code:", response.status_code)  # Print status code for debugging
        
        response.raise_for_status()  # Raises an exception for 4xx, 5xx HTTP responses
        
        print("Response text:", response.text)  # Print response text for debugging
        
        # Try to parse the response JSON
        data = response.json()
        
        print("Parsed JSON data:", data)  # Print parsed JSON data for debugging
        
        # Return the total number of results
        return jsonify({'total_requerimentos': len(data)})

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
# Endpoint para obter dados populados na tabela localizacaoCarro
@app.route('/dados_localizacao_carro', methods=['GET'])
def dados_localizacao_carro():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        # Consulta para obter os dados populados na tabela localizacaoCarro
        query = "SELECT localizacaoCarroCoordenada, localizacaoCarroData FROM localizacaoCarro where localizacaoCarroCoordenada is not null and localizacaoCarroCoordenada <>'0'" 
        cursor.execute(query)
        # Extrair os dados do cursor
        dados_localizacao_carro = cursor.fetchall()
        # Converter os dados em um formato adequado para retorno JSON
        dados_formatados = [{'coordenada': row[0], 'data': row[1]} for row in dados_localizacao_carro]
        return jsonify(dados_formatados)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

def connect_to_database():
    return mysql.connector.connect(
        host='172.16.30.111',
        user='mcastilho',
        password='#KUTu547G6!aV@Si',
        database='carroConectado'
    )

# Endpoint para listar todas as coordenadas com suas respectivas ocorrências
@app.route('/coordenadas', methods=['GET'])
def listar_coordenadas():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT tipoIntercorrencia, coordenadaIntercorrencia, pathImagemIntercorrencia, dataIntercorrencia FROM intercorrencia WHERE coordenadaIntercorrencia <> '0' and coordenadaIntercorrencia <>'None'"
        cursor.execute(query)
        coordenadas = cursor.fetchall()
        return jsonify(coordenadas)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

# Endpoint para listar todas as coordenadas com suas respectivas ocorrências
@app.route('/ocorrencia', methods=['GET'])
def listar_ocorrencia():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT * FROM intercorrencia group by idDeteccao"
        cursor.execute(query)
        ocorrencia = cursor.fetchall()
        return jsonify(ocorrencia)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


# Endpoint para as 10 principais intercorrências por bairro
@app.route('/top_bairros_intercorrencias', methods=['GET'])
def top_bairros_intercorrencias():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT COUNT(*) as quantidade, bairroIntercorrencia FROM intercorrencia GROUP BY bairroIntercorrencia ORDER BY quantidade DESC LIMIT 10"
        cursor.execute(query)
        top_bairros = cursor.fetchall()
        return jsonify(top_bairros)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

# Endpoint para as 10 principais intercorrências por rua
@app.route('/top_ruas_intercorrencias', methods=['GET'])
def top_ruas_intercorrencias():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT COUNT(*) as quantidade, ruaIntercorrencia FROM intercorrencia GROUP BY ruaIntercorrencia ORDER BY quantidade DESC LIMIT 10"
        cursor.execute(query)
        top_ruas = cursor.fetchall()
        return jsonify(top_ruas)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


@app.route('/imagens', methods=['GET'])
def listar_imagens():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT pathImagemIntercorrencia, tipoIntercorrencia, bairroIntercorrencia, ruaIntercorrencia FROM intercorrencia WHERE coordenadaIntercorrencia <> '0'"
        cursor.execute(query)
        imagens = [{'path': row[0], 'tipo': row[1], 'bairro': row[2], 'rua': row[3]} for row in cursor.fetchall()]
        return jsonify(imagens)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


# Endpoint para retornar a quantidade total de ocorrências na base
@app.route('/total_intercorrencias', methods=['GET'])
def total_intercorrencias():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = '''SELECT COUNT(*) AS total_linhas
FROM (
    SELECT idDeteccao, COUNT(*) AS total_registros
    FROM intercorrencia
    GROUP BY idDeteccao
) AS subquery;'''
        cursor.execute(query)
        total = cursor.fetchone()[0]
        return jsonify({'total': total})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

@app.route('/total_ruas', methods=['GET'])
def total_ruas():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT COUNT(DISTINCT ruaIntercorrencia) as total FROM intercorrencia"
        cursor.execute(query)
        total = cursor.fetchone()[0]
        return jsonify({'total': total})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

@app.route('/total_bairros', methods=['GET'])
def total_bairros():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT COUNT(DISTINCT bairroIntercorrencia) as total FROM intercorrencia"
        cursor.execute(query)
        total = cursor.fetchone()[0]
        return jsonify({'total': total})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

# Endpoint para retornar a quantidade de ocorrências por tipo
@app.route('/total_intercorrencias_por_tipo', methods=['GET'])
def intercorrencias_por_tipo():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT SUBSTRING_INDEX(tipoIntercorrencia, ' ', 1) AS tipo, COUNT(*) as quantidade FROM intercorrencia GROUP BY tipo"
        cursor.execute(query)
        intercorrencias_tipo = cursor.fetchall()
        return jsonify(intercorrencias_tipo)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

# Endpoint para retornar a localização com as maiores intercorrências
@app.route('/localizacao_maiores_intercorrencias', methods=['GET'])
def localizacao_maiores_intercorrencias():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT coordenadaIntercorrencia, COUNT(*) as quantidade FROM intercorrencia GROUP BY coordenadaIntercorrencia ORDER BY quantidade DESC LIMIT 5"
        cursor.execute(query)
        localizacao_maiores = cursor.fetchall()
        return jsonify(localizacao_maiores)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


# Novo endpoint para calcular a distância percorrida
@app.route('/distancia_total', methods=['GET'])
def distancia_total():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "SELECT coordenadaIntercorrencia FROM intercorrencia WHERE coordenadaIntercorrencia <> '0'"
        cursor.execute(query)
        coordenadas_result = cursor.fetchall()
        coordenadas = [eval(coord[0]) for coord in coordenadas_result]
        distancia_total_km = 0
        for i in range(len(coordenadas) - 1):
            coord1 = coordenadas[i]
            coord2 = coordenadas[i+1]
            distancia_total_km += geodesic(coord1, coord2).kilometers
        distancia_total_km = round(distancia_total_km, 2)
        return jsonify({'distancia_total_km': distancia_total_km})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()

@app.route('/priorizacao', methods=['POST'])
def priorizacao():
    # Obtendo os dados do POST request
    data = request.get_json()
    db_connection = connect_to_database()
    ocorrencia1 = data.get('ocorrencia1')
    ocorrencia2 = data.get('ocorrencia2')
    ocorrencia3 = data.get('ocorrencia3')
    insert_query = "INSERT INTO intercorrencia (tipoIntercorrencia, coordenadaIntercorrencia, pathImagemIntercorrencia, dataIntercorrencia) VALUES (%s, %s, %s, %s)"
    cursor = db_connection.cursor()

    cursor.execute(insert_query, (ocorrencia1, ocorrencia2, ocorrencia3))
    db_connection.commit()

    print(ocorrencia1, ocorrencia2, ocorrencia3)
    # Retornar uma resposta JSON
    return jsonify({'ocorrencia1': ocorrencia1, 'ocorrencia2': ocorrencia2, 'ocorrencia3': ocorrencia3})

@app.route('/autenticacao', methods=['POST'])
def autenticacao():
    global token
    token = request.json.get('token')  # Assumindo que o token será enviado como JSON {'token': 'token_aqui'}
    if token:
        print(f'Token recebido: {token}')
        return redirect('http://127.0.0.1:8050/')
    else:
        return 'Token não encontrado na requisição', 400

# Novo endpoint para visualizar o token
@app.route('/visualizar_token', methods=['GET'])
def visualizar_token():
    if token:
        return jsonify({'token': token})
    else:
        return jsonify({'message': 'Token não encontrado'}), 404


# Endpoint para validar se o token ainda é válido
@app.route('/validar_token', methods=['GET'])
def validar_token():
    global token_info
    print('oi')
    url = "https://gatewayqa.sigcorp.com.br/plataforma/auth/get-user"
    

    
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get(url, headers=headers,verify=False)
        if response.status_code == 200:
            print('caiu aqui')
            return jsonify({'status': 'sim'})
        else:
            print( 'nao caiu aqui')
            return jsonify({'status': 'não'})
    except Exception as e:
        return jsonify({'status': 'não', 'error': str(e)}), 500

@app.route('/action', methods=['POST', 'OPTIONS'])
def action():
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return '', 200, headers

    # Restante do código para o endpoint POST
    data = request.get_json()
    print (data)
    
    ocorrencia = data.get('ocorrencia')
    rua = data.get('rua')
    bairro = data.get('bairro')
    data_ocorrencia = data.get('data')
    imagem_url = data.get('imagem')

    if not (ocorrencia and data_ocorrencia and imagem_url):
        return jsonify({'error': 'Dados incompletos'}), 400

    try:
        # Baixar a imagem do URL
        response = requests.get(imagem_url)
        response.raise_for_status()  # Lança uma exceção em caso de erro HTTP
        
        # Extrair o nome do arquivo da URL
        nome_arquivo = os.path.basename(imagem_url)
        caminho_salvar = os.path.join(UPLOAD_FOLDER, nome_arquivo)

        # Salvar a imagem localmente
        with open(caminho_salvar, 'wb') as f:
            f.write(response.content)

        # Processar a imagem (exemplo: imprimir o conteúdo)
        print(f'Imagem processada: {caminho_salvar}')
        

        # Apagar a imagem após o processamento
        #os.remove(caminho_salvar)
        
        
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Erro ao baixar imagem: {str(e)}'}), 500
    except OSError as e:
        return jsonify({'error': f'Erro ao apagar imagem: {str(e)}'}), 500
    payload = {
        'fluxoId': '12',
        'formulariosRespondidos[0][respostas][0][formCampoId]': '194',
        'formulariosRespondidos[0][respostas][0][campoId]': '4',
        'formulariosRespondidos[0][respostas][0][valor]': ocorrencia,
        'formulariosRespondidos[0][respostas][1][formCampoId]': '195',
        'formulariosRespondidos[0][respostas][1][campoId]': '1',
        'formulariosRespondidos[0][respostas][1][valor]': data_ocorrencia,
        'formulariosRespondidos[0][respostas][2][formCampoId]': '196',
        'formulariosRespondidos[0][respostas][2][campoId]': '1',
        'formulariosRespondidos[0][respostas][2][valor]': rua,
        'formulariosRespondidos[0][respostas][3][formCampoId]': '197',
        'formulariosRespondidos[0][respostas][3][campoId]': '1',
        'formulariosRespondidos[0][respostas][3][valor]': '165',
        'formulariosRespondidos[0][respostas][4][formCampoId]': '198',
        'formulariosRespondidos[0][respostas][4][campoId]': '1',
        'formulariosRespondidos[0][respostas][4][valor]': '165a',
        'formulariosRespondidos[0][respostas][5][formCampoId]': '199',
        'formulariosRespondidos[0][respostas][5][campoId]': '1',
        'formulariosRespondidos[0][respostas][5][valor]': bairro,
        'formulariosRespondidos[0][respostas][6][formCampoId]': '200',
        'formulariosRespondidos[0][respostas][6][campoId]': '2',
        'formulariosRespondidos[0][formularioTipoId]': '68'
    }

    
    if not os.path.exists(caminho_salvar):
        return jsonify({'error': 'Imagem não encontrada'}), 400

    files = [
        ('formulariosRespondidos[0][respostas][6][valor]', ('ocorrencia.png', open(caminho_salvar, 'rb'), 'image/png'))
    ]

    headers = {
        'Client-Key': 'q3AoVnBH89RNwEjcBJPIzQ73dWY4aZBl',
        'Authorization': 'Bearer ' + token
    }

    # Enviar a requisição para o endpoint externo
    try:
        response = requests.post("https://gatewayqa.sigcorp.com.br/processos/cajamar/requerimento/create", headers=headers, data=payload, files=files, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

    
        # Retornar a resposta apropriada
    return jsonify({'message': 'Ação recebida com sucesso e enviada para o endpoint externo!'}), 200
    
    
'''def action():
    data = request.get_json()

    print(data)



    # Aqui você pode processar os dados recebidos
    ocorrencia = data.get('ocorrencia')
    rua = data.get('rua')
    bairro = data.get('bairro')
    data_ocorrencia = data.get('data')
    imagem = data.get('imagem')

    print(imagem)

    # Verifique se todos os dados necessários foram fornecidos
    if not (ocorrencia and rua and bairro and data_ocorrencia):
        return jsonify({'error': 'Dados incompletos'}), 400

    # Preparar payload para o endpoint externo
    payload = {
        'fluxoId': '12',
        'formulariosRespondidos[0][respostas][0][formCampoId]': '194',
        'formulariosRespondidos[0][respostas][0][campoId]': '4',
        'formulariosRespondidos[0][respostas][0][valor]': ocorrencia,
        'formulariosRespondidos[0][respostas][1][formCampoId]': '195',
        'formulariosRespondidos[0][respostas][1][campoId]': '1',
        'formulariosRespondidos[0][respostas][1][valor]': data_ocorrencia,
        'formulariosRespondidos[0][respostas][2][formCampoId]': '196',
        'formulariosRespondidos[0][respostas][2][campoId]': '1',
        'formulariosRespondidos[0][respostas][2][valor]': rua,
        'formulariosRespondidos[0][respostas][3][formCampoId]': '197',
        'formulariosRespondidos[0][respostas][3][campoId]': '1',
        'formulariosRespondidos[0][respostas][3][valor]': '165',
        'formulariosRespondidos[0][respostas][4][formCampoId]': '198',
        'formulariosRespondidos[0][respostas][4][campoId]': '1',
        'formulariosRespondidos[0][respostas][4][valor]': '165a',
        'formulariosRespondidos[0][respostas][5][formCampoId]': '199',
        'formulariosRespondidos[0][respostas][5][campoId]': '1',
        'formulariosRespondidos[0][respostas][5][valor]': bairro,
        'formulariosRespondidos[0][respostas][6][formCampoId]': '200',
        'formulariosRespondidos[0][respostas][6][campoId]': '2',
        'formulariosRespondidos[0][formularioTipoId]': '68'
    }

    image_path = 'C:\\Users\\milena.castilho\\Desktop\\imagem.png'
    
    if not os.path.exists(image_path):
        return jsonify({'error': 'Imagem não encontrada'}), 400

    files = [
        ('formulariosRespondidos[0][respostas][6][valor]', ('bb.png', open(image_path, 'rb'), 'image/png'))
    ]

    headers = {
        'Client-Key': 'q3AoVnBH89RNwEjcBJPIzQ73dWY4aZBl',
        'Authorization': 'Bearer ' + token
    }

    # Enviar a requisição para o endpoint externo
    try:
        response = requests.post("https://gatewayqa.sigcorp.com.br/processos/cajamar/requerimento/create", headers=headers, data=payload, files=files, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

    # Retornar a resposta apropriada
    return jsonify({'message': 'Ação recebida com sucesso e enviada para o endpoint externo!'}), 200
'''
@app.route('/filtro', methods=['POST'])

def filtro():
    data = request.get_json()
    db_connection = connect_to_database()
    cursor = db_connection.cursor()

    # Extraindo valores do JSON corretamente
    date = data.get('date')
    print(date)
    bairro = data.get('bairro')
    rua = data.get('rua')
    page = data.get('page', 1)
    page_size = data.get('page_size', 50)

    # Assegurando que page e page_size sejam inteiros
    page = int(page) if page else 1
    page_size = int(page_size) if page_size else 50

    # Construindo a consulta com filtros
    query = "SELECT * FROM intercorrencia WHERE 1=1"
    query_count = "SELECT COUNT(*) FROM intercorrencia WHERE 1=1"
    params = []

    if date:
        query += " AND dataIntercorrencia LIKE %s"
        query_count += " AND dataIntercorrencia LIKE %s"
        params.append(f"{date}%")
    if rua:
        query += " AND ruaIntercorrencia = %s"
        query_count += " AND ruaIntercorrencia = %s"
        params.append(rua)
    if bairro:
        query += " AND bairroIntercorrencia = %s"
        query_count += " AND bairroIntercorrencia = %s"
        params.append(bairro)

    print (query_count)

    # Executando a consulta de contagem
    cursor.execute(query_count, tuple(params))
    total_records = cursor.fetchone()[0]

    # Adicionando a paginação à consulta
    offset = (page - 1) * page_size
    query += " LIMIT %s OFFSET %s"
    params.append(page_size)
    params.append(offset)

    # Executando a consulta com paginação
    cursor.execute(query, tuple(params))
    query_result = cursor.fetchall()

    # Construindo a resposta
    response_data = []
    for row in query_result:
        response_data.append({
            "id": row[0],
            "ocorrencia": row[1],
            "coordenadas": row[2],
            "imagem": row[3],
            "data": row[4].strftime('%Y-%m-%d %H:%M:%S'),  # Formatando datetime para string
            "bairro": row[5],
            "rua": row[6]
        })

    return jsonify({'total': total_records, 'records': response_data})

if __name__ == '__main__':
    app.run(debug=False)
