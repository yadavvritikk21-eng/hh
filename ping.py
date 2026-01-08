def register_ping(app):
    @app.route("/ping")
    def ping():
        return "OK", 200
