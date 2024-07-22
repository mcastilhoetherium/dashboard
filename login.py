import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import json

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])

# Definindo o estilo do quadrado branco
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
        dbc.Spinner(html.Div(id="verify-status", className="mt-3"), color="primary")
    ],
    id="offcanvas-verificacao",
    title="Verificação de código",
    is_open=False,
    placement="end",
)

# Layout da aplicação
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
            style={
                "height": "100vh", 
                "display": "flex", 
                "align-items": "center", 
                "justify-content": "center",
                "backgroundImage": 'url("/assets/background.png")',
                "backgroundSize": "cover"
            },
        ),
        offcanvas_verificacao
    ]
)

@app.callback(
    Output("offcanvas-verificacao", "is_open"),
    Output("login-status", "children"),
    Input("login-button", "n_clicks"),
    State("example-email", "value"),
    State("example-password", "value"),
    prevent_initial_call=True
)
def open_offcanvas(n_clicks, email, password):
    if n_clicks and email and password:
        return True, "Verificando..."
    return False, ""

@app.callback(
    Output("verify-status", "children"),
    Output("url", "href"),
    Input("verify-button", "n_clicks"),
    State("example-email", "value"),
    State("example-password", "value"),
    State("verify-code", "value"),
    prevent_initial_call=True
)
def verify_code(n_clicks, email, password, verify_code):
    if n_clicks and email and password and verify_code:
        url = "https://gatewayqa.sigcorp.com.br/plataforma/auth/login"
        payload = json.dumps({
            "email": email,
            "cpf": "09876574965",  # Este valor pode ser dinâmico se necessário
            "password": password,
            "keepAlive": True,
            "verifyCode": verify_code
        })
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("message") == "Usuário logado com sucesso!":
                    # Enviar o token para o endpoint Flask
                    token = response_data["data"]["access_token"]
                    send_token_to_flask(token)
                    return "Usuário logado com sucesso!", "http://127.0.0.1:8050/"
                else:
                    return f"Falha no login: {response.text}", None
            else:
                return f"Falha no login: {response.text}", None
        except requests.exceptions.RequestException as e:
            return f"Erro na requisição: {e}", None
    return "", None

# Função para enviar o token para o endpoint Flask
def send_token_to_flask(token):
    url = "http://127.0.0.1:5000/autenticacao"
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "token": token
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Token enviado com sucesso para o endpoint Flask.")
        else:
            print(f"Falha ao enviar token para o endpoint Flask: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar token para o endpoint Flask: {e}")

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
