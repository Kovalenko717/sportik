from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from  config import  host, user, password, name_db
from flask import Flask, render_template, url_for, request, flash, session, redirect
import re
import cli



app = Flask(__name__)
app.secret_key = 'mamapomogy'


try:
    conn = psycopg2.connect(
        database=name_db,
        user=user,
        password=password,
        host=host
    )
except:
    print('no connection')


def create_db():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(cli.create_database())

@app.route('/')
def index():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM client;')
    list_users = cursor.fetchall()
    return render_template("index.html", list_users=list_users)

#регистрация пользователя
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Проверка, существуют ли запросы на публикацию "имя пользователя"
    # и "пароль"
    if request.method == 'POST' and 'user_login' in request.form and 'password' in request.form:
        # Создаются переменные для удобного доступа к ним
        user_name = request.form['user_name']
        user_login = request.form['user_login']
        user_phone = request.form['user_phone']
        password = request.form['password']
        _hashed_password = generate_password_hash(password)

        # Проверка на существование учетной записи
        cursor.execute(
            'SELECT * FROM client WHERE client_login = %s', (user_login,))
        account = cursor.fetchone()

        # Если учетная запись существует - проверки на ошибку и валидацию
        if account:
            flash('Учетная запись уже была создана')
        elif not re.match(r'[A-Za-z0-9]+', user_login):
            flash('Имя пользователя должно содержать только символы и цифры!')
        elif not user_login or not password or not user_name:
            flash('Необходимо заполнить форму!')
        else:
            # Если учетная запись не существует и данные формы действительны, то в таблицу пользователей заносится
            # новая учетная запись
            cursor.execute(
                "INSERT INTO client (client_name, client_login, client_phone, client_password) VALUES (%s,%s,%s,%s)",
                           (user_name, user_login, user_phone, _hashed_password))
            conn.commit()
            return redirect(url_for('login'))

    elif request.method == 'POST':
        flash('Please fill out the form!')

    return render_template("registration.html")

#авторизация пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Проверка на существование запросов на публикацию "имя пользователя" и
    # "пароль"
    if request.method == 'POST' and 'user_login' in request.form and 'password' in request.form:
        user_login = request.form['user_login']
        password = request.form['password']

        cursor.execute(
            'SELECT * FROM client WHERE client_login = %s', (user_login,))
        account = cursor.fetchone()
        if account:
            password_rs = account['client_password']
            # Если учетная запись существует в таблице пользователей в базе данных out
            if check_password_hash(password_rs, password):
                # Создаются данные сеанса
                session['loggedin'] = True
                session['user_login'] = account['client_login']
                session['user_name'] = account['client_name']
                session['id_user'] = account['id_client']
                # Перенаправление на страницу профиля
                return redirect(url_for('profile'))
            else:
                # Учетная запись не существует (пользователя/пароль неверны)
                flash('Неправильное имя пользователя / пароль')
        else:
            # Учетная запись не существует (пользователя/пароль неверны)
            flash('Неправильное имя пользователя / пароль')

    elif request.method == 'POST':
        flash('Необходимо заполнить форму!')

    return render_template("login.html")

#выход из учетной записи
@app.route('/logout')
def logout():
    # Выход пользователя из системы
    session.clear()
    return redirect(url_for('login'))

#профиль пользователя
@app.route('/profile')
def profile():
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM client WHERE client_login = %s', [session['user_login']])
        account = cursor.fetchone()

        # Вывод своих записей на тренировки
        cursor.execute(
            "SELECT numb, id_client FROM client_train WHERE id_client=%s;", [session['id_user']])
        addtrain = cursor.fetchall()

        return render_template("profile.html", account=account, addtrain=addtrain)
    return redirect(url_for('login'))

#расписание доступных тренировок
@app.route('/raspis')
def raspis():
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT numb, date_start, date_finish, id_adm, id_sport, id_gym FROM event_t;")
        show_rasp = cursor.fetchall()

        cursor.execute(
            "SELECT sport_name FROM kind_of_sport;")
        show_sport = cursor.fetchall()

        cursor.execute(
            "SELECT gym_name FROM gym;")
        show_gym = cursor.fetchall()

        cursor.execute(
            "SELECT numb FROM client_train WHERE id_client=%s;", [session['id_user']]);
        number_train = cursor.fetchall()
        print(str(number_train))

        return render_template("raspis.html", show_rasp=show_rasp, show_sport=show_sport, show_gym=show_gym, number_train=number_train)
    return render_template("login.html")

#страница с контактными данными админитраторов
@app.route('/contactAdmin')
def contactAdmin():
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT id_adm, adm_name, adm_login, adm_phone, adm_email FROM adm;")
        user = cursor.fetchall()
        return render_template("contactAdmin.html", user=user)

#страница с информацией для пользователя
@app.route('/aboutus')
def aboutus():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM client;')
    list_users = cursor.fetchall()
    return render_template("aboutus.html", list_users=list_users)

#редактирование профиля пользователя
@app.route('/edit/<int:id_edit>', methods=['GET', 'POST'])
def edit(id_edit):
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT id_client, client_name, client_phone, client_text FROM client WHERE id_client = %s',
                       [id_edit])
        profile_info = cursor.fetchall()

        if request.method == 'POST':
            client_name = request.form['client_name']
            client_phone = request.form['client_phone']
            client_text = request.form['client_text']

            if not client_name or not client_phone or not client_text:
                flash('Необходимо добавить данные!', category='error')
            elif len(client_name) > 50:
                flash('Необходимо добавить данные!', category='error')
            elif len(client_phone) > 50:
                flash('Необходимо добавить данные!', category='error')
            elif len(client_text) > 255:
                flash('Необходимо добавить данные!', category='error')
            else:
                cursor.execute(
                    "UPDATE client SET client_name = %s, client_phone = %s, client_text = %s WHERE id_client = %s",
                    (client_name, client_phone, client_text, id_edit))
                conn.commit()
                flash('Профиль обновлен!', category='success')
                return redirect(url_for('profile', id_edit=session['user_login']))
        return render_template('edit.html', profile_info=profile_info)
    return redirect(url_for('login'))

#авторизация для администратора
@app.route('/admin', methods=['GET', 'POST'])
def logadmin():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Проверка, существуют ли запросы на публикацию "имя пользователя" и
    # "пароль"
    if request.method == 'POST' and 'user_login' in request.form and 'password' in request.form:
        user_login = request.form['user_login']
        password = request.form['password']

        cursor.execute(
            'SELECT * FROM adm WHERE adm_login = %s', (user_login,))
        account = cursor.fetchone()
        if account:
            password_rs = account['adm_password']
            # Если учетная запись существует в таблице пользователей в базе данных out
            if password_rs == password:
                # Создаются данные сеанса
                session['loggedinadmin'] = True
                session['admin_login'] = account['adm_login']
                session['id_admin'] = account['id_adm']
                # Перенаправление на страницу просмотра объявлений пользователей
                return redirect(url_for('listforadmin'))
            else:
                flash('Неправильный логин / пароль')
        else:
            flash('Неправильный логин / пароль')

    elif request.method == 'POST':
        flash('Необходимо заполнить форму!')

    return render_template("logadmin.html")


# выход из сесии администратора
@app.route('/logoutadmin')
def logoutAdmin():
    # Выход пользователя из системы
    session.clear()
    return redirect(url_for('index'))


# список всех пользователей
@app.route('/listforadmin')
def listforadmin():
    if 'loggedinadmin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT id_client, client_name, client_login, client_phone, client_text FROM client;")
        user = cursor.fetchall()

        return render_template("listforadmin.html", user=user)
    return render_template("logadmin.html")

# страница, где адинистратор может создать или удалить запись на определенную тренировку
@app.route('/admrasp')
def admrasp():
    if 'loggedinadmin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT numb, date_start, date_finish, id_adm, id_sport, id_gym FROM event_t;")
        show_rasp = cursor.fetchall()

        cursor.execute(
            "SELECT sport_name FROM kind_of_sport;")
        show_sport = cursor.fetchall()

        cursor.execute(
            "SELECT gym_name FROM gym;")
        show_gym = cursor.fetchall()

        return render_template("admrasp.html", show_rasp=show_rasp, show_sport=show_sport, show_gym=show_gym)
    return render_template("logadmin.html")

# добавление администратором новых расписаний
@app.route('/addevent', methods=['GET', 'POST'])
def addevent():
    if 'loggedinadmin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT numb FROM event_t;")
        list_event = cursor.fetchall()

        cursor.execute("SELECT id_sport, sport_name FROM kind_of_sport;")
        list_sport = cursor.fetchall()

        cursor.execute("SELECT id_gym, gym_name FROM gym;")
        list_gym = cursor.fetchall()


        if request.method == 'POST':
            date_start = request.form['date_start']
            date_finish = request.form['date_finish']
            id_sport = request.form['id_sport']
            id_gym = request.form['id_gym']

            if not date_start or not date_finish or not id_sport or not id_gym:
                flash('Заполните расписание', category='error')
            if len(date_start) > 20:
                flash('Заполните дату', category='error')
            elif len(date_finish) > 20:
                flash('Заполните дату', category='error')
            else:
                cursor.execute(
                    "INSERT INTO event_t (date_start, date_finish, id_adm, id_sport, id_gym) VALUES (%s,%s,%s,%s,%s)",
                               (date_start, date_finish, session['id_admin'], id_sport, id_gym))
                conn.commit()

                flash('Расписание добавлено', category='success')

        return render_template("addevent.html", list_event=list_event, list_sport=list_sport, list_gym=list_gym)
    return redirect(url_for('logadmin'))

# удаление любой тренировки администратором
@app.route('/deleteevent/<int:id_deleteevent>', methods=['GET', 'POST'])
def deleteevent(id_deleteevent):
    if 'loggedinadmin' in session:
        if request.method == 'POST':
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if (request.form.get('yes', None)):
                cursor.execute(
                    "DELETE FROM event_t WHERE numb = %s",
                    [id_deleteevent])
                conn.commit()
            return redirect(url_for('admrasp'))
        return render_template('deleteevent.html')
    return redirect(url_for('logadmin'))

# процесс записи пользователя на тренировку
@app.route('/accept/<int:id_accept>', methods=['GET', 'POST'])
def accept(id_accept):
    if 'loggedin' in session:
        if request.method == 'POST':
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if (request.form.get('yes', None)):
                cursor.execute(
                    "INSERT INTO client_train (numb, id_client) VALUES (%s,%s)",
                        (id_accept, session['id_user']))
                conn.commit()
                return redirect(url_for('raspis', id_accept=session['id_user']))
        return render_template('accept.html')
    return redirect(url_for('logadmin'))

# отмена пользователем записи на тренировку
@app.route('/deletezap/<int:id_deletezap>', methods=['GET', 'POST'])
def deletezap(id_deletezap):
    if request.method == 'POST':
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if (request.form.get('yes', None)):
            cursor.execute(
                "DELETE FROM client_train WHERE numb = %s",
                [id_deletezap])
            conn.commit()
            return redirect(url_for('profile'))
    return render_template('deletezap.html')


# удаление пользователя администратором
@app.route('/deleteuser/<int:id_deleteuser>', methods=['GET', 'POST'])
def deleteuser(id_deleteuser):
    if 'loggedinadmin' in session:
        if request.method == 'POST':
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            if (request.form.get('yes', None)):

                # удаление публикаций пользователя
                cursor.execute(
                    "DELETE FROM client_train WHERE id_client = %s",
                     [id_deleteuser])
                conn.commit()

                 # удаление пользователя
                cursor.execute(
                "DELETE FROM client WHERE id_client = %s",
                [id_deleteuser])
                conn.commit()
            return redirect(url_for('listforadmin'))
        return render_template('deleteuser.html')
    return render_template("logadmin.html")

# получение информации о тренировке, на которую записан пользователь
@app.route('/infotrain/<int:id_train>')
def infotrain(id_train):
        if 'loggedin' in session:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(
                "SELECT numb, date_start, date_finish, id_adm, id_sport, id_gym FROM event_t WHERE numb = %s;",
                (id_train,))
            show_train = cursor.fetchall()

            cursor.execute(
                "SELECT sport_name FROM kind_of_sport WHERE id_sport IN (SELECT id_sport FROM event_t WHERE numb = %s);",
                (id_train,))
            show_sport = cursor.fetchall()

            cursor.execute(
                "SELECT gym_name FROM gym WHERE id_gym IN (SELECT id_gym FROM event_t WHERE numb = %s);",
                (id_train,))
            show_gym = cursor.fetchall()

            cursor.execute(
                "SELECT numb FROM client_train WHERE id_client =%s;", [session['id_user']]);
            number_train = cursor.fetchall()

            return render_template("infotrain.html", show_train=show_train, show_sport=show_sport, show_gym=show_gym, number_train=number_train)
        return render_template("login.html")

# просмотр администратором тренировок, на которые записан каждый пользователь
@app.route('/showclients/<int:id_prof>')
def showclients(id_prof):
    if 'loggedinadmin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "SELECT numb, id_client FROM client_train WHERE id_client =%s;",
            (id_prof,))
        show_train = cursor.fetchall()

        return render_template("showclients.html", show_train=show_train)
    return render_template("logadmin.html")

if __name__ == "__main__":
    app.run(debug=True)


