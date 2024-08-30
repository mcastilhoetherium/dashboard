from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
import mysql.connector
from geopy.geocoders import Nominatim 
import googlemaps
from geopy.distance import geodesic
import requests
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

# Converta a imagem para base64
with open("assets/logo.png", "rb") as img_file:
    encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
UPLOAD_FOLDER = r'C:\Users\milena.castilho\Desktop'
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})



##emai

EMAIL_ADDRESS = "milena_castilho@live.com"
EMAIL_PASSWORD = "always"




# Endpoint para obter o valor atual de priorização
@app.route('/get_priorizacao_value', methods=['GET'])
def get_priorizacao_value():
    conn = connect_to_database()
    cursor = conn.cursor()

    query = "SELECT parametro FROM parametros  WHERE tipo = 'numero de ocorrencias'"
    cursor.execute(query)
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return jsonify({"value": result[0]})
    else:
        return jsonify({"value": 0}), 404

# Endpoint para atualizar o valor de priorização
@app.route('/update_priorizacao_value/<int:new_value>', methods=['POST'])
def update_priorizacao_value(new_value):
    conn = connect_to_database()
    cursor = conn.cursor()

    query = "Update parametros set parametro = (%s) WHERE tipo = 'numero de ocorrencias' "
    cursor.execute(query, (new_value,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"success": True}), 200

def send_email(to_email, subject, body):
    try:
        # Configurando o servidor SMTP
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        # Criando o email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject

        # Anexa o corpo do email como HTML
        msg.attach(MIMEText(body, 'html'))

        # Enviando o email
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print(f"Falha ao enviar email: {e}")

@app.route('/convidar', methods=['POST'])
def convidar():
    data = request.json
    nome = data.get('nome')
    email = data.get('contato')
    setor = data.get('setor')
    documento = data.get('documento')
    ocorrencias = data.get('ocorrencias')
    acesso = data.get('acesso')
    tipo_acesso = data.get('tipo_acesso')

    if not nome or not email:
        return jsonify({"error": "Nome e email são obrigatórios"}), 400

    # Inserir dados na tabela nivelacesso
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        query = "INSERT INTO nivelAcesso (email, tipoAcesso) VALUES (%s, %s)"
        values = (email,acesso)  # Convertendo ocorrencias para string
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        return jsonify({"error": f"Erro ao inserir dados: {err}"}), 500

    # Enviar e-mail
    link = "http://127.0.0.1:8051/"  # Exemplo de link de confirmação
    body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        .email-container {{
            border: 3px solid purple;
            padding: 20px;
            max-width: 600px;
            margin: auto;
            font-family: Arial, sans-serif;
        }}
        .header-image {{
            display: block;
            margin: 0 auto;
            width: 100px;
        }}
        .email-body {{
            text-align: left;
            color: #333;
            font-size: 16px;
        }}
        .email-body a {{
            color: purple;
            text-decoration: none;
        }}
        .email-body a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <img src="assets/logo.png" alt="Logo" class="header-image">
        <div class="email-body">
            <p>Olá {nome},</p>
            <p>Você foi convidado a participar da plataforma Urban.AI! Por favor, faça seu cadastro clicando no link abaixo:</p>
            <p><a href="{link}">{link}</a></p>
            <p>Atenciosamente,<br>Prefeitura X</p>
        </div>
    </div>
</body>
</html>
"""

    send_email(email, "Cadastro Bem-Sucedido", body)

    return jsonify({"message": "E-mail enviado com sucesso!"}), 200

def send_email(to_address, subject, body):
    from_address = "milena_castilho@live.com"
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP('smtp.office365.com', 587) as server:
        server.starttls()
        server.login(from_address, "always")
        server.send_message(msg)

@app.route('/finalizar_cadastro', methods=['POST'])
def finalizar_cadastro():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email é necessário'}), 400
    
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # Verificar se o email existe na tabela
        cursor.execute("SELECT * FROM sua_tabela WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            # Atualizar o campo de acesso
            cursor.execute("UPDATE sua_tabela SET acesso = 'sim' WHERE email = %s", (email,))
            connection.commit()
            
            # Enviar e-mail de boas-vindas
            body = "Olá! Bem-vindo ao Urban.AI."
            send_email(email, "Bem-vindo ao Urban.AI", body)
            
            return jsonify({'message': 'Cadastro finalizado com sucesso. E-mail enviado.'}), 200
        
        else:
            # Enviar e-mail orientando contato com a prefeitura
            body = "O email fornecido não está cadastrado. Por favor, entre em contato com a prefeitura."
            send_email(email, "Contato Necessário", body)
            
            return jsonify({'message': 'E-mail não encontrado. Orientações enviadas.'}), 404
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
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
        
        
        
        response.raise_for_status()  # Raises an exception for 4xx, 5xx HTTP responses
        
       
        
        # Try to parse the response JSON
        data = response.json()
        
       
        
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
        query = "SELECT * FROM intercorrencia"
        cursor.execute(query)
        ocorrencia = cursor.fetchall()
        return jsonify(ocorrencia)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


@app.route('/ocorrencia_priorizada', methods=['GET'])
def listar_ocorrencia_priorizada():
    try:
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        query = "select a.nome from ocorrencias a inner join ocorrenciaPriorizada b ON a.id =b.id  and b.data_inicial is null"
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
        query = 'SELECT COUNT(*) FROM intercorrencia'
        cursor.execute(query)
        total = cursor.fetchone()[0]
        print (total)
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
    
    # Conectando ao banco de dados
    db_connection = connect_to_database()
    cursor = db_connection.cursor()

    # Extraindo os dados da requisição
    ocorrencias = {
        'ocorrencia1': data.get('select1'),
        'ocorrencia2': data.get('select2'),
        'ocorrencia3': data.get('select3')
    }
    
    # Consulta de inserção
    insert_query = """
        INSERT INTO ocorrenciaPriorizada (ocorrencia)
        VALUES (%s)
    """
    print(insert_query)
    # Inserir uma ocorrência por vez
    for key, ocorrencia in ocorrencias.items():
        if ocorrencia:  # Verifica se o valor não é None ou vazio
            cursor.execute(insert_query, (ocorrencia,))
    
    # Confirmando a transação
    db_connection.commit()
    
    # Fechando o cursor e a conexão
    cursor.close()
    db_connection.close()

    # Retornar uma resposta JSON
    return jsonify({'status': 'success', 'message': 'Ocorrências inseridas com sucesso'})

@app.route('/ocorrencias', methods=['GET'])
def get_ocorrencias():
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)  # dictionary=True para retornar os resultados como dicionários

    cursor.execute("SELECT id, nome FROM ocorrencias")  # Substitua pelo nome correto da tabela
    ocorrencias = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(ocorrencias)

@app.route('/ruas', methods=['GET'])
def get_ruas():
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)  # dictionary=True para retornar os resultados como dicionários

    cursor.execute("SELECT count(tipoIntercorrencia), ruaIntercorrencia, bairroIntercorrencia FROM intercorrencia where ruaIntercorrencia is not null group by ruaIntercorrencia order by bairroIntercorrencia ASC")  # Substitua pelo nome correto da tabela
    ruas = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(ruas)


@app.route('/bairros', methods=['GET'])
def get_bairros():
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)  # dictionary=True para retornar os resultados como dicionários

    cursor.execute("SELECT count(tipoIntercorrencia), count(distinct (ruaIntercorrencia)), bairroIntercorrencia FROM intercorrencia where bairroIntercorrencia is not null group by bairroIntercorrencia order by bairroIntercorrencia ASC")  # Substitua pelo nome correto da tabela
    bairros = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(bairros)



@app.route('/autenticacao', methods=['POST'])
def autenticacao():
    global token
    token = request.json.get('token')  # Assumindo que o token será enviado como JSON {'token': 'token_aqui'}
    if token:
        
        return redirect(f'http://127.0.0.1:8050/dashboard?token={token}')
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
    
    url = "https://gatewayqa.sigcorp.com.br/plataforma/auth/get-user"
    

    
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get(url, headers=headers,verify=False)
        if response.status_code == 200:
            
            return jsonify({'status': 'sim'})
        else:
            
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
   
    db_connection = connect_to_database()
    cursor = db_connection.cursor()

    # Restante do código para o endpoint POST
    data = request.get_json()

    ocorrencia = data.get('ocorrencia')
    rua = data.get('rua')
    bairro = data.get('bairro')
    data_ocorrencia = data.get('data')
    imagem_url = data.get('imagem')
    id = data.get('id')

    try:
        query = "INSERT INTO chamados (idOcorrencia, data, status) VALUES (%s, NOW(), 'aberto')"
        values = (id,)
        cursor.execute(query, values)

    # Commit da transação
        db_connection.commit()

        print("Registro inserido com sucesso!")
    except Exception as e:
        print(f"Erro ao inserir: {e}")
        db_connection.rollback()  # Desfaz a transação em caso de erro

    return jsonify({'message': 'Ação recebida com sucesso e enviada para o endpoint externo!'}), 200

    
'''def action():
    data = request.get_json()

   



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
            "data": row[4].strftime('%d-%m-%Y %H:%M:%S'),  # Formatando datetime para string
            "bairro": row[5],
            "rua": row[6]
        })

    return jsonify({'total': total_records, 'records': response_data})

@app.route('/consulta_chamados', methods=['GET'])
def consulta_chamados():
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Consulta SQL para buscar os dados
    query = """
    SELECT a.id, a.data AS 'Chamado Aberto em:', a.status, a.descricao, 
           i.tipoIntercorrencia, i.pathImagemIntercorrencia, 
           i.dataIntercorrencia AS 'Detectado em:', i.bairroIntercorrencia, 
           i.ruaIntercorrencia 
    FROM chamados a 
    INNER JOIN intercorrencia i ON a.idOcorrencia = i.idintercorrencia
    """

    try:
        cursor.execute(query)
        resultados = cursor.fetchall()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify(resultados), 200


if __name__ == '__main__':
    app.run(debug=False)
