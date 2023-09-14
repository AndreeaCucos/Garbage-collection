from datetime import datetime, timedelta

import config
import pyodbc
import bcrypt
import jwt
from config import SECRET_KEY

conn = pyodbc.connect(
    f'Driver={config.sql};Server={config.server};Database={config.database};UID={config.username};PWD={config.password};Trusted_Connection=True;')


def check_user_exists(token):
    """
        Funcția check_user_exists interoghează baza de date pentru
        a verifica existența utilizatorului.

        Parametrii:
            token (str) - token-ul utilizatorului.

        Returnează: None în cazul în care acesta nu există,
                    identificatorul utilizatorului în caz
                    contrar.
    """
    cursor = conn.cursor()
    # Decodificare token utilizator pentru a extrage câmpul 'sub'
    # în care se află id-ul utilizatorului.
    decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    # Căutăm utilizatorul în tabela Users pentru a verifica existența acestuia.
    cursor.execute("SELECT * FROM Users WHERE user_id=?",
                   decoded_jwt['sub'])
    rows = cursor.fetchall()
    if not rows:
        # Dacă interogarea întoarce o listă goală înseamnă că acest
        # id nu există în baza de date.
        return None
    else:
        user_id = 0
        for row in rows:
            user_id = row[0]
        return int(user_id)


def check_if_admin(id_user):
    """
        Funcția check_if_admin verifică dacă utilizatorul care realizează
        operația are rolul de administrator al aplicației.

        Parametrii:
            id_user (int): identificatorul utilizatorului

        Returnează: boolean: True în cazul în care este administrator,
                            False în caz contrar.

    """
    cursor = conn.cursor()
    # Selectăm identificatorul rolului său din tabela UserRoles pe baza
    # identificatorului utilizatorului.
    cursor.execute("SELECT role_id FROM UserRoles WHERE user_id=?",
                   id_user)
    rows = cursor.fetchall()
    role_id = 0
    for row in rows:
        role_id = int(row[0])
    # Căutăm numele rolului în tabela Roles.
    cursor.execute("SELECT rolename FROM Roles WHERE role_id=?",
                   role_id)
    rows = cursor.fetchall()
    rolename = ""
    for row in rows:
        rolename = row[0]
    if rolename == "admin":
        return True
    else:
        return False


def add_user(username, password, email):
    """
         Funcția add_user se ocupă cu adăugarea unui nou utilizator
         în tabela Users. Parola introdusă de utilizator este
         codificată utilizând funcția hashpw din bcrypt.

         Parametrii:
            username (str): denumirea utilizatorului
            password (str): parola utilizatorului
            email (str): adresa de email a utilizatorului
    """
    cursor = conn.cursor()
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    cursor.execute("INSERT INTO Users(username, password, email) "
                   "VALUES(?, ?, ?)",
                   (username, hashed_password, email))

    conn.commit()
    cursor.close()


def delete_user_account(user_id):
    """
        Funcția delete_user_account permite utilizatorului să își
        șteargă contul din aplicație.

        Parametrii:
            user_id (int): identificatorul utilizatorului
    """
    cursor = conn.cursor()
    # Selectăm înregistrările din tabela de join asociate lui.
    cursor.execute("SELECT * FROM JoinUserNeighbourhood "
                   "WHERE id_user=?", user_id)
    rows = cursor.fetchall()
    if rows:
        # Ștergem înregistrările aferente lui.
        cursor.execute("DELETE FROM JoinUserNeighbourhood "
                       "WHERE id_user=?", user_id)
    # Ștergem asocierea cu rolul din tabela UserRoles
    cursor.execute("DELETE FROM UserRoles WHERE user_id=?", user_id)
    # Ștergem utilizatorul din tabela Users.
    cursor.execute("DELETE FROM Users WHERE user_id=?", user_id)
    conn.commit()
    cursor.close()


def add_token_to_blacklist(jti, token, exp, iat):
    """
        Funcția add_token_to_blacklist salvează în tabela
        BlacklistTokens token-urile invalide.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului
                    utilizatorului
            token (str): token-ul utilizatorului
            exp (Date): momentul în care acesta va expira
            iat (Date): momentul în care a fost creat
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO BlacklistTokens VALUES(?, ?, ?, ?)",
                   jti, token, exp, iat)
    conn.commit()
    cursor.close()


def get_user_info(username):
    """
        Funcția get_user_info se ocupă cu extragerea informațiilor
        utilizatorului din tabela Users (id, password, email) și salvarea
        acestora într-un dicționar.

        Parametrii:
            username (str): denumirea utilizatorului

        Returnează:
            (Dictionary) : dicționar care conține informațiile
                            utilizatorului căutat.
    """
    cursor = conn.cursor()
    info = {}  # Dicționar în care sunt salvate informatiile utilizatorului.
    cursor.execute(f"SELECT * FROM Users WHERE username=?", (username,))
    rows = cursor.fetchall()
    if rows:
        info = {
            "id": 0,
            "password": "",
            "email": "",
        }
        for row in rows:
            info["id"] = row[0]
            info["password"] = row[2]
            info["email"] = row[3]
    conn.commit()
    cursor.close()
    return info


def get_user_role(user_id):
    """
        Funcția get_user_role întoarce rolul utilizatorului.

        Parametrii:
            user_id (int): identificatorul utilizatorului

        Returnează:
            (str): denumirea rolului utilizatorului
    """
    cursor = conn.cursor()
    # Selectăm rolul utilizator din tabela join UserRoles.
    cursor.execute(f"SELECT role_id FROM UserRoles WHERE user_id=?", user_id)
    rows = cursor.fetchall()
    role_id = 0
    for row in rows:
        role_id = row[0]
    # Selectăm numele rolului din tabela Roles.
    cursor.execute(f'SELECT rolename FROM Roles WHERE role_id=?', role_id)
    rows = cursor.fetchall()
    conn.commit()
    cursor.close()
    rolename = ""
    for row in rows:
        rolename = row[0]
    return rolename


def add_role_to_user(username):
    """
        Funcția add_role_to_user realizează asocierea dintre identificatorul
        utilizatorului și identificatorul rolului care i se asociază la creare.

        Parametrii:
            username (str): denumirea utilizatorului
    """
    cursor = conn.cursor()
    # Extragem identificatorul utilizatorului din tabela Users.
    cursor.execute("SELECT user_id FROM Users WHERE username=?", username)
    rows = cursor.fetchall()
    user_id = 0
    for row in rows:
        user_id = row[0]
    # Inserăm în tebala de join identificatorul utilizatorului și a rolului
    # cu denumirea „user”.
    cursor.execute("INSERT INTO UserRoles (user_id, role_id) SELECT "
                   "(SELECT user_id FROM Users WHERE user_id=?),"
                   "(SELECT role_id FROM Roles WHERE rolename='user')",
                   user_id)
    conn.commit()
    cursor.close()


def search_token_in_blacklist(token):
    """
        Funcția search_token_in_blacklist permite căutarea unui token
        în tabela BlacklistTokens în care sunt salvate token-urile invalidate.
        Este utilizată pentru a verifica validitatea unui token.

        Parametrii:
            token (str): token-ul utilizatorului.

        Returnează:
            (boolean): True dacă există în tabelă, False în caz contrar.
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM BlacklistTokens WHERE token=?", (token,))
    row = cursor.fetchone()
    if row is None:
        return False
    return True


def get_cities():
    """
        Funcția get_cities întoarce toate orașele salvate în tabela Cities.

        Returnează:
            names (list): conține numele orașelor salvate în tabelă.
    """
    cursor = conn.cursor()
    cursor.execute(f"select * from Cities")
    names = []
    rows = cursor.fetchall()
    for row in rows:
        names.append(row[1])
    return names


def check_neighbourhood_exists(nume, id_oras):
    """
        Funcția check_neighbourhood_exists verifică dacă denumirea unui
        cartier există în baza de date.

        Parametrii:
            nume (str): denumirea cartierului
            oras (str): denumirea orașului în care se află

        Returnează:
            (boolean): True dacă acesta există în tabelă,
                       False în caz contrar
    """
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM Neighbourhoods WHERE id_city=? AND name=?',
                   (id_oras, nume,))
    rows = cursor.fetchall()
    if not rows:
        return False
    return True


def add_cartier(nume, oras):
    """
        Funcția add_cartier adaugă un nou cartier în tabela
        Neighbourhoods.

        Parametrii:
            nume (str): denumirea cartierului.
            oras (str): denumirea orașului în care se află.
    """
    cursor = conn.cursor()
    id_oras = get_city_id(oras)
    cursor.execute(f"INSERT INTO Neighbourhoods VALUES(?, ?)", id_oras, nume)
    conn.commit()
    cursor.close()


def check_exists_neighbouthood(nume, id_oras):
    """
        Funcția check_exists_neighbouthood verifică dacă un cartier există în
        tabela Neighbourhoods.

        Parametrii:
            nume (str): denumirea cartierului căutat.
            id_oras (int): identificatorul orașului în care ar trebui să se afle.

        Returnează:
            (boolean): True dacă acesta există în tabelă, False în caz contrar.
    """
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM Neighbourhoods WHERE name=? AND id_city=?',
                   nume, id_oras)
    rows = cursor.fetchall()
    if not rows:
        return False
    return True


def delete_cartier(id_oras, nume):
    """
        Funcția delete_cartier elimină o înregistrare din tabela Neighbourhoods.

        Parametrii:
            id_oras (int): identificatorul orașului în care se află.
            nume (str): denumirea cartierului căutat.
    """
    cursor = conn.cursor()
    # Verificăm dacă există înregistrări asociate cartierului pe care dorim să îl
    # ștergem în tabela de join. În caz pozitiv, acestea vor fi șterse.

    # Extragem mai întâi identificatorul cartierului
    id_neighbourhood = 0
    cursor.execute("SELECT id FROM Neighbourhoods WHERE name=?", (nume,))
    for row in cursor.fetchall():
        id_neighbourhood = int(row[0])

    cnt = 0
    # Verificăm dacă există în tabela de join.
    cursor.execute("SELECT COUNT(*) FROM JoinUserNeighbourhood "
                   "WHERE id_neighbourhood=?", id_neighbourhood)
    for row in cursor.fetchall():
        cnt = int(row[0])
    if cnt != 0:
        # Există în tabela de join și ștergem înregistrările corespunzătoare lui.
        cursor.execute("DELETE FROM JoinUserNeighbourhood"
                       " WHERE id_neighbourhood=?", id_neighbourhood)
    # Ștergem cartierul.
    cursor.execute(f"DELETE FROM Neighbourhoods "
                   f"WHERE name=? AND id_city=?", nume, id_oras)
    conn.commit()
    cursor.close()


def add_city(oras):
    """
        Funcția add_city adaugă o nouă înregistrare în tabela Cities.

        Parametrii:
            oras (str): denumirea orașului care trebuie adăugat.
    """
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Cities VALUES(?)', oras)
    conn.commit()
    cursor.close()


def delete_city(id_oras):
    """
        Funcția delete_city elimină un oraș din baza de date. În acest sens,
        ținând cont de legătura dintre tabela Neighbourhoods și Cities, mai
        întâi eliminăm înregistrările din tabela Neighbourhoods
        aferente identificatorului orașului pe care utilizatorul dorește
        să îl elimine și ulterior eliminăm orașul din tabela Cities.

        Parametrii:
            id_oras (int): identificatorul orașului.
    """
    cursor = conn.cursor()

    # Extragem din tabela Neighbourhoods identificatoarele cartierelor
    # din orașul respectiv și le salvăm într-o listă.
    ids = []
    cursor.execute('SELECT id FROM Neighbourhoods '
                   'WHERE id_city=?', id_oras)
    for row in cursor.fetchall():
        ids.append(int(row[0]))
    # Ștergem cartierele din tabela de join dintre utilizator și cartier.
    for id in ids:
        cursor.execute('DELETE FROM JoinUserNeighbourhood '
                       'WHERE id_neighbourhood=?', id)
    # Ștergem cartierele din oraș.
    cursor.execute('DELETE FROM Neighbourhoods '
                   'WHERE id_city=?', id_oras)
    # Ștergem orașul.
    cursor.execute('DELETE FROM Cities '
                   'WHERE id_city=?', id_oras)
    conn.commit()
    cursor.close()


def add_zona_to_user(user_id, nume_zona, oras):
    """
        Funcția add_zona_to_user asociază o zonă de
        parcurgere untilizatorului.

        Parametrii:
            user_id (int): identificatorul utilizatorului
                            căruia i se asociază zona.
            nume_zona (str): denumirea cartierului.
            oras (str): denumirea orașului în care se află
                        cartierul.
    """
    cursor = conn.cursor()
    id_oras = get_city_id(oras)
    # Extragem identificatorul înregistrării care are
    # câmpurile name și id_city corespunzătoare.
    cursor.execute('SELECT id FROM Neighbourhoods '
                   'WHERE name=? AND id_city=?',
                   (nume_zona, id_oras))
    rows = cursor.fetchall()
    id_zona = 0
    for row in rows:
        id_zona = int(row[0])
    current_date_time = datetime.today()
    status = 0  # Adăugăm faptul că a început să parcurgă zona.
    cursor.execute(f"INSERT INTO JoinUserNeighbourhood VALUES(?, ?, ?, ?)",
                   user_id, id_zona, current_date_time, status)
    conn.commit()
    cursor.close()


def get_free_neighbourhoods(oras):
    """
        Funcția get_free_neighbourhoods întoarce cartierele
        care nu au fost parcurse săptămâna aceasta și care nu
        sunt în parcurgere în ziua curentă.

        Parametrii:
            oras (str): denumirea orașului în care se află
                        cartierele.

        Returnează:
            names (list): listă care conține denumirile orașelor
                            disponibile.
    """
    cursor = conn.cursor()
    id_oras = get_city_id(oras)
    cursor.execute('SELECT id_neighbourhood, data FROM JoinUserNeighbourhood')
    rows = cursor.fetchall()
    # Creăm o listă care va conține identificatorii tuturor cartierelor care sunt
    # în parcurgere.
    neighbourhoods = []
    if rows:
        for row in rows:
            data = row[1]
            current_time = datetime.today().date()
            # Verificăm dacă data la care a avut loc parcurgerea este cea curentă.
            # În caz afirmativ o salvăm în lista neighbourhoods.
            if data == str(current_time):
                neighbourhoods.append(int(row[0]))
            # Trebuie să verificăm și dacă a trecut o săptămână de la data care
            # a fost salvată în tabelă.
            # Dacă nu a trecut o săptămână, salvăm identificatorul cartierului în
            # lista neighbourhoods deoarece
            # înseamnă că nu trebuie colectate deșeurile încă.
            data_saptamana_viitoare = datetime.strptime(data, "%Y-%m-%d").date() + \
                                      timedelta(weeks=1)
            if current_time < data_saptamana_viitoare:
                neighbourhoods.append(int(row[0]))
    names = []
    if not neighbourhoods:
        # Dacă lista este goală înseamnă că nu sunt cartiere în parcurgere în ziua
        # curentă, deci putem selecta toate cartierele din orașul ales.
        cursor.execute('SELECT name FROM Neighbourhoods where id_city=?', id_oras)

        rows = cursor.fetchall()
        for row in rows:
            names.append(row[0])
    else:
        # În cazul în care lista nu este goală, funcția întoarce denumirile cartierelor
        # ale căror identificatori nu se află în lista neighbourhoods.
        placeholders = ','.join('?' * len(neighbourhoods))
        query = f"SELECT name FROM Neighbourhoods " \
                f"WHERE id NOT IN ({placeholders}) " \
                f"and id_city=?"

        parameters = neighbourhoods + [id_oras]
        cursor.execute(query, parameters)

        rows = cursor.fetchall()
        for row in rows:
            names.append(row[0])
    conn.commit()
    cursor.close()
    return names


def get_all_neighbourhoods(city):
    """
        Funcția get_all_neighbourhoods întoarce denumirile tuturor
        cartierelor dintr-un oraș.

        Parametrii:
            oras (str): denumirea orașului în care se află cartierele.

        Returnează:
            names (list): listă care conține denumirile cartierelor din
                            orașul trimis ca parametru.
    """
    cursor = conn.cursor()
    id_oras = get_city_id(city)
    neighbourhoods = []
    cursor.execute("SELECT name FROM Neighbourhoods WHERE id_city=?", id_oras)
    for row in cursor.fetchall():
        neighbourhoods.append(row[0])
    return neighbourhoods


def get_city_id(oras):
    """
        Funcția get_city_id extrage identificatorul orașului cu denumirea
        căutată din tabela Cities.

        Parametrii:
            oras (str): denumirea orașului căutat

        Returnează:
            None: în cazul în care orașul nu există în tabelă.
            id_oras (int): identificatorul orașului căutat.
    """
    cursor = conn.cursor()
    cursor.execute("select * from Cities where city_name=?", (str(oras),))
    rows = cursor.fetchall()
    id_oras = 0
    if not rows:
        return None
    for row in rows:
        id_oras = int(row[0])
    return id_oras


def check_if_user_is_done(token):
    """
        Funcția check_if_user_is_done verifică dacă utilizatorul a marcat
        încheierea parcurgerii cartierului ales.

        Parametrii:
            token (str): token-ul utilizatorului

        Returnează:
            (int): 1 în cazul în care nu există înregistrări aferente lui
                        în tabela de join sau în cazul în care acesta a marcat
                        faptul că a terminat de parcurs zona
                   0 în caz contrar.
    """
    cursor = conn.cursor()
    decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    cursor.execute('SELECT * FROM JoinUserNeighbourhood WHERE id_user=?',
                   decoded_jwt['sub'])
    rows = cursor.fetchall()
    conn.commit()
    cursor.close()
    if not rows:
        return 1  # Nu a parcurs nici un traseu până acum, nu are înregistrări.
    else:
        # Verificăm dacă parcurgerile înregistrate sunt de astăzi
        # și dacă sunt gata.
        for row in rows:
            data = row[2]
            current_time = datetime.today().date()
            status = int(row[3])
            if data == str(current_time):
                if status == 0:
                    # Dacă este de astăzi, funcția returnează
                    # 0 atunci când statusul este 0,
                    # adică nu a terminat
                    # parcurgerea, trebuie să o termine.
                    return 0


def done_zona(user_id):
    """
        Funcția done_zona actualizează tabela JoinUserNeighbourhood, marcând
        faptul că utilizatorul a terminat parcurgerea cartierului.

        Parametrii:
            user_id (int): identificatorul utilzatorului.

        Returnează:
            id (int) : identificatorul cartierului parcurs.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id_neighbourhood FROM JoinUserNeighbourhood "
                   "WHERE id_user=? and status=?", user_id, 0)
    id = 0
    for row in cursor.fetchall():
        id = int(row[0])
    cursor.execute('UPDATE JoinUserNeighbourhood SET status=? WHERE id_user=?',
                   1, user_id)
    conn.commit()
    cursor.close()
    return id


def get_neighbourhood_id_from_name(name):
    """
        Funcția get_neighbourhood_id_from_name extrage identificatorul
        cartierului pe baza denumirii acestuia de forma ora, cartier.

        Parametrii:
            name (str): denumirea cartierului;

        Returnează:
            id (int): identificatorul cartierului.
    """
    cursor = conn.cursor()
    parts = name.split(", ")
    city = parts[0]
    cartier = parts[1]
    print(cartier)
    id_oras = get_city_id(city)
    cursor.execute('SELECT id FROM Neighbourhoods WHERE name=? AND id_city=?',
                   (cartier, id_oras,))
    id = 0
    for row in cursor.fetchall():
        id = int(row[0])
    conn.commit()
    cursor.close()
    return id
