import flask
import logging
import psycopg2
import time
import random
import datetime
import jwt
from functools import wraps
from dotenv import load_dotenv
import os
from flask import request, jsonify

load_dotenv()

app = flask.Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_KEY')

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500,
    'unauthorized': 401
}



##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(
    host="127.0.0.1",
    port='5432',
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

    return db

##########################################################
## AUTHENTICATION HELPERS
##########################################################
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = flask.request.headers.get('Authorization')
        logger.info(f'token: {auth_header}')

        if not auth_header:
            return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Token is missing', 'results': None})

        try:
            payload_data = jwt.decode(auth_header.split(" ")[1], os.getenv('JWT_KEY'), algorithms=["HS256"]) #faz decode
            logger.debug(f'JWT payload: {payload_data}')
        except jwt.ExpiredSignatureError: #se estiver expirado
            return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Token expired', 'results': None})
        except jwt.InvalidTokenError: #token inválido
            print(payload_data)
            return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Invalid token', 'results': None})

        return f(*args, **kwargs)
    return decorated

def token_required_with_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = flask.request.headers.get('Authorization')
            logger.info(f'token: {auth_header}')

            if not auth_header:
                return flask.jsonify({'status': 401, 'errors': 'Token is missing', 'results': None})

            try:
                payload_data = jwt.decode(auth_header.split(" ")[1], os.getenv('JWT_KEY'), algorithms=["HS256"]) #faz decode
                logger.debug(f'JWT payload: {payload_data}')

                
            except jwt.ExpiredSignatureError: #se estiver expirado
                return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Token expired', 'results': None})
            except jwt.InvalidTokenError: #token inválido
                return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Invalid token', 'results': None})
            
            if payload_data.get('role') != required_role:
                return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'You do not have this permission', 'results': None})

            return f(*args, **kwargs)
        return decorated
    return decorator


##########################################################
## ENDPOINTS
##########################################################

@app.route('/dbproj/user', methods=['PUT'])
def login_user():
    data = flask.request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Username and password are required', 'results': None})

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT password, userid FROM utilizador WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user is None:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Username not found', 'results': None})

    if password == user[0]:
        roles = ['admin', 'instructor', 'student']
        for role in roles:
            cursor.execute(f"SELECT utilizador_userid FROM {role} WHERE utilizador_userid=%s", (user[1],))
            userEncontrado = cursor.fetchone()
            if userEncontrado is not None:
                payload_data = {
                    "username": username,
                    "role": role
                }
                break


        resultAuthToken = jwt.encode(payload=payload_data, key=os.getenv('JWT_KEY'))
        response = {'status': StatusCodes['success'], 'errors': None, 'results': resultAuthToken}
        return flask.jsonify(response)
    else:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Password is incorrect', 'results': None})


@app.route('/dbproj/register/student', methods=['POST'])
@token_required
@token_required_with_role('admin')
def register_student():
    conn = db_connection()
    cur = conn.cursor()

    data = flask.request.get_json()

    balance = data.get('balance')
    email = data.get('mail')
    password = data.get('password')
    name= data.get('name')
    age = data.get('age')
    phone_number= data.get('phone_number')
    username = data.get('username')

    if not balance or not email or not password or not name or not age or not phone_number or not username:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Balance, mail, password, name, age, phone number and username are required', 'results': None})

    statement1 = 'INSERT INTO utilizador (mail, password, name,age,phone_number,username) VALUES (%s, %s, %s, %s, %s,%s) returning userid'
    values1 = (email, password,name,age,phone_number, username)

    try:
        cur.execute(statement1, values1)
        
        resultUserId = cur.fetchone()[0]
        # commit the transaction
        conn.commit()

        statement2 = 'INSERT INTO student (balance, utilizador_userid) VALUES (%s,%s)'
        values2 = (balance, resultUserId)

        cur.execute(statement2, values2)
        conn.commit()
        response = {'status': StatusCodes['success'], 'errors': None, 'results': resultUserId}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/student - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(response)

@app.route('/dbproj/register/instructor', methods=['POST'])
@token_required
@token_required_with_role('admin')
def register_instructor():
    conn = db_connection()
    cur = conn.cursor()

    data = flask.request.get_json()

    instructor_type = data.get('type')  # 'coordinator' ou 'staff'
    email = data.get('mail')
    password = data.get('password')
    name = data.get('name')
    age = data.get('age')
    phone_number = data.get('phone_number')
    username = data.get('username')

    if not instructor_type or instructor_type not in ['coordinator', 'staff']:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Instructor type must be "coordinator" or "staff"', 'results': None})

    if not email or not password or not name or not age or not phone_number or not username:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'mail, password, name, age, phone number and username are required', 'results': None})

    statement1 = 'INSERT INTO utilizador (mail, password, name, age, phone_number, username) VALUES (%s, %s, %s, %s, %s, %s) returning userid'
    values1 = (email, password, name, age, phone_number, username)

    try:
        cur.execute(statement1, values1)
        resultUserId = cur.fetchone()[0]
        conn.commit()

        statement2 = 'INSERT INTO instructor (type, utilizador_userid) VALUES (%s, %s)'
        values2 = (instructor_type, resultUserId)

        cur.execute(statement2, values2)
        conn.commit()

        response = {'status': StatusCodes['success'], 'errors': None, 'results': resultUserId}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/instructor - error: {error}')
        conn.rollback()
        response = {'status': StatusCodes['internal_error'], 'errors': str(error), 'results': None}

    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(response)
    
@app.route('/dbproj/enroll_degree/<degree_id>', methods=['POST'])
@token_required
@token_required_with_role('instructor')  # Apenas staff pode usar, mudar ppoiis nao existe a tabela staff
def enroll_degree(degree_id):
    data = flask.request.get_json()
    conn = db_connection()
    cur = conn.cursor()

    student_id = data.get('student_id')
    date = data.get('date')

    if not student_id or not date:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Student ID and date are required', 'results': None})
    try:
        # Verificar se o utilizador autenticado é um instrutor com tipo 'staff'
        cur.execute("""
            SELECT type FROM instructor
            WHERE utilizador_userid = %s
        """, (user_id,))
        result = cur.fetchone()

        if not result or result[0] != 'staff':
            return flask.jsonify({
                'status': StatusCodes['unauthorized'],
                'errors': 'Only instructors of type "staff" can perform this action',
                'results': None
            })

        # Inserir na tabela enrollment
        cur.execute("""
            INSERT INTO enrollment (status, type, data, version_version_id, student_utilizador_userid)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING enrollment_id
        """, (True, 'regular', date, 1, student_id))  # version_id = 1 é exemplo

        enrollment_id = cur.fetchone()[0]

        # Inserir na tabela de ligação com degree
        cur.execute("""
            INSERT INTO enrollment_degree (enrollment_enrollment_id, degree_program_degree_id)
            VALUES (%s, %s)
        """, (enrollment_id, degree_id))

        conn.commit()

        response = {
            'status': StatusCodes['success'],
            'errors': None,
            'results': {'enrollment_id': enrollment_id}
        }
        return flask.jsonify(response)

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/enroll_degree/{degree_id} - error: {error}')
        conn.rollback()
        response = {
            'status': StatusCodes['internal_error'],
            'errors': str(error),
            'results': None
        }

    finally:
        if conn:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/enroll_activity/<activity_id>', methods=['POST'])
@token_required
@token_required_with_role('student')
def enroll_activity(activity_id):
    conn = db_connection()
    cur = conn.cursor()

    # ID do estudante vem do token JWT
    student_id = flask.g.user_id

    try:
        # Verifica se a atividade existe
        cur.execute('SELECT type FROM activities_extra WHERE type = %s', (activity_id,))
        if cur.fetchone() is None:
            return flask.jsonify({
                'status': StatusCodes['not_found'],
                'errors': f'Activity "{activity_id}" not found',
                'results': None
            })

        # Verifica se o estudante já está inscrito na atividade
        cur.execute('''
            SELECT 1 FROM activities_extra_student 
            WHERE activities_extra_type = %s AND student_utilizador_userid = %s
        ''', (activity_id, student_id))
        if cur.fetchone():
            return flask.jsonify({
                'status': StatusCodes['api_error'],
                'errors': 'Student already enrolled in this activity',
                'results': None
            })

        # Inserção
        cur.execute('''
            INSERT INTO activities_extra_student (activities_extra_type, student_utilizador_userid)
            VALUES (%s, %s)
        ''', (activity_id, student_id))

        conn.commit()
        response = {
            'status': StatusCodes['success'],
            'errors': None,
            'results': f'Student {student_id} enrolled in activity "{activity_id}"'
        }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/enroll_activity/{activity_id} - error: {error}')
        conn.rollback()
        response = {
            'status': StatusCodes['internal_error'],
            'errors': str(error),
            'results': None
        }

    finally:
        if conn:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/enroll_course_edition/<course_edition_id>', methods=['POST'])
@token_required
@token_required_with_role('student')
def enroll_course_edition(course_edition_id):
    conn = db_connection()
    cur = conn.cursor()
    
    data = flask.request.get_json()
    #classes = data.get('classes')  # Lista de IDs de turmas (se aplicável), mudar diagrama para tal, ligacao entre enrollment e lesson

    # O ID do aluno pode ser obtido do token, por exemplo:
    student_id = flask.g.user_id  # assumindo que g.user_id contém o utilizador autenticado

    if not course_edition_id or not student_id:
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': 'Course edition ID and student ID are required.',
            'results': None
        })

    try:
        # Inserir em enrollment
        statement1 = '''
            INSERT INTO enrollment (status, type, date, student_utilizador_userid)
            VALUES (%s, %s, CURRENT_DATE, %s)
            RETURNING enrollment_id
        '''
        values1 = (True, 'course', student_id)
        cur.execute(statement1, values1)
        enrollment_id = cur.fetchone()[0]

        # Relacionar com a versão (course_edition)
        statement2 = '''
            INSERT INTO enrollment_version (enrollment_enrollment_id, version_version_id)
            VALUES (%s, %s)
        '''
        values2 = (enrollment_id, course_edition_id)
        cur.execute(statement2, values2)

        # [Opcional] Se houver uma tabela que relacione matrícula com aulas (classes),
        # então inserimos cada uma:
        #if classes:
            #for class_id in classes:
                #cur.execute('''
                    #INSERT INTO enrollment_class (enrollment_id, class_id)
                    #VALUES (%s, %s)
               # ''', (enrollment_id, class_id))

       # conn.commit()
       # response = {
            #'status': StatusCodes['success'],
           # 'errors': None,
           # 'results': enrollment_id
       # }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/enroll_course_edition - error: {error}')
        conn.rollback()
        response = {
            'status': StatusCodes['internal_error'],
            'errors': str(error),
            'results': None
        }
    finally:
        if conn:
            conn.close()
    
    return flask.jsonify(response)

@app.route('/dbproj/submit_grades/<course_edition_id>', methods=['POST'])
@token_required
@token_required_with_role('instructor')  # Apenas instrutores podem aceder
def submit_grades(user_id, course_edition_id):
    conn = db_connection()
    cur = conn.cursor()
    data = flask.request.get_json()

    period = data.get('period')
    grades_list = data.get('grades')  # [[student_id1, grade1], [student_id2, grade2], ...]

    if not period or not grades_list:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Missing period or grades list'})

    try:
        # Verificar se o user_id é um instrutor do tipo 'coordinator'
        cur.execute("""
            SELECT type 
            FROM instructor 
            WHERE utilizador_userid = %s
        """, (user_id,))
        result = cur.fetchone()

        if not result or result[0] != 'coordinator':
            return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Only course coordinators can submit grades'})

        # Verificar se o user_id é o coordenador da edição do curso
        cur.execute("""
            SELECT instructor_utilizador_userid 
            FROM version 
            WHERE version_id = %s
        """, (course_edition_id,))
        version_row = cur.fetchone()

        if not version_row or str(version_row[0]) != str(user_id):
            return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'You are not the coordinator of this course edition'})

        # Inserir notas e associar à edição
        for student_id, grade in grades_list:
            cur.execute("""
                INSERT INTO grades (status, grade, evaluation_period_period_id, instructor_utilizador_userid)
                VALUES (%s, %s, %s, %s)
                RETURNING evaluation_period_period_id
            """, (True, grade, period, user_id))
            grade_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO grades_version (grades_evalution_period_period_id, version_version_id)
                VALUES (%s, %s)
            """, (grade_id, course_edition_id))

        conn.commit()
        return flask.jsonify({'status': StatusCodes['success'], 'errors': None})

    except Exception as e:
        conn.rollback()
        return flask.jsonify({'status': StatusCodes['internal_error'], 'errors': str(e)})
    
    finally:
        if conn:
            conn.close()


@app.route('/dbproj/degree_details/<degree_id>', methods=['GET'])
@token_required
def degree_details(degree_id):

    resultDegreeDetails = [ # TODO
        {
            'course_id': random.randint(1, 200),
            'course_name': "some coure",
            'course_edition_id': random.randint(1, 200),
            'course_edition_year': 2023,
            'capacity': 30,
            'enrolled_count': 27,
            'approved_count': 20,
            'coordinator_id': random.randint(1, 200),
            'instructors': [random.randint(1, 200), random.randint(1, 200)]
        }
    ]

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultDegreeDetails}
    return flask.jsonify(response)

@app.route('/dbproj/top3', methods=['GET'])
@token_required
def top3_students():

    resultTop3 = [ # TODO
        {
            'student_name': "John Doe",
            'average_grade': 15.1,
            'grades': [
                {
                    'course_edition_id': random.randint(1, 200),
                    'course_edition_name': "some course",
                    'grade': 15.1,
                    'date': datetime.datetime(2024, 5, 12)
                }
            ],
            'activities': [random.randint(1, 200), random.randint(1, 200)]
        },
        {
            'student_name': "Jane Doe",
            'average_grade': 16.3,
            'grades': [
                {
                    'course_edition_id': random.randint(1, 200),
                    'course_edition_name': "another course",
                    'grade': 15.1,
                    'date': datetime.datetime(2023, 5, 11)
                }
            ],
            'activities': [random.randint(1, 200)]
        }
    ]

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultTop3}
    return flask.jsonify(response)

@app.route('/dbproj/top_by_district', methods=['GET'])
@token_required
@token_required_with_role('staff')
def top_by_district():
    conn = db_connection()
    cur = conn.cursor()

    
    query = """
        SELECT DISTINCT ON (u.district) s.utilizador_userid, u.district, AVG(g.grade) AS avg_grade
        FROM student AS s
        JOIN utilizador AS u ON s.utilizador_userid = u.userid
        JOIN grades AS g ON g.student_utilizador_userid = s.utilizador_userid
        GROUP BY s.utilizador_userid, u.name, u.district
        ORDER BY u.district, AVG(g.grade) DESC
    """
    cur.execute(query)
    rows = cur.fetchall()
    result = [
        {
            'student_id': row[0],
            'district': row[1],
            'average_grade': float(row[2])
        }
        for row in rows
    ]
    conn.close()
    return flask.jsonify({'status': StatusCodes['success'], 'errors': None, 'results': result})



@app.route('/dbproj/report', methods=['GET'])
@token_required
def monthly_report():
    conn = db_connection()
    cur = conn.cursor()


    cur.execute("""
        SELECT m1.month, m1.course_edition_id, m1.course_edition_name, m1.approved, m1.evaluated
        FROM monthly_report AS m1
        JOIN (
            SELECT month, MAX(approved) AS max_approved
            FROM monthly_report
            WHERE month >= EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '12 months')
            GROUP BY month
        ) m2
        ON m1.month = m2.month AND m1.approved = m2.max_approved
        WHERE m1.month >= EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '12 months')
        ORDER BY m1.month DESC;
    """)
    rows = cur.fetchall()

    resultReport = []
    for row in rows:
        resultReport.append({
            'month': row[0],
            'course_edition_id': row[1],
            'course_edition_name': row[2],
            'approved': row[3],
            'evaluated': row[4]
        })
    conn.close()
    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultReport}
    return flask.jsonify(response)


@app.route('/dbproj/delete_details/<student_id>', methods=['DELETE'])
@token_required_with_role('staff')
def delete_student(student_id):
    conn = db_connection()
    cur = conn.cursor()

    try:
        # Verifica se o student_id existe
        cur.execute("SELECT 1 FROM student WHERE utilizador_userid = %s", (student_id,))
        exists = cur.fetchone()
        if not exists:
            response = {'status': StatusCodes['api_error'], 'errors': 'Student not found'}
        else:
            cur.execute("CALL delete_student_data(%s)", (student_id,))
            conn.commit()
            response = {'status': StatusCodes['success'], 'errors': None}
    except Exception as e:
        conn.rollback()
        response = {'status': StatusCodes['internal_error'], 'errors': str(e)}
    finally:
        conn.close()
    return flask.jsonify(response)

if __name__ == '__main__':
    # set up logging
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API stubs online: http://{host}:{port}')