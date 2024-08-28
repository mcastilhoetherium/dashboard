import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import json
import mysql.connector
from flask import request, make_response, redirect, jsonify

def check_email_in_db(email):
    try:
        connection = mysql.connector.connect(
            host='172.16.30.111',
            user='mcastilho',
            password='#KUTu547G6!aV@Si',
            database='carroConectado'
        )
        cursor = connection.cursor()
        query = "SELECT COUNT(*) FROM nivelAcesso WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        return result[0] > 0
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])

quadrado_branco = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Row(
                [
                    dbc.Col(html.Img(src="/assets/logo.png", height="300"), width=3),
                ],
                align="center",
            )
        ),
        dbc.CardBody(
            [
                html.Div(
                    [
                        dbc.Label("Email", html_for="example-email"),
                        dbc.Input(type="email", id="example-email", placeholder="Digite seu email"),
                    ],
                    className="mb-3",
                ),
                html.Div(
                    [
                        dbc.Label("Senha", html_for="example-password"),
                        dbc.Input(
                            type="password",
                            id="example-password",
                            placeholder="Digite sua senha",
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Button("Entrar", id="login-button", color="primary", className="mr-1"),
                html.Div(id="login-status", className="mt-3")
            ]
        ),
    ],
    className="p-3 mb-5 rounded",
)

offcanvas_verificacao = dbc.Offcanvas(
    [
        html.Div(
            [
                dbc.Label("Código de verificação", html_for="verify-code"),
                dbc.Input(type="text", id="verify-code", maxLength=6, placeholder="Digite o código de 6 dígitos"),
            ],
            className="mb-3",
        ),
        dbc.Button("Enviar", id="verify-button", color="primary"),
        html.Div(id="verify-status", className="mt-3")
    ],
    id="offcanvas-verificacao",
    title="Verificação de código",
    is_open=False,
    placement="end",
)

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=True),
        html.Div(
            [
                dbc.Row(
                    dbc.Col(
                        quadrado_branco, width={"size": 50, "offset": 1}
                    )
                ),
            ],
            style={"height": "100vh", "display": "flex", "align-items": "center", "justify-content": "center"},
        ),
        offcanvas_verificacao,
        dcc.Store(id='store-token'),
    ]
)

@app.callback(
    [Output("login-status", "children"),
     Output("offcanvas-verificacao", "is_open"),
     Output("verify-status", "children"),
     Output('url', 'href')],
    [Input("login-button", "n_clicks"),
     Input("verify-button", "n_clicks")],
    [State("example-email", "value"),
     State("example-password", "value"),
     State("verify-code", "value")],
    prevent_initial_call=True
)
def update_status(login_n_clicks, verify_n_clicks, email, password, verify_code):
    ctx = dash.callback_context

    if not ctx.triggered:
        return "", False, "", None

    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_input == "login-button":
        if not check_email_in_db(email):
            return "E-mail não encontrado na base de dados.", False, "", None

        url = "https://gatewayqa.sigcorp.com.br/plataforma/auth/login"
        payload = json.dumps({
            "email": email,
            "cpf": "09876574965",
            "password": password,
            "keepAlive": True
        })
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("message") == "Usuário logado com sucesso!":
                    return "Usuário logado com sucesso!", True, "", None
                elif response_data.get("message") == "Código de verificação enviado para o email!":
                    return "Código de verificação enviado para o email!", True, "", None
                else:
                    return f"Falha no login: {response_data.get('message')}", False, "", None
            else:
                return f"Falha no login: {response.text}", False, "", None
        except requests.exceptions.RequestException as e:
            return f"Erro na requisição: {e}", False, "", None

    elif triggered_input == "verify-button":
        if email and password and verify_code:
            url = "https://gatewayqa.sigcorp.com.br/plataforma/auth/login"
            payload = json.dumps({
                "email": email,
                "cpf": "09876574965",
                "password": password,
                "verifyCode": verify_code,
                "keepAlive": True
            })
            headers = {'Content-Type': 'application/json'}
            try:
                response = requests.post(url, headers=headers, data=payload, verify=False)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get("message") == "Usuário logado com sucesso!":
                        token = response_data["data"]["access_token"]
                        access_type = get_access_type_from_db(email)  # Obtém o tipo de acesso do banco

                        set_cookie_url = f"/set_cookie?token={token}&access_type={access_type}"

                        return "", False, "Usuário verificado com sucesso!", set_cookie_url
                    else:
                        return "", True, f"Falha na verificação: {response_data.get('message')}", None
                else:
                    return "", True, f"Falha na verificação: {response.text}", None
            except requests.exceptions.RequestException as e:
                return "", True, f"Erro na requisição: {e}", None

    return "", False, "", None

def get_access_type_from_db(email):
    try:
        connection = mysql.connector.connect(
            host='172.16.30.111',
            user='mcastilho',
            password='#KUTu547G6!aV@Si',
            database='carroConectado'
        )
        cursor = connection.cursor()
        query = "SELECT tipoAcesso FROM nivelAcesso WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        return result[0] if result else "default"  # Retorna um tipo de acesso padrão se não encontrado
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return "default"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.server.route('/set_cookie')
def set_cookie():
    token = request.args.get("token")
    access_type = request.args.get("access_type")

    # Definir cookies com o token e o tipo de acesso
    response = make_response(redirect('http://127.0.0.1:8050/dashboard'))
    response.set_cookie("token", token, httponly=True, secure=True)
    response.set_cookie("access_type", access_type, httponly=True, secure=True)
    return response



if __name__ == '__main__':
    app.run_server(debug=True, port=8052)
