import pyodbc
from flask import Flask, request
import datetime
import time
import graph_database
import map
import jwtUtilities
import database_opperations
import jwt
import re
from config import SECRET_KEY
app = Flask(__name__)


@app.route('/api/login', methods=['POST'])
def login():
    """
        Endpoint pentru operația de autentificare.

        Verifică corectitudinea informațiilor de conectare
        introduse de utilizator.

        Request Headers:
            - Content-Type: application/json

        Request Body:
            - username (str): denumirea utilzatorului
            - password (str): parola utilzatorului

        Returns:
            - 200 (OK) - împreună cu token-ul utilizatorului în urma unei
                        autentificări reușite;
            - 401 (Unauthorized) - parola introdusă este greșită.
            - 404 (Not Found) - utilizatorul nu există;
    """
    username = request.json.get('username')
    password = request.json.get('password')
    # Extragem parola utilizatorului din baza de date.
    p = database_opperations.get_user_info(username)
    # Dacă valoarea returnată este un dicționar gol înseamnă că nu există.
    if p == {}:
        return {"error": "Nu exista utilizatorul"}, 404
    else:
        # Verificăm dacă parola coincide cu parola din baza de date.
        if jwtUtilities.verify_password(password, p["password"]):
            # Creăm token-ul.
            token = jwtUtilities.get_token(username)
            return {"response": str(token)}, 200
        else:
            return {"eroare": "Parola gresita"}, 401


@app.route('/api/logout', methods=['GET'])
def logout():
    """
        Endpoint pentru operația de deconectare.

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (OK) - deconectare reușită;
            - 401 (Unauthorized) - token invalid.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Extragem câmpul jti din jwt.
        decoded_jwt = jwt.decode(auth_token, SECRET_KEY, algorithms=['HS256'])
        jti = decoded_jwt['jti']
        iat = datetime.datetime.fromtimestamp(decoded_jwt['iat'])
        exp = datetime.datetime.fromtimestamp(decoded_jwt['exp'])
        # Adăugăm token-ul în tabela cu token-uri invalidate.
        database_opperations.add_token_to_blacklist(jti, auth_token, exp, iat)
        # Ștergem informațiile corespunzătoare lui din baza de date Neo4j
        # în cazul în care să deconectat fără să marcheze zona terminată.
        graph_database.delete_by_jti(jti)
        return {"response": "Loged out"}, 200


@app.route('/api/users', methods=['POST'])
def add_user():
    """
        Endpoint pentru crearea unui nou cont de utilizator.

        Request Body:
            - username (str): denumirea utilizatorului
            - password (str): parola utilizatorului
            - email (str): adresa de email a utilizatorului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 201 (Created) - adăugare utilizator reușită;
            - 400 (Bad Request) - încălcare constrângeri de tip check;
            - 409 (Conflict) - încălcare constrângeri de tip unique key.
    """
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    # Parola aceasta se salvează în baza de date împreună cu numele utilizatorului.
    # Din baza de date selectăm id-ul rolului de user pentru a îl adăuga în
    # informațiile utilizatorului.
    try:
        database_opperations.add_user(username, password, email)
        database_opperations.add_role_to_user(username)
        return {"response": "registered"}, 201
    except pyodbc.IntegrityError as e:
        # Tratăm erorile cauzate de încălcarea constrângerilor de tip unique key sau check:

        # Pattern pentru extragerea denumirii constrângerii de tip unique key.
        patternUK = r'IX_Users_([A-Za-z]+)'

        # Pattern pentru extragerea denumirii constrângerii de tip check.
        patternCK = r'CK_Users_([A-Za-z]+)'

        # Extragem valorile corespunzătoare din textul erorii.
        matchesUK = re.findall(patternUK, str(e.args[1]))

        # Dacă eroarea generată este cauzată de încălcarea constrângerii de tip unique key
        # funcția returnează numele constrângerii împreună cu codul de eroare.
        if matchesUK:
            return {"error": str(matchesUK[0])}, 409
        else:
            # În caz contrar eroarea este cauzată de încălcarea unei constrângeri de tip check.
            matchesCK = re.findall(patternCK, str(e.args[1]))
            # Returnează numele constrângerii împreună cu codul de eroare.
            return {"error": str(matchesCK[0])}, 400


@app.route('/api/users', methods=['GET'])
def get_user_role():
    """
        Endpoint pentru determinarea rolului utilizatorului.

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (OK) - împreună cu denumirea rolului utilizatorului
                            în cazul unei operații reușite;
            - 401 (Unauthorized) - token-ul este invalid.
            - 404 (Not Found) - utilizatorul nu există.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Verificăm dacă există utilizatorul.
        user_id = database_opperations.check_user_exists(auth_token)
        if user_id is None:
            return {"error": "Utilizatorul nu exista!"}, 404
        else:
            # Funcția returnează rolul utilizatorului.
            info = database_opperations.get_user_role(user_id)
            return {"response": info}, 200


@app.route('/api/users', methods=['DELETE'])
def delete_account():
    """
        Endpoint pentru ștergerea unui cont de utilizator.

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 204 (No Content) - ștergere utilizator reușită;
            - 401 (Unauthorized) - token invalid.
            - 404 (Not Found) - utilizatorul nu există.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Verificăm dacă există utilizatorul.
        user_id = database_opperations.check_user_exists(auth_token)
        if user_id is None:
            return {"error": "Nu exista utilizatorul"}, 404
        else:
            # Ștergem contul utilizatorului.
            database_opperations.delete_user_account(user_id)
            return {"message": "User account deleted"}, 204


@app.route('/api/users/neighbourhoods', methods=['GET'])
def check_user_done():
    """
        Endpoint utilizat pentru a verifica dacă utilizatorul a
        terminat sau nu de parcurs zona aleasă.

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (OK) - împreună cu o valoare de tip boolean
                            în cazul unei cereri reușite;
            - 401 (Unauthorized) - token invalid.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        check = database_opperations.check_if_user_is_done(auth_token)
        return {"response": check}, 200


@app.route('/api/users/neighbourhoods', methods=['POST'])
def add_neighbourhood_user():
    """
        Endpoint pentru ascoierea dintre utilizator și cartier.

        Request Body:
            - zona (str): denumirea cartierului
            - oras (str): denumirea orașului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (OK) - adăugare informații necesare reușită;
            - 404 (Not Found) - utilizatorul nu există.
            - 401 (Unauthorized) - token invalid;
    """
    zona = request.json.get("zona")
    oras = request.json.get("oras")

    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        user_id = database_opperations.check_user_exists(auth_token)
        if user_id is None:
            return {"error": "Utilizatorul nu exista"}, 404
        else:
            database_opperations.add_zona_to_user(user_id, zona, oras)
            return {"response": "Adaugare reusita!"}, 200


@app.route('/api/users/neighbourhoods', methods=['PUT'])
def mark_done():
    """
        Endpoint pentru marcarea zonei ca fiind parcursă.

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (Ok) - actualizare reușită a informațiilor
                            din tabela de join;
            - 401 (Unauthorized) - token invalid;
            - 404 (Not Found) - utilizatorul nu există;
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Verificăm dacă utilizatorul există.
        user_id = database_opperations.check_user_exists(auth_token)
        if user_id is None:
            return {"error": "Utilizatorul nu exista"}, 404
        else:
            # Marcăm faptul că acesta a terminat de parcurs zona.
            id = database_opperations.done_zona(user_id)
            # Eliminăm înregistrarea aferentă lui din baza Neo4j.
            jti = jwtUtilities.get_jti(auth_token)
            start_time = time.time()
            graph_database.delete_nodes(jti, id)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print("STERGERE DIGRAF: {:.2f} seconds".format(elapsed_time))
            return {"response": "Done"}, 200


@app.route('/api/cities', methods=['POST'])
def add_city():
    """
        Endpoint pentru înregistrarea unui nou oraș.

        Request Body:
            - oras (str): denumirea orașului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 201 (Created) - adăugare de oraș reușită;
            - 401 (Unauthorized) - token invalid;
            - 403 (Forbidden) - utilizatorul nu are rolul de administrator
                        și nu poate realiza operația;
            - 404 (Not Found) - utilizatorul sau orașul nu există;
            - 409 (Conflict) - încălcare constrângeri de tip unique key.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    nume_oras = request.json.get("oras")
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Verificăm dacă utilizatorul există.
        user_id = database_opperations.check_user_exists(auth_token)
        if user_id is None:
            return {"error": "Utilizatorul nu exista"}, 404
        else:
            # Dacă acesta există, verificăm dacă are rol de adminstrator.
            # În caz contrar acesta nu poate realiza operația dorită și este
            # returnat un mesaj de eroare corespunzător.
            if database_opperations.check_if_admin(user_id):
                # Verificăm dacă denumirea orașului este validă.
                if map.check_city(nume_oras):
                    # Încercăm să inserăm valoarea în tabelă.
                    try:
                        database_opperations.add_city(nume_oras)
                        return {"response": 'done'}, 201
                    except pyodbc.IntegrityError as e:
                        # Tratare erori cauzate de încălcarea constrângerilor de
                        # tip unique key sau check:

                        # Pattern pentru extragerea denumirii constrângerii de
                        # tip unique key.
                        patternUK = r'IX_Cities'

                        # Pattern pentru extragerea denumirii constrângerii
                        # de tip check.
                        patternCK = r'CK_Cities'

                        # Extragem valorile corespunzătoare din textul erorii.
                        matchesUK = re.findall(patternUK, str(e.args[1]))

                        # Dacă eroarea generată este de la încălcarea constrângerii
                        # de tip unique key returnăm numele constrângerii.
                        if matchesUK:
                            return {"error": str(matchesUK[0])}, 409
                        else:
                            # În caz contrar, eroarea este cauzată de încălcarea
                            # unei constrângeri de tip check.
                            matchesCK = re.findall(patternCK, str(e.args[1]))
                            # Returnăm numele constrângerii.
                            return {"error": str(matchesCK[0])}, 400
                else:
                    return {"error": "Nu exista orasul!"}, 404
            else:
                return {"error": "Operatie nepermisa pentru utilizator de tip user"}, 403


@app.route('/api/cities/<city>', methods=['DELETE'])
def delete_city(city):
    """
        Endpoint pentru ștergerea unui oraș din tabelă.

        Request Parameters:
            - city (str): denumirea orașului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 204 (No Content) - ștergerea orașului reușită;
            - 401 (Unauthorized) - token invalid;
            - 403 (Forbidden) - utilizatorul nu are rolul de administrator
                                    și nu poate realiza operația;
            - 404 (Not Found) - utilizatorul sau orașul nu există;
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Verificăm dacă utilizatorul există.
        user_id = database_opperations.check_user_exists(auth_token)
        if user_id is None:
            return {"error": "Utilizatorul nu exista"}, 404
        else:
            # Dacă acesta există, verificăm dacă are rol de adminstrator.
            # În caz contrar, acesta nu poate realiza operația dorită și este
            # returnat un mesaj de eroare corespunzător.
            if database_opperations.check_if_admin(user_id):
                # Extragem identificatorul orașului din tabelă.
                id_oras = database_opperations.get_city_id(city)
                if id_oras is None:
                    return {"error": "Nu exista in baza de date!"}, 404
                else:
                    # Dacă orașul există, îl putem șterge.
                    database_opperations.delete_city(id_oras)
                    return {"response": 'City deleted!'}, 204
            else:
                return {"error": "Operatie nepermisa pentru utilizator de tip user"}, 403


@app.route('/api/cities', methods=['GET'])
def get_cities():
    """
        Endpoint pentru obținerea listei de orașe salvate în baza de date.

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (Ok) - împreună cu lista de nume a orașelor în
                        urma unei cereri reușite;
            - 401 (Unauthorized) - token invalid;
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        names = database_opperations.get_cities()
        return {"response": names}, 200


@app.route('/api/neighbourhoods', methods=['POST'])
def add_neighbourhood():
    """
        Endpoint pentru adăugarea unui nou cartier.

        Request Body:
            - zona (str): denumirea cartierului
            - oras (str): denumirea orașului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 201 (Created) - adăugare de cartier reușită;
            - 401 (Unauthorized) - token invalid;
            - 403 (Forbidden) - utilizatorul nu are rolul de administrator
                            și nu poate realiza operația;
            - 404 (Not Found) - utilizatorul nu există;
            - 409 (Conflict) - încălcare constrângeri de tip unique key.
    """
    zona = request.json.get("zona")
    oras = request.json.get("oras")
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Pentru început verificăm dacă utilizatorul există.
        id_user = database_opperations.check_user_exists(auth_token)
        if id_user is None:
            return {"error": "Utilizatorul nu exista!"}, 404
        else:
            # Dacă acesta există, verificăm dacă are rol de adminstrator.
            # În caz contrar, acesta nu poate realiza operația dorită și este
            # returnat un mesaj de eroare corespunzător.
            if database_opperations.check_if_admin(id_user):
                id_oras = database_opperations.get_city_id(oras)
                if id_oras is None:
                    return {"error": "Orașul nu există în baza de date!"}, 404
                else:  # Verificăm dacă adresa este validă.
                    if map.check_address(zona, oras):
                        # În caz afirmativ, verificăm dacă aceasta există deja în baza de date.
                        if database_opperations.check_neighbourhood_exists(zona, id_oras):
                            return {"error": "Cartierul există deja în listă!"}, 409
                        else:
                            database_opperations.add_cartier(zona, oras)
                            return {"response": 'Adaugare reusita.'}, 201
                    else:
                        return {"error": "Cartierul nu există!"}, 404
            else:
                return {"error": "Operație nepermisă pentru utilizator de tip user"}, 403


@app.route('/api/neighbourhoods/<city>/<zona>', methods=['DELETE'])
def delete_neighbourhood(city, zona):
    """
        Endpoint pentru ștergerea unui cartier.

        Request Parameters:
            - zona (str): denumirea cartierului
            - city (str): denumirea orașului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 204 (No Content) - ștergerea cartierului reușită;
            - 401 (Unauthorized) - token invalid;
            - 403 (Forbidden) - utilizatorul nu are rolul de administrator
                                    și nu poate realiza operația;
            - 404 (Not Found) - utilizatorul, cartierul sau orașul
                                    căutat nu există;
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token invalid!"}, 401
    else:
        # Verificăm dacă utilizatorul există
        id_user = database_opperations.check_user_exists(auth_token)
        if id_user is None:
            return {"error": "Utilizatorul nu există !"}, 404
        else:
            # Dacă acesta există, verificăm dacă are rol de adminstrator.
            # În caz contrar, acesta nu poate realiza operația dorită și este
            # returnat un mesaj de eroare corespunzător.
            if database_opperations.check_if_admin(id_user):
                # Extragem identificatorul orașului din tabelă.
                id_oras = database_opperations.get_city_id(city)
                if id_oras is None:
                    return {"error": "Orașul nu există în baza de date!"}, 404
                else:
                    # Verificăm dacă valoarea pe care dorim să o ștergem există în tabelă.
                    # Dacă există o ștergem, în caz contrar returnăm un mesaj de eroare.
                    if database_opperations.check_neighbourhood_exists(zona, id_oras):
                        database_opperations.delete_cartier(id_oras, zona)
                        return {"response": 'Cartier șters cu succes'}, 204
                    else:
                        return {"error": "Cartierul nu există în orașul selectat!"}, 404
            else:
                return {"error": "Operație nepermisă pentru utilizator de tip user"}, 403


@app.route('/api/neighbourhoods', methods=['GET'])
def get_free_neighbourhoods():
    """
        Endpoint pentru obținerea tuturor cartierelor care pot
        fi parcurse din baza de date care se află
        într-un oraș dat.

        Request Parameters:
            - city (str): denumirea orașului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (Ok) - împreună cu o listă care conține numele
                        cartierelor din orașul primit în crerere în
                        urma unei cereri reușite;
            - 401 (Unauthorized) - token invalid;
    """
    city = request.args.get('city')
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"message": "Token expirat!"}, 401
    else:
        names = database_opperations.get_free_neighbourhoods(city)
        return {"response": names}, 200


@app.route('/api/neighbourhoods/<city>', methods=['GET'])
def get_neighbourhoods(city):
    """
        Endpoint pentru obținerea tuturor cartierelor
        din baza de date care se află
        într-un oraș dat.

        Request Parameters:
            - city (str): denumirea orașului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (Ok) - împreună cu o listă care conține numele
                        cartierelor din orașul primit în crerere în
                        urma unei cereri reușite;
            - 401 (Unauthorized) - token invalid;
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"message": "Token expirat!"}, 401
    else:
        names = database_opperations.get_all_neighbourhoods(city)
        return {"response": names}, 200


@app.route('/api/graph', methods=['POST'])
def create_graph():
    """
        Endpoint pentru crearea și
        determinarea coordonatelor nodurilor digrafului.

        Request Body:
            - denumire (str): denumirea cartierului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (OK) - împreună cu dicționarul care conține
                    nodurile și coordonatele aferente
                    în cazul unei operații reușite;
            - 400 (Bad Request) - eroare la crearea digrafului.
            - 401 (Unauthorized) - token invalid.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]

    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        location = request.json.get('location')
        size = request.json.get("size")
        denumire = request.json.get("denumire")
        # Dacă toți parametrii sunt diferiți de 0 atunci funcția returnează coordonatele.
        id_cartier = database_opperations.get_neighbourhood_id_from_name(denumire)
        # Extragem coordonatele corespunzătoare nodurilor digrafului.
        vals = map.coords(location, size, jwtUtilities.get_jti(auth_token), id_cartier)
        if vals is None:
            # Eroare la crearea digrafului.
            return {"error": "Eroare la crearea digrafului."}, 400
        else:
            return {"result": vals}, 200


@app.route('/api/graph/<denumire>', methods=['GET'])
def get_adjacency_matrix(denumire):
    """
        Endpoint pentru determinarea matricei de adiacență și a indecșilor nodurilor.

        Request Parameters:
            - denumire (str): denumirea cartierului

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (OK) - împreună cu matricea de adiacență și
                    dicționarul de noduri în urma unei operații reușite;
            - 400 (Bad Request) - eroare la crearea digrafului.
            - 401 (Unauthorized) - token invalid.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]

    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        id_cartier = database_opperations.get_neighbourhood_id_from_name(denumire)
        [matrix, nodes] = map.get_adj_matrix(jwtUtilities.get_jti(auth_token), id_cartier)
        code = 200
        if matrix is None and nodes is None:
            code = 400
        return {"matrix": matrix, "nodes": nodes}, code


@app.route('/api/garph/<zona>/path', methods=['GET'])
def get_path(zona):
    """
        Endpoint pentru extragerea traseului optimizat.

        Request Parameters:
            - zona (str): denumirea zonei de parcurs

        Request Headers:
            - Content-Type: application/json
            - Authorization: Bearer <access_token>

        Returns:
            - 200 (OK) - împreună cu lista care conține traseul
                    optimizat în urma unei cereri reușite;
            - 400 (Bad Request) - digraful nu conține un ciclu eulerian
                                  după aplicarea algoritmului sau
                                  algoritmul nu poate fi aplicat asupra acestuia.
            - 401 (Unauthorized) - token invalid.
    """
    auth_header = request.headers.get('Authorization')
    auth_token = auth_header.split(' ')[1]
    if not jwtUtilities.authorize_token(auth_token):
        return {"error": "Token expirat!"}, 401
    else:
        # Determinarea traseului optimizat.
        id_cartier = database_opperations.get_neighbourhood_id_from_name(zona)
        start_time = time.time()
        path, streets = map.get_path(jwtUtilities.get_jti(auth_token), id_cartier)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("TRASEU: {:.2f} seconds".format(elapsed_time))
        # Dacă valoarea determinată anterior este None înseamnă că pe acest digraf nu poate fi
        # rezolvată problema poștașului chinez.
        if path is None:
            return {"error": "Nu poate fi găsit un ciclu eulerian în acest digraf."}, 400
        return {"path": path, "streets": streets}, 200


if __name__ == '__main__':
    app.run(debug=True)
