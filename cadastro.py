import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import json
import re  # Importando módulo de expressões regulares para validação de senha

# Inicializando o aplicativo Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])

# Função para criar os inputs do formulário
def create_input_form():
    inputs = [
        {"label": "Nome", "id": "example-nome", "type": "text", "placeholder": "Digite seu nome"},
        {"label": "Email", "id": "example-email", "type": "email", "placeholder": "Digite seu email"},
        {"label": "Senha", "id": "example-senha", "type": "password", "placeholder": "Digite sua senha"},
        {"label": "Data de Nascimento", "id": "example-dataNasc", "type": "text", "placeholder": "YYYY-MM-DD"},
        {"label": "Telefone", "id": "example-telefone", "type": "text", "placeholder": "Digite seu telefone"},
        {"label": "Celular", "id": "example-celular", "type": "text", "placeholder": "Digite seu celular"},
        {"label": "CEP", "id": "example-cep", "type": "text", "placeholder": "Digite seu CEP"},
        {"label": "Logradouro", "id": "example-logradouro", "type": "text", "placeholder": "Digite seu logradouro"},
        {"label": "Número", "id": "example-numero", "type": "text", "placeholder": "Digite seu número"},
        {"label": "Bairro", "id": "example-bairro", "type": "text", "placeholder": "Digite seu bairro"},
    ]
    return [
        html.Div(
            [
                dbc.Label(input_field["label"], html_for=input_field["id"]),
                dbc.Input(
                    type=input_field["type"],
                    id=input_field["id"],
                    placeholder=input_field["placeholder"],
                    required=True
                ),
                dbc.FormFeedback(
                    "Campo obrigatório", 
                    type="invalid",
                    id=f"{input_field['id']}-feedback"
                ),
            ],
            className="mb-3",
        ) for input_field in inputs
    ]

# Criando o card de cadastro com scroll
quadrado_cadastro = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Row(
                [
                    dbc.Col(html.Img(src="/assets/logo.png", height="150px"), width=12, className="text-center"),
                ],
                align="center",
            )
        ),
        dbc.CardBody(
            children=create_input_form(),
            className="p-4",
            style={"height": "400px", "overflow-y": "auto"}  # Definindo altura e scroll
        ),
        dbc.CardFooter(
            dbc.Button("Cadastrar", id="register-button", color="primary", style={"width": "100%", "background-color": "#8d008fa6"}),
            className="text-center"
        )
    ],
    className="mb-5 rounded shadow",
    style={"width": "600px"}  # Ajuste a largura do card aqui
)

# Layout da aplicação
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=True),
        html.Div(
            [
                dbc.Row(
                    dbc.Col(
                        quadrado_cadastro, width={"size": 12, "offset": 1}  # Ajustando para centralizar
                    )
                ),
            ],
            style={"height": "100vh", "display": "flex", "align-items": "center", "justify-content": "center"},
        ),
        html.Div(id="register-status", className="mt-3")
    ]
)

# Função para validar a segurança da senha
def is_password_strong(password):
    # Verificando se a senha tem pelo menos 6 caracteres, inclui letras maiúsculas, minúsculas, números e caracteres especiais
    return (
        len(password) >= 6 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

# Callback para realizar o cadastro
@app.callback(
    Output("register-status", "children"),
    [Input("register-button", "n_clicks")],
    [State("example-nome", "value"),
     State("example-email", "value"),
     State("example-senha", "value"),
     State("example-dataNasc", "value"),
     State("example-telefone", "value"),
     State("example-celular", "value"),
     State("example-cep", "value"),
     State("example-logradouro", "value"),
     State("example-numero", "value"),
     State("example-bairro", "value")],
    prevent_initial_call=True
)
def register(n_clicks, nome, email, senha, dataNasc, telefone, celular, cep, logradouro, numero, bairro):
    if n_clicks:
        # Checando campos vazios e mostrando feedback
        invalid_fields = []
        for field, value in zip(
            ["example-nome", "example-email", "example-senha", "example-dataNasc", "example-telefone", "example-celular", "example-cep", "example-logradouro", "example-numero", "example-bairro"],
            [nome, email, senha, dataNasc, telefone, celular, cep, logradouro, numero, bairro]
        ):
            if not value:
                invalid_fields.append(field)
        
        # Verificando a segurança da senha
        if senha and not is_password_strong(senha):
            invalid_fields.append("example-senha")
            return dbc.Alert("Senha fraca. A senha deve ter pelo menos 6 caracteres, incluindo letra maiúscula, minúscula, números e caracteres especiais.", color="danger")

        if invalid_fields:
            return dbc.Alert("Preencha todos os campos obrigatórios.", color="danger")
        
        url_cadastro = "https://gatewayqa.sigcorp.com.br/plataforma/pessoa/auto-cadastro"
        payload = json.dumps({
            "nome": nome,
            "email": email,
            "senha": senha,
            "dataNasc": dataNasc,
            "telefone": telefone,
            "celular": celular,
            "cep": cep,
            "logradouro": logradouro,
            "numero": numero,
            "bairro": bairro
        })
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url_cadastro, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                # Enviando o e-mail para outro endpoint após o cadastro ser bem-sucedido
                url_envio_email = "https://exemplo.com/endpoint-email"
                email_payload = json.dumps({"email": email})
                email_response = requests.post(url_envio_email, headers=headers, data=email_payload, verify=False)
                
                if email_response.status_code == 200:
                    return dbc.Alert("Cadastro realizado com sucesso! E-mail enviado.", color="success")
                else:
                    return dbc.Alert(f"Cadastro realizado, mas houve falha ao enviar o e-mail: {email_response.text}", color="warning")
            else:
                return dbc.Alert(f"Falha no cadastro: {response.text}", color="danger")
        except requests.exceptions.RequestException as e:
            return dbc.Alert(f"Erro na requisição: {e}", color="danger")
    return ""

if __name__ == '__main__':
    app.run_server(debug=False, port=8051)
