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
        roles = ['admin', 'Instructor_grades', 'student']
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
        conn.commit()

        statement2 = 'INSERT INTO student (balance, utilizador_userid) VALUES (%s,%s)'
        values2 = (balance, resultUserId)

        cur.execute(statement2, values2)
        conn.commit()
        response = {'status': StatusCodes['success'], 'errors': None, 'results': resultUserId}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/student - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        conn.rollback()

    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(response)

@app.route('/dbproj/register/staff', methods=['POST'])  ###Comentario:Precisamos criar!!!
@token_required
@token_required_with_role('admin')
def register_staff():
    data = flask.request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Username, email, and password are required', 'results': None})
    
    resultUserId = random.randint(1, 200) # TODO

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultUserId}
    return flask.jsonify(response)

@app.route('/dbproj/register/instructor', methods=['POST']) ###Comentario:associar instrutor a um curso
@token_required
@token_required_with_role('admin')
def register_instructor():
    conn = db_connection()
    cur = conn.cursor()

    data = flask.request.get_json()

    type = data.get('type')
    email = data.get('mail')
    password = data.get('password')
    name= data.get('name')
    age = data.get('age')
    phone_number= data.get('phone_number')
    username = data.get('username')

    if type not in ['staff', 'coordinator']:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Invalid instructor type. Must be "staff" or "coordinator".', 'results': None})

    if not type or not email or not password or not name or not age or not phone_number or not username:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Balance, mail, password, name, age, phone number and username are required', 'results': None})

    statement1 = 'INSERT INTO utilizador (mail, password, name,age,phone_number,username) VALUES (%s, %s, %s, %s, %s,%s) returning userid'
    values1 = (email, password,name,age,phone_number, username)

    try:
        cur.execute(statement1, values1)
        
        resultUserId = cur.fetchone()[0]
        # commit the transaction
        conn.commit()

        statement2 = 'INSERT INTO instructor (type, utilizador_userid) VALUES (%s,%s)'
        values2 = (type, resultUserId)

        cur.execute(statement2, values2)
        conn.commit()
        response = {'status': StatusCodes['success'], 'errors': None, 'results': resultUserId}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/instructor - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(response)

@app.route('/dbproj/enroll_degree/<degree_id>', methods=['POST'])
@token_required_with_role('staff')  # Apenas staff pode usar
def enroll_degree(degree_id):
    data = flask.request.get_json()
    conn = db_connection()
    cur = conn.cursor()

    student_id = data.get('student_id')
    date = data.get('date')

    if not student_id or not date:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Student ID and date are required', 'results': None})

    try:
        # Inserir na tabela enrollment
        cur.execute("""
            INSERT INTO enrollment (status, type, data, version_version_id, student_utilizador_userid)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING enrollment_id
        """, (True, 'regular', date, 1, student_id))  
        enrollment_id = cur.fetchone()[0]

        # Inserir na tabela enrollment_degree
        cur.execute("""
            INSERT INTO enrollment_degree (enrollment_enrollment_id, degree_program_degree_id)
            VALUES (%s, %s)
        """, (enrollment_id, degree_id))

        conn.commit()
        
        response = {'status': StatusCodes['success'], 'errors': None, 'results': {'enrollment_id': enrollment_id}}
        return flask.jsonify(response)
    
    except Exception as e:
        conn.rollback()
        return flask.jsonify({'status': StatusCodes['internal_error'], 'errors': str(e), 'results': None})
    finally:
        cur.close()
        conn.close()


@app.route('/dbproj/enroll_activity/<activity_id>', methods=['POST'])
@token_required_with_role('student')   #so aluno pode usar
###Comentario:verificar a qtd de alunos antes de matricular
def enroll_activity(activity_id):
    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)

@app.route('/dbproj/enroll_course_edition/<course_edition_id>', methods=['POST'])
@token_required
def enroll_course_edition(course_edition_id):
    data = flask.request.get_json()
    classes = data.get('classes', [])

    if not classes:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'At least one class ID is required', 'results': None})
    
    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)

@app.route('/dbproj/submit_grades/<course_edition_id>', methods=['POST'])
@token_required ###Comentario: precisamos de autenticacao do instrutor e se ele esta relacionado àquele curso!!
def submit_grades(course_edition_id):
    data = flask.request.get_json()
    period = data.get('period')
    grades = data.get('grades', [])

    if not period or not grades:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Evaluation period and grades are required', 'results': None})
    
    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)

@app.route('/dbproj/student_details/<student_id>', methods=['GET'])
@token_required ###Comentario: so staff e o aluno autenticado podem ver, resultados mais recentes em cima
def student_details(student_id):

    resultStudentDetails = [ # TODO
        {
            'course_edition_id': random.randint(1, 200),
            'course_name': "some course",
            'course_edition_year': 2024,
            'grade': 12
        },
        {
            'course_edition_id': random.randint(1, 200),
            'course_name': "another course",
            'course_edition_year': 2025,
            'grade': 17
        }
    ]

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultStudentDetails}
    return flask.jsonify(response)

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
            'average_grade': 15.1, ###Comentario: funcao AVG dentro do SQL para as notas
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
def top_by_district():

    resultTopByDistrict = [ # TODO
        {
            'student_id': random.randint(1, 200),
            'district': "Coimbra",
            'average_grade': 15.2  ###Comentario: funcao AVG dentro do SQL para as notas
        },
        {
            'student_id': random.randint(1, 200),
            'district': "Coimbra",
            'average_grade': 13.6
        }
    ]

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultTopByDistrict}
    return flask.jsonify(response)

@app.route('/dbproj/report', methods=['GET'])
@token_required
def monthly_report():

    resultReport = [ # TODO
        {
            'month': "month_0",
            'course_edition_id': random.randint(1, 200),
            'course_edition_name': "Some course",
            'approved': 20,    ###Comentario: colocar trigger ao submeter notas para criar tabela de aprovados ou não
            'evaluated': 23
        },
        {
            'month': "month_1",
            'course_edition_id': random.randint(1, 200),
            'course_edition_name': "Another course",
            'approved': 200,
            'evaluated': 123
        }
    ]

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultReport}
    return flask.jsonify(response)

@app.route('/dbproj/delete_details/<student_id>', methods=['DELETE'])
@token_required_with_role('staff')  # Apenas staff pode usar
def delete_student(student_id):
    data = flask.request.get_json()
    conn = db_connection()
    cur = conn.cursor()

    student_id = data.get('student_id')

    if not student_id:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Student ID and is required', 'results': None})
    
    #try:
    #    cur.execute("DELETE FROM enrollment WHERE student_utilizador_userid = %s", (student_id,))

    ###Comentario: precisa fazer um grande efeito cascata, poir o aluno vai estar em muitas atividades, cursos, salas de aula etc 
    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)

if __name__ == '__main__':
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API stubs online: http://{host}:{port}') 