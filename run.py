"Ponto de entrada da aplicacao Flask (modo desenvolvimento)."

from app import criar_app

app = criar_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])