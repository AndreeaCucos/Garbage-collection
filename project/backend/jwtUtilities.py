import jwt
import bcrypt
from database_opperations import get_user_info, add_token_to_blacklist, search_token_in_blacklist
from datetime import datetime, timedelta
import uuid
from config import SECRET_KEY
from graph_database import delete_by_jti


def get_token(username):
    """
        Funcția get_token se ocupă de crearea token-ului
        aferent utilizatorului curent.

        Parametrii:
            username (str): denumirea utilizatorului.

        Returnează:
            (str): token-ul creat.
    """
    # Extragem din baza de date identificatorul utilizatorului.
    info = get_user_info(username)
    id = info["id"]
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    payload = {
        'jti': str(uuid.uuid4()),
        'sub': str(id),
        'iat': datetime.utcnow(),
        "exp": expiration_time
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def verify_password(password, hashed_password):
    """
        Funcția verify_password verifică dacă parola introdusă
        de utilizator coincide cu cea salvată
        în tabela Users.

        Parametrii:
            password (str): parola introdusă de utilizator.
            hashed_password (str): parola codificată extrasă din tabelă.

        Returnează:
            (boolean): True dacă parolele coincid, False în caz contrar.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


def authorize_token(token):
    """
        Funcția authorize_token verifică validitatea token-ului.

        Parametrii:
            token (str): token-ul utilizatorului.

        Returnează:
            (boolean): True dacă este valid, False în caz contrar.
    """
    try:
        decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        jti = decoded_jwt['jti']
        iat = decoded_jwt['iat']
        exp = datetime.fromtimestamp(decoded_jwt['exp'])
    except jwt.ExpiredSignatureError as e:  # Este expirat.
        if not search_token_in_blacklist(token):
            # Decodificare token-ului fără verificarea semnăturii.
            # https://pyjwt.readthedocs.io/en/latest/usage.html#reading-the-claimset-without-validation
            decoded_jwt = jwt.decode(token, options={"verify_signature": False})
            jti = decoded_jwt['jti']
            exp = datetime.fromtimestamp(decoded_jwt['exp'])
            iat = datetime.fromtimestamp(decoded_jwt['iat'])
            add_token_to_blacklist(jti, token, exp, iat)
            delete_by_jti(jti)
        return False
    except jwt.InvalidTokenError:  # Este invalid. (nu coincide semnătura)
        if not search_token_in_blacklist(token):
            decoded_jwt = jwt.decode(token, options={"verify_signature": False})
            jti = decoded_jwt['jti']
            exp = datetime.fromtimestamp(decoded_jwt['exp'])
            iat = datetime.fromtimestamp(decoded_jwt['iat'])
            add_token_to_blacklist(jti, token, exp, iat)
            delete_by_jti(jti)
        return False
    # Verificăm dacă există în tabela BlacklistTokens, dacă da îl invalidăm.
    if not search_token_in_blacklist(token):
        # Dacă nu se află în tabela BlacklistTokens, verificăm dacă
        # momentul expirării coincide cu momentul actual, în caz afirmativ îl invalidăm.
        now = datetime.utcnow()
        if exp < now:
            add_token_to_blacklist(jti, token, exp, iat)
            delete_by_jti(jti)
            return False
        return True
    else:
        return False


def get_jti(token):
    """
        Funcția get_jti extrage identificatorul unic al token-ului din acesta.

        Parametrii:
            token (str): token-ul utilizatorului.

        Returnează:
            (str): identificatorul token-ului.
    """
    decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    jti = decoded_jwt['jti']
    return jti
