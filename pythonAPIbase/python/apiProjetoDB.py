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
from flask import request, jsonify, g

load_dotenv()

app = flask.Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_KEY')

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500,
    'unauthorized': 401
}

# set up logging
logging.basicConfig(filename='log_file.log')
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
ch.setFormatter(formatter)
logger.addHandler(ch)

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
            g.username = payload_data.get('username')
            g.role = payload_data.get('role') 
            # Busque o user_id no banco:
            conn = db_connection()
            cur = conn.cursor()
            cur.execute("SELECT userid FROM utilizador WHERE username = %s", (g.username,))
            user = cur.fetchone()
            if user:
                g.user_id = user[0]
            else:
                g.user_id = None
            conn.close()
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

            if not auth_header or not auth_header.startswith('Bearer '):
                return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Token is missing or malformed', 'results': None})

            token = auth_header.split(" ")[1]

            try:
                payload_data = jwt.decode(token, os.getenv('JWT_KEY'), algorithms=["HS256"]) #faz decode
                logger.debug(f'JWT payload: {payload_data}')
                g.username = payload_data.get('username')
                # Busque o user_id no banco:
                conn = db_connection()
                cur = conn.cursor()
                cur.execute("SELECT userid FROM utilizador WHERE username = %s", (g.username,))
                user = cur.fetchone()
                if user:
                    g.user_id = user[0]
                else:
                    g.user_id = None
                conn.close()

                
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

    email = data.get('mail')
    password = data.get('password')
    name= data.get('name')
    username = data.get('username')
    district = data.get('district')
    balance = data.get('balance')

    if not balance or not email or not password or not name or not username or not district:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Balance, mail, password, name, username and district are required', 'results': None})

    statement1 = 'INSERT INTO utilizador (mail, password, name, username) VALUES (%s, %s, %s, %s) returning userid'
    values1 = (email, password,name, username)

    try:
        cur.execute(statement1, values1)
        
        resultUserId = cur.fetchone()[0]
        # commit the transaction
        conn.commit()

        statement2 = 'INSERT INTO student (balance, district, utilizador_userid) VALUES (%s,%s, %s)'
        values2 = (balance, district, resultUserId)

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

@app.route('/dbproj/register/staff', methods=['POST']) 
@token_required
@token_required_with_role('admin')
def register_staff():
    conn = db_connection()
    cur = conn.cursor()

    data = flask.request.get_json()

    email = data.get('mail')
    password = data.get('password')
    name = data.get('name')
    username = data.get('username')


    if not email or not password or not name or not username:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'mail, password, name, and username are required', 'results': None})

    statement1 = 'INSERT INTO utilizador (mail, password, name, username) VALUES (%s, %s, %s, %s) returning userid'
    values1 = (email, password, name, username)

    try:
        cur.execute(statement1, values1)
        resultUserId = cur.fetchone()[0]
        conn.commit()

        statement2 = 'INSERT INTO admin ( utilizador_userid) VALUES ( %s)'
        values2 = (resultUserId,)

        cur.execute(statement2, values2)
        conn.commit()

        response = {'status': StatusCodes['success'], 'errors': None, 'results': resultUserId}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/staff - error: {error}')
        conn.rollback()
        response = {'status': StatusCodes['internal_error'], 'errors': str(error), 'results': None}

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

    email = data.get('mail')
    password = data.get('password')
    name = data.get('name')
    username = data.get('username')

    if not email or not password or not name or not username:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'mail, password, name, and username are required', 'results': None})

    statement1 = 'INSERT INTO utilizador (mail, password, name, username) VALUES (%s, %s, %s, %s) returning userid'
    values1 = (email, password, name, username)

    try:
        cur.execute(statement1, values1)
        resultUserId = cur.fetchone()[0]
        conn.commit()

        statement2 = 'INSERT INTO instructor ( utilizador_userid) VALUES ( %s)'
        values2 = (resultUserId,)

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
@token_required_with_role('admin')
def enroll_student_in_degree(degree_id):
    conn = db_connection()
    cur = conn.cursor()

    data = flask.request.get_json()
    student_id = data.get('student_id')
    enroll_date = data.get('date')  

    if not student_id or not enroll_date:
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': 'student_id and date are required',
            'results': None
        })

   
    try:
        # Inserir na tabela enrollment
        insert_enrollment = """
            INSERT INTO enrollment (status, type, data, student_utilizador_userid)
            VALUES (%s, %s, %s, %s)
            RETURNING enrollment_id
        """

        values_enrollment = (True, 'degree', enroll_date, student_id)
        cur.execute(insert_enrollment, values_enrollment)
        enrollment_id = cur.fetchone()[0]

        # Associar à tabela enrollment_degree
        insert_enrollment_degree = """
            INSERT INTO enrollment_degree_program (enrollment_enrollment_id, degree_program_degree_id)
            VALUES (%s, %s)
        """
        values_assoc = (enrollment_id, degree_id)
        cur.execute(insert_enrollment_degree, values_assoc)

        conn.commit()
        response = {
            'status': StatusCodes['success'],
            'errors': None,
            'results': enrollment_id
        }

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

@app.route('/dbproj/enroll_activity/<activity_name>', methods=['POST'])
@token_required
@token_required_with_role('student')
def enroll_activity(activity_name):
    conn = db_connection()
    cur = conn.cursor()

    # ID do estudante vem do token JWT
    student_id = flask.g.user_id

    try:
        # Verifica se a atividade existe
        cur.execute('SELECT type FROM activities_extra WHERE type = %s', (activity_name,))
        if cur.fetchone() is None:
            return flask.jsonify({
                'status': StatusCodes['not_found'],
                'errors': f'Activity "{activity_name}" not found',
                'results': None
            })

        # Verifica se o estudante já está inscrito na atividade
        cur.execute('''
            SELECT 1 FROM activities_extra_student 
            WHERE activities_extra_type = %s AND student_utilizador_userid = %s
            FOR UPDATE
        ''', (activity_name, student_id))
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
        ''', (activity_name, student_id))

        conn.commit()
        response = {
            'status': StatusCodes['success'],
            'errors': None,
            'results': f'Student {student_id} enrolled in activity "{activity_name}"'
        }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/enroll_activity/{activity_name} - error: {error}')
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

    student_id = flask.g.user_id  # ID do estudante autenticado
    data = flask.request.get_json()
    lesson_ids = data.get('classes')

    if not course_edition_id or not student_id:
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': 'Course edition ID and student ID are required.',
            'results': None
        })

    if not lesson_ids or not isinstance(lesson_ids, list):
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': '"classes" field must be a non-empty list.',
            'results': None
        })

    try:
        #admin_id = 1  

        # Inserir matrícula
        cur.execute(
            '''
            INSERT INTO enrollment (status, type, data, student_utilizador_userid)
            VALUES (%s, %s, CURRENT_DATE, %s)
            RETURNING enrollment_id
            ''',
            (True, 'course', student_id)
        )
        row = cur.fetchone()
        if not row:
            raise Exception("Failed to retrieve enrollment_id after insert.")
        enrollment_id = row[0]

        # Associar à edição do curso
        cur.execute(
            '''
            INSERT INTO enrollment_version (enrollment_enrollment_id, version_version_id)
            VALUES (%s, %s)
            ''',
            (enrollment_id, course_edition_id)
        )

        # Associar às aulas indicadas
        for lesson_id in lesson_ids:
            cur.execute(
                '''
                SELECT version_version_id FROM lesson
                WHERE lesson_id = %s AND version_version_id = %s
                FOR UPDATE
                ''',
                (lesson_id, course_edition_id)
            )
            result = cur.fetchone()
            if not result:
                raise Exception(f'Lesson {lesson_id} does not belong to course edition {course_edition_id}')

            cur.execute(
                '''
                INSERT INTO enrollment_lesson (enrollment_enrollment_id, lesson_lesson_id)
                VALUES (%s, %s)
                ''',
                (enrollment_id, lesson_id)
            )

        conn.commit()
        response = {
            'status': StatusCodes['success'],
            'errors': None
        }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/enroll_course_edition - error: {error}')
        conn.rollback()
        response = {
            'status': StatusCodes['internal_error'],
            'errors': str(error)
        }

    finally:
        if conn:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/submit_grades/<course_edition_id>', methods=['POST'])
@token_required
@token_required_with_role('instructor')
def submit_grades(course_edition_id):
    conn = db_connection()
    cur = conn.cursor()

    data = flask.request.get_json()
    period = data.get('period')
    grades_list = data.get('grades')  # [[student_id, grade], ...]

    if not period or not grades_list:
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': '"period" and "grades" fields are required'
        })

    try:
        # Obtemos o ID do instrutor autenticado diretamente de flask.g
        instructor_userid = flask.g.user_id  
        
        # Verifica se o usuário atual é o instrutor da versão
        cur.execute(
            'SELECT instructor_utilizador_userid FROM version WHERE version_id = %s FOR UPDATE',
            (course_edition_id,)
        )
        result = cur.fetchone()

        if not result:
            return flask.jsonify({
                'status': StatusCodes['not_found'],
                'errors': 'Course edition (version) not found'
            })

        expected_instructor_id = result[0]

        if expected_instructor_id != instructor_userid:
            return flask.jsonify({
                'status': StatusCodes['unauthorized'],
                'errors': 'Only the responsible instructor can submit grades for this course edition'
            })

       
        # Inserir notas e associar à versão
        for entry in grades_list:
            student_id = entry[0]
            grade = entry[1]

            if not student_id or grade is None:
                continue  # Pula entradas incompletas

        # Inserir nota
        cur.execute(
            '''
            INSERT INTO grades (status, grade, evaluation_period_period_id, instructor_utilizador_userid, student_utilizador_userid)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (evaluation_period_period_id, student_utilizador_userid)
            DO UPDATE SET grade = EXCLUDED.grade, instructor_utilizador_userid = EXCLUDED.instructor_utilizador_userid, status = EXCLUDED.status
            ''',
            (True, grade, period, instructor_userid, student_id)
        )

            # Associar à edição do curso
        cur.execute(
            '''INSERT INTO grades_version (grades_evaluation_period_period_id, version_version_id)
           VALUES (%s, %s)
           ON CONFLICT DO NOTHING''',
            (period, course_edition_id)
        )

        cur.execute("""
            UPDATE evaluation_period
            SET
                num_approved = (
                    SELECT COUNT(*) FROM grades
                    WHERE evaluation_period_period_id = %s AND status = TRUE AND grade >= 10
                ),
                average = (
                    SELECT AVG(grade)::FLOAT FROM grades
                    WHERE evaluation_period_period_id = %s AND status = TRUE
                )
            WHERE period_id = %s
        """, (period, period, period))

        conn.commit()
        response = {'status': StatusCodes['success'], 'errors': None}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/submit_grades - error: {error}')
        conn.rollback()
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/student_details/<student_id>', methods=['GET'])
@token_required
def student_details(student_id):
    conn = db_connection()
    cur = conn.cursor()
    try:
        # Permite apenas staff (admin) ou o próprio aluno acessar
        user_role = getattr(g, 'role', None)
        user_id = getattr(g, 'user_id', None)
        if user_role != 'admin' and str(user_id) != str(student_id):
            return flask.jsonify({
                'status': StatusCodes['unauthorized'],
                'errors': 'You can only view your own course details',
                'results': None
            })

        # Busca os detalhes dos cursos em que o estudante está matriculado
        query = """
            SELECT
                v.version_id AS course_edition_id,
                c.course_name,
                v.version_year,
                g.grade
            FROM enrollment e
            JOIN enrollment_version ev ON e.enrollment_id = ev.enrollment_enrollment_id
            JOIN version v ON ev.version_version_id = v.version_id
            JOIN course c ON v.course_course_id = c.course_id
            LEFT JOIN grades g ON g.student_utilizador_userid = e.student_utilizador_userid
            WHERE e.student_utilizador_userid = %s
            ORDER BY v.version_year DESC, v.version_id DESC
        """
        cur.execute(query, (student_id,))
        rows = cur.fetchall()

        results = [
            {
                "course_edition_id": row[0],
                "course_name": row[1],
                "course_edition_year": row[2],
                "grade": row[3]
            }
            for row in rows
        ]

        response = {
            'status': StatusCodes['success'],
            'errors': None,
            'results': results
        }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/student_details/{student_id} - error: {error}')
        response = {
            'status': StatusCodes['internal_error'],
            'errors': str(error),
            'results': None
        }
    finally:
        if conn:
            conn.close()

    return flask.jsonify(response)


@app.route('/dbproj/degree_details/<degree_id>', methods=['GET'])
@token_required_with_role('admin')
def degree_details(degree_id):
    conn = db_connection()
    cur = conn.cursor()
    try:
        query = """
            SELECT
                c.course_id,
                c.course_name,
                v.version_id AS course_edition_id,
                v.version_year AS course_edition_year,
                v.capacity,
                v.coordinator AS coordinator_id,
                ARRAY_REMOVE(ARRAY[v.coordinator, v.assistant], NULL) AS instructors,
                COUNT(DISTINCT e.enrollment_id) AS enrolled_count,
                COUNT(DISTINCT CASE WHEN g.status = TRUE THEN e.enrollment_id END) AS approved_count
            FROM degree_program_course dpc
            JOIN course c ON dpc.course_course_id = c.course_id
            JOIN version v ON v.course_course_id = c.course_id
            LEFT JOIN enrollment_version ev ON ev.version_version_id = v.version_id
            LEFT JOIN enrollment e ON e.enrollment_id = ev.enrollment_enrollment_id
            LEFT JOIN grades g ON g.student_utilizador_userid = e.student_utilizador_userid
            WHERE dpc.degree_program_degree_id = %s
            GROUP BY c.course_id, c.course_name, v.version_id, v.version_year, v.capacity, v.coordinator, v.assistant
            ORDER BY v.version_year DESC, v.version_id DESC
        """
        cur.execute(query, (degree_id,))
        rows = cur.fetchall()

        results = []
        for row in rows:
            results.append({
                "course_id": row[0],
                "course_name": row[1],
                "course_edition_id": row[2],
                "course_edition_year": row[3],
                "capacity": row[4],
                "coordinator_id": row[5],
                "instructors": [i for i in row[6] if i is not None],
                "enrolled_count": row[7],
                "approved_count": row[8]
            })

        response = {
            'status': StatusCodes['success'],
            'errors': None,
            'results': results
        }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/degree_details/{degree_id} - error: {error}')
        response = {
            'status': StatusCodes['internal_error'],
            'errors': str(error),
            'results': None
        }
    finally:
        if conn:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/top3', methods=['GET'])
@token_required
@token_required_with_role('admin')
def top3_students():
    conn = None
    try:
        conn = db_connection()
        cur = conn.cursor()

        query = """
            WITH student_grades AS (
                SELECT 
                    s.utilizador_userid AS student_id,
                    u.name AS student_name,
                    AVG(g.grade) AS average_grade,
                    COUNT(g.grade) AS grade_count
                FROM student s
                JOIN utilizador u ON s.utilizador_userid = u.userid
                JOIN grades g ON g.student_utilizador_userid = s.utilizador_userid
                JOIN enrollment e ON e.student_utilizador_userid = s.utilizador_userid
                JOIN enrollment_version ev ON e.enrollment_id = ev.enrollment_enrollment_id
                JOIN version v ON ev.version_version_id = v.version_id
                WHERE g.status = TRUE
                AND v.version_year = EXTRACT(YEAR FROM CURRENT_DATE)
                GROUP BY s.utilizador_userid, u.name
            )
            SELECT 
                sg.student_name,
                sg.average_grade,
                sg.grade_count,
                ARRAY(
                    SELECT json_build_object(
                        'course_edition_id', v.version_id,
                        'course_edition_name', v.version_name,
                        'grade', g.grade,
                        'date', ep.final_date
                    )
                    FROM enrollment e
                    JOIN grades g ON g.student_utilizador_userid = sg.student_id
                    JOIN evaluation_period ep ON g.evaluation_period_period_id = ep.period_id
                    JOIN enrollment_version ev ON e.enrollment_id = ev.enrollment_enrollment_id
                    JOIN version v ON ev.version_version_id = v.version_id
                    WHERE e.student_utilizador_userid = sg.student_id
                    AND g.status = TRUE
                    ORDER BY ep.final_date DESC
                    LIMIT 3
                ) AS grades,
                ARRAY(
                    SELECT a.type
                    FROM activities_extra_student aes
                    JOIN activities_extra a ON aes.activities_extra_type = a.type
                    WHERE aes.student_utilizador_userid = sg.student_id
                ) AS activities
            FROM student_grades sg
            ORDER BY sg.average_grade DESC
            LIMIT 3;
        """
        
        cur.execute(query)
        rows = cur.fetchall()

        result = []
        aviso = None
        for row in rows:
            if row[2] < 3:
                aviso = "Alguns estudantes possuem menos de 3 notas. Mais dados seriam necessários para um ranking mais preciso."
            result.append({
                'student_name': row[0],
                'average_grade': float(row[1]),
                'grades': row[3],      # lista de objetos json
                'activities': row[4],  # lista de atividades
                'grade_count': row[2]
            })

        response = {
            'status': StatusCodes['success'],
            'errors': aviso,
            'results': result
        }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/top3 - error: {error}')
        response = {
            'status': StatusCodes['internal_error'],
            'errors': str(error),
            'results': None
        }
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/top_by_district', methods=['GET'])
@token_required
@token_required_with_role('admin')
def top_by_district():
    conn = db_connection()
    cur = conn.cursor()

    
    query = """
        SELECT DISTINCT ON (s.district) s.utilizador_userid, s.district, AVG(g.grade) AS avg_grade
        FROM student AS s
        JOIN utilizador AS u ON s.utilizador_userid = u.userid
        JOIN grades AS g ON g.student_utilizador_userid = s.utilizador_userid
        GROUP BY s.utilizador_userid, u.name, s.district
        ORDER BY s.district, AVG(g.grade) DESC
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
@token_required_with_role('admin')
def monthly_report():
    conn = db_connection()
    cur = conn.cursor()

    conn = db_connection()
    cur = conn.cursor()

   
    cur.execute("""
    SELECT 
        TO_CHAR(ep.start_date, 'YYYY-MM') AS month,
        v.version_id AS course_edition_id,
        v.version_name AS course_edition_name,
        ep.num_approved AS approved,
        COUNT(g.grade) AS evaluated
    FROM grades g
    JOIN evaluation_period ep ON g.evaluation_period_period_id = ep.period_id
    JOIN grades_version gv ON g.evaluation_period_period_id = gv.grades_evaluation_period_period_id
    JOIN version v ON gv.version_version_id = v.version_id
    WHERE ep.start_date >= (CURRENT_DATE - INTERVAL '12 months')
    GROUP BY month, v.version_id, v.version_name, ep.num_approved
    """)

    rows = cur.fetchall()

    conn.close()

    result = []
    for row in rows:
        result.append({
            'month': row[0],
            'course_edition_id': row[1],
            'course_edition_name': row[2],
            'approved': row[3],
            'evaluated': row[4]
        })

    return jsonify({'status': StatusCodes['success'], 'errors': None, 'results': result})

@app.route('/dbproj/delete_details/<student_id>', methods=['DELETE'])
@token_required_with_role('admin')
def delete_student(student_id):
    conn = db_connection()
    cur = conn.cursor()

    try:
        # Verifica se o student_id existe
        cur.execute("SELECT 1 FROM student WHERE utilizador_userid = %s FOR UPDATE", (student_id,))
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

@app.route('/dbproj/withdraw_activity/<activity_name>', methods=['DELETE'])
@token_required
@token_required_with_role('student')
def withdraw_activity(activity_name):
    conn = db_connection()
    cur = conn.cursor()
    student_id = flask.g.user_id

    try:
        # Verifica se o estudante está inscrito na atividade
        cur.execute(
            '''
            SELECT 1 FROM activities_extra_student
            WHERE activities_extra_type = %s AND student_utilizador_userid = %s
            ''',
            (activity_name, student_id)
        )
        if not cur.fetchone():
            return flask.jsonify({
                'status': StatusCodes['api_error'],
                'errors': 'Student is not enrolled in this activity',
                'results': None
            })

        # Remove a inscrição (aciona o trigger de reembolso)
        cur.execute(
            '''
            DELETE FROM activities_extra_student
            WHERE activities_extra_type = %s AND student_utilizador_userid = %s
            ''',
            (activity_name, student_id)
        )
        conn.commit()
        response = {
            'status': StatusCodes['success'],
            'errors': None,
            'results': f'Student {student_id} withdrawn from activity "{activity_name}"'
        }
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'DELETE /dbproj/withdraw_activity/{activity_name} - error: {error}')
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

def create_default_staff():
    conn = db_connection()
    cur = conn.cursor()
    try:
        # Verifica se já existe
        cur.execute("SELECT userid FROM utilizador WHERE username = %s", ('init_adm',))
        user = cur.fetchone()
        if not user:
            # Cria utilizador
            cur.execute("""
                INSERT INTO utilizador (mail, password, name, username)
                VALUES (%s, %s, %s, %s)
                RETURNING userid
            """, ('init.admf@uni.pt', 'admin123', 'Initial Admin','init_adm'))
            userid = cur.fetchone()[0]
            cur.execute("INSERT INTO admin (utilizador_userid) VALUES (%s)", (userid,))
            conn.commit()
            logger.info("Utilizador admin default criado.")
        else:
            logger.info("Utilizador admin default já existe.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao criar utilizador admin default: {e}")
    finally:
        conn.close()

# Chame a função antes de iniciar o app
create_default_staff()

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API stubs online: http://{host}:{port}')