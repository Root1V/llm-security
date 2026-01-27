from fastapi import Request

# ---------- Dependencies ----------
def get_users(request: Request) -> dict:
    """
    Accede al diccionario de usuarios cargado en app.state
    """
    return request.app.state.users
