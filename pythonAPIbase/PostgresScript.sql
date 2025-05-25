CREATE TABLE utilizador (
	userid	 BIGSERIAL,
	mail	 VARCHAR(512) NOT NULL,
	password VARCHAR(512) NOT NULL,
	name	 VARCHAR(512) NOT NULL,
	username VARCHAR(512) NOT NULL,
	PRIMARY KEY(userid)
);

CREATE TABLE admin (
	utilizador_userid BIGINT,
	PRIMARY KEY(utilizador_userid)
);

CREATE TABLE student (
	balance		 FLOAT(8) NOT NULL,
	district		 VARCHAR(512) NOT NULL,
	utilizador_userid BIGINT,
	PRIMARY KEY(utilizador_userid)
);

CREATE TABLE instructor (
	utilizador_userid BIGINT,
	PRIMARY KEY(utilizador_userid)
);

CREATE TABLE course (
	course_id	 BIGSERIAL,
	course_name VARCHAR(40) NOT NULL,
	PRIMARY KEY(course_id)
);

CREATE TABLE version (
	version_id			 BIGSERIAL,
	version_name		 VARCHAR(30) NOT NULL,
	coordinator			 VARCHAR(512) NOT NULL,
	assistant			 VARCHAR(512),
	capacity			 BIGINT NOT NULL,
	semester			 VARCHAR(512) NOT NULL,
	version_year		 BIGINT NOT NULL,
	instructor_utilizador_userid BIGINT NOT NULL,
	course_course_id		 BIGINT NOT NULL,
	PRIMARY KEY(version_id)
);

CREATE TABLE lesson (
	lesson_id			 BIGSERIAL,
	lesson_type			 VARCHAR(512) NOT NULL,
	frequency			 INTEGER NOT NULL,
	instructor_utilizador_userid BIGINT NOT NULL,
	version_version_id		 BIGINT NOT NULL,
	classroom_id_classrom	 BIGINT NOT NULL,
	PRIMARY KEY(lesson_id)
);

CREATE TABLE classroom (
	id_classrom BIGSERIAL,
	building	 VARCHAR(512) NOT NULL,
	floor	 BIGINT NOT NULL,
	capacity	 BIGINT NOT NULL,
	PRIMARY KEY(id_classrom)
);

CREATE TABLE degree_program (
	degree_id	 BIGSERIAL,
	degree_name VARCHAR(45) NOT NULL,
	PRIMARY KEY(degree_id)
);

CREATE TABLE grades (
	status			 BOOL NOT NULL,
	grade			 BIGINT NOT NULL,
	evaluation_period_period_id	 BIGINT,
	student_utilizador_userid	 BIGINT,
	instructor_utilizador_userid BIGINT NOT NULL,
	PRIMARY KEY(evaluation_period_period_id, student_utilizador_userid)
);

CREATE TABLE evaluation_period (
	period_id	 BIGSERIAL,
	start_date	 DATE NOT NULL,
	final_date	 DATE NOT NULL,
	num_approved BIGINT,
	average	 FLOAT(8),
	PRIMARY KEY(period_id)
);

CREATE TABLE activities_extra (
	type VARCHAR(512),
	PRIMARY KEY(type)
);

CREATE TABLE transactions (
	transaction_id		 BIGSERIAL,
	amount			 FLOAT(8) NOT NULL,
	transactions_type	 VARCHAR(512),
	transaction_data		 DATE NOT NULL,
	student_utilizador_userid BIGINT NOT NULL,
	PRIMARY KEY(transaction_id)
);

CREATE TABLE enrollment (
	enrollment_id		 BIGSERIAL,
	status			 BOOL NOT NULL,
	type			 VARCHAR(512) NOT NULL,
	data			 DATE NOT NULL,
	student_utilizador_userid BIGINT NOT NULL,
	PRIMARY KEY(enrollment_id)
);

CREATE TABLE enrollment_lesson (
	enrollment_enrollment_id BIGINT,
	lesson_lesson_id	 BIGINT,
	PRIMARY KEY(enrollment_enrollment_id,lesson_lesson_id)
);

CREATE TABLE grades_version (
	grades_evaluation_period_period_id BIGINT,
	version_version_id		 BIGINT NOT NULL,
	PRIMARY KEY(grades_evaluation_period_period_id)
);

CREATE TABLE student_lesson (
	student_utilizador_userid BIGINT,
	lesson_lesson_id		 BIGINT,
	PRIMARY KEY(student_utilizador_userid,lesson_lesson_id)
);

CREATE TABLE enrollment_version (
	enrollment_enrollment_id BIGINT,
	version_version_id	 BIGINT,
	PRIMARY KEY(enrollment_enrollment_id,version_version_id)
);

CREATE TABLE enrollment_degree_program (
	enrollment_enrollment_id BIGINT,
	degree_program_degree_id BIGINT,
	PRIMARY KEY(enrollment_enrollment_id,degree_program_degree_id)
);

CREATE TABLE admin_enrollment (
	admin_utilizador_userid	 BIGINT,
	enrollment_enrollment_id BIGINT,
	PRIMARY KEY(admin_utilizador_userid,enrollment_enrollment_id)
);

CREATE TABLE activities_extra_student (
	activities_extra_type	 VARCHAR(512),
	student_utilizador_userid BIGINT,
	PRIMARY KEY(activities_extra_type,student_utilizador_userid)
);

CREATE TABLE course_course (
	course_course_id	 BIGINT,
	course_course_id1 BIGINT,
	PRIMARY KEY(course_course_id,course_course_id1)
);

CREATE TABLE degree_program_course (
	degree_program_degree_id BIGINT,
	course_course_id	 BIGINT,
	PRIMARY KEY(degree_program_degree_id,course_course_id)
);

CREATE TABLE transactions_activities_extra (
	transactions_transaction_id BIGINT,
	activities_extra_type	 VARCHAR(512) NOT NULL,
	PRIMARY KEY(transactions_transaction_id)
);

ALTER TABLE utilizador ADD UNIQUE (mail, username);
ALTER TABLE admin ADD CONSTRAINT admin_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE student ADD CONSTRAINT student_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE instructor ADD CONSTRAINT instructor_fk1 FOREIGN KEY (utilizador_userid) REFERENCES utilizador(userid);
ALTER TABLE course ADD UNIQUE (course_name);
ALTER TABLE version ADD UNIQUE (version_name);
ALTER TABLE version ADD CONSTRAINT version_fk1 FOREIGN KEY (instructor_utilizador_userid) REFERENCES instructor(utilizador_userid);
ALTER TABLE version ADD CONSTRAINT version_fk2 FOREIGN KEY (course_course_id) REFERENCES course(course_id);
ALTER TABLE lesson ADD CONSTRAINT lesson_fk1 FOREIGN KEY (instructor_utilizador_userid) REFERENCES instructor(utilizador_userid);
ALTER TABLE lesson ADD CONSTRAINT lesson_fk2 FOREIGN KEY (version_version_id) REFERENCES version(version_id);
ALTER TABLE lesson ADD CONSTRAINT lesson_fk3 FOREIGN KEY (classroom_id_classrom) REFERENCES classroom(id_classrom);
ALTER TABLE degree_program ADD UNIQUE (degree_name);
ALTER TABLE grades ADD CONSTRAINT grades_fk1 FOREIGN KEY (evaluation_period_period_id) REFERENCES evaluation_period(period_id);
ALTER TABLE grades ADD CONSTRAINT grades_fk2 FOREIGN KEY (student_utilizador_userid) REFERENCES student(utilizador_userid);
ALTER TABLE grades ADD CONSTRAINT grades_fk3 FOREIGN KEY (instructor_utilizador_userid) REFERENCES instructor(utilizador_userid);
ALTER TABLE transactions ADD CONSTRAINT transactions_fk1 FOREIGN KEY (student_utilizador_userid) REFERENCES student(utilizador_userid);
ALTER TABLE transactions ADD CONSTRAINT transactions_fk2 FOREIGN KEY (activities_extra_type) REFERENCES activities_extra(type);
ALTER TABLE enrollment ADD CONSTRAINT enrollment_fk1 FOREIGN KEY (student_utilizador_userid) REFERENCES student(utilizador_userid);
ALTER TABLE enrollment_lesson ADD CONSTRAINT enrollment_lesson_fk1 FOREIGN KEY (enrollment_enrollment_id) REFERENCES enrollment(enrollment_id);
ALTER TABLE enrollment_lesson ADD CONSTRAINT enrollment_lesson_fk2 FOREIGN KEY (lesson_lesson_id) REFERENCES lesson(lesson_id);
ALTER TABLE grades_version ADD CONSTRAINT grades_version_fk1 FOREIGN KEY (grades_evaluation_period_period_id) REFERENCES grades(evaluation_period_period_id);
ALTER TABLE grades_version ADD CONSTRAINT grades_version_fk2 FOREIGN KEY (version_version_id) REFERENCES version(version_id);
ALTER TABLE student_lesson ADD CONSTRAINT student_lesson_fk1 FOREIGN KEY (student_utilizador_userid) REFERENCES student(utilizador_userid);
ALTER TABLE student_lesson ADD CONSTRAINT student_lesson_fk2 FOREIGN KEY (lesson_lesson_id) REFERENCES lesson(lesson_id);
ALTER TABLE enrollment_version ADD CONSTRAINT enrollment_version_fk1 FOREIGN KEY (enrollment_enrollment_id) REFERENCES enrollment(enrollment_id);
ALTER TABLE enrollment_version ADD CONSTRAINT enrollment_version_fk2 FOREIGN KEY (version_version_id) REFERENCES version(version_id);
ALTER TABLE enrollment_degree_program ADD CONSTRAINT enrollment_degree_program_fk1 FOREIGN KEY (enrollment_enrollment_id) REFERENCES enrollment(enrollment_id);
ALTER TABLE enrollment_degree_program ADD CONSTRAINT enrollment_degree_program_fk2 FOREIGN KEY (degree_program_degree_id) REFERENCES degree_program(degree_id);
ALTER TABLE admin_enrollment ADD CONSTRAINT admin_enrollment_fk1 FOREIGN KEY (admin_utilizador_userid) REFERENCES admin(utilizador_userid);
ALTER TABLE admin_enrollment ADD CONSTRAINT admin_enrollment_fk2 FOREIGN KEY (enrollment_enrollment_id) REFERENCES enrollment(enrollment_id);
ALTER TABLE activities_extra_student ADD CONSTRAINT activities_extra_student_fk1 FOREIGN KEY (activities_extra_type) REFERENCES activities_extra(type);
ALTER TABLE activities_extra_student ADD CONSTRAINT activities_extra_student_fk2 FOREIGN KEY (student_utilizador_userid) REFERENCES student(utilizador_userid);
ALTER TABLE course_course ADD CONSTRAINT course_course_fk1 FOREIGN KEY (course_course_id) REFERENCES course(course_id);
ALTER TABLE course_course ADD CONSTRAINT course_course_fk2 FOREIGN KEY (course_course_id1) REFERENCES course(course_id);
ALTER TABLE degree_program_course ADD CONSTRAINT degree_program_course_fk1 FOREIGN KEY (degree_program_degree_id) REFERENCES degree_program(degree_id);
ALTER TABLE degree_program_course ADD CONSTRAINT degree_program_course_fk2 FOREIGN KEY (course_course_id) REFERENCES course(course_id);
ALTER TABLE transactions_activities_extra ADD CONSTRAINT transactions_activities_extra_fk1 FOREIGN KEY (transactions_transaction_id) REFERENCES transactions(transaction_id);
ALTER TABLE transactions_activities_extra ADD CONSTRAINT transactions_activities_extra_fk2 FOREIGN KEY (activities_extra_type) REFERENCES activities_extra(type);


--outras alteraçoes
ALTER TABLE grades DROP CONSTRAINT grades_pkey CASCADE;
ALTER TABLE grades ADD PRIMARY KEY (evaluation_period_period_id, student_utilizador_userid);


ALTER TABLE grades
DROP CONSTRAINT grades_fk2,
ADD CONSTRAINT grades_fk2 FOREIGN KEY (student_utilizador_userid) REFERENCES student(utilizador_userid) ON DELETE CASCADE;

ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_fk2;
ALTER TABLE transactions DROP COLUMN IF EXISTS activities_extra_type;

--Procedimento de deletar estudante e seus dados associados
CREATE OR REPLACE PROCEDURE delete_student_data(stud_id BIGINT) 
LANGUAGE plpgsql AS $$
BEGIN
    -- Apagar registros associados ao aluno
    DELETE FROM activities_extra_student WHERE student_utilizador_userid = stud_id;
    DELETE FROM transactions WHERE student_utilizador_userid = stud_id;
    DELETE FROM student_lesson WHERE student_utilizador_userid = stud_id;

    -- Apagar dados relacionados a enrollment
    DELETE FROM enrollment_lesson WHERE enrollment_enrollment_id IN (
        SELECT enrollment_id FROM enrollment WHERE student_utilizador_userid = stud_id
    );

    DELETE FROM enrollment_version WHERE enrollment_enrollment_id IN (
        SELECT enrollment_id FROM enrollment WHERE student_utilizador_userid = stud_id
    );

    DELETE FROM enrollment_degree_program WHERE enrollment_enrollment_id IN (
        SELECT enrollment_id FROM enrollment WHERE student_utilizador_userid = stud_id
    );

    DELETE FROM admin_enrollment WHERE enrollment_enrollment_id IN (
        SELECT enrollment_id FROM enrollment WHERE student_utilizador_userid = stud_id
    );

    DELETE FROM enrollment WHERE student_utilizador_userid = stud_id;

    -- Outros dados do aluno
    DELETE FROM grades WHERE instructor_utilizador_userid = stud_id;
    DELETE FROM student WHERE utilizador_userid = stud_id;
    DELETE FROM utilizador WHERE userid = stud_id;
END;
$$;

--- Triggers
CREATE OR REPLACE FUNCTION public.charge_student_on_enrollment()
RETURNS trigger
LANGUAGE plpgsql
AS $BODY$
DECLARE
    current_balance NUMERIC;
    enrollment_fee NUMERIC := 100.0;  -- valor da matrícula
BEGIN
    -- Só cobra se for matrícula em degree
    IF NEW.type IS DISTINCT FROM 'degree' THEN
        RETURN NEW;
    END IF;

    SELECT balance
    INTO current_balance
    FROM student
    WHERE utilizador_userid = NEW.student_utilizador_userid;

    IF current_balance < enrollment_fee THEN
        RAISE EXCEPTION 'Saldo insuficiente para matrícula. Saldo atual: %, necessário: %', current_balance, enrollment_fee;
    END IF;

    UPDATE student
    SET balance = balance - enrollment_fee
    WHERE utilizador_userid = NEW.student_utilizador_userid;

    INSERT INTO transactions (
        amount,
        transactions_type,
        transaction_data,
        student_utilizador_userid
    )
    VALUES (
        -enrollment_fee,
        'enrollment',
        CURRENT_DATE,
        NEW.student_utilizador_userid
    );

    RETURN NEW;
END;
$BODY$;



CREATE OR REPLACE FUNCTION public.check_classrom_capacity_before_enrollment()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
DECLARE
    classrom_capacity INT;
    current_enrollments INT;
    classrom_id INT;
BEGIN
    -- Pega a sala associada à versão (curso) em que o aluno vai se matricular
    SELECT cl.id_classrom, cl.capacity
    INTO classrom_id, classrom_capacity
    FROM version v
    JOIN lesson l ON l.version_version_id = v.version_id
    JOIN classrom cl ON cl.id_classrom = l.classrom_id_classrom
    WHERE v.version_id = (
        SELECT v2.version_id
        FROM enrollment e
        JOIN version v2 ON v2.version_id = (
            SELECT l.version_version_id
            FROM lesson l
            LIMIT 1  -- Supondo 1 aula por curso
        )
        WHERE e.enrollment_id = NEW.enrollment_id
    )
    LIMIT 1;

    -- Conta quantos alunos estão matriculados nesse curso
    SELECT COUNT(*)
    INTO current_enrollments
    FROM enrollment e
    JOIN version v ON v.version_id = (
        SELECT l.version_version_id
        FROM lesson l
        WHERE l.classrom_id_classrom = classrom_id
        LIMIT 1
    )
    WHERE e.type = 'degree';  -- exemplo: só conta matrículas normais

    -- Verifica a capacidade
    IF current_enrollments >= classrom_capacity THEN
        RAISE EXCEPTION 'Sala cheia (%/%). Matrícula não permitida.', current_enrollments, classrom_capacity;
    END IF;

    RETURN NEW;
END;
$BODY$;

ALTER FUNCTION public.check_classrom_capacity_before_enrollment()
    OWNER TO postgres;

-- Função para cobrar ao inscrever
CREATE OR REPLACE FUNCTION charge_on_activity_signup()
RETURNS TRIGGER AS $$
DECLARE
    activity_fee NUMERIC := 50.0;
    current_balance NUMERIC;
BEGIN
    SELECT balance INTO current_balance
    FROM student
    WHERE utilizador_userid = NEW.student_utilizador_userid;

    IF current_balance < activity_fee THEN
        RAISE EXCEPTION 'Saldo insuficiente para inscrição na atividade extra.';
    END IF;

    UPDATE student
    SET balance = balance - activity_fee
    WHERE utilizador_userid = NEW.student_utilizador_userid;

    INSERT INTO transactions (
        amount,
        transactions_type,
        transaction_data,
        student_utilizador_userid
    ) VALUES (
        -activity_fee,
        'activity_signup',
        CURRENT_DATE,
        NEW.student_utilizador_userid
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Função para devolver ao sair
CREATE OR REPLACE FUNCTION refund_on_activity_withdraw()
RETURNS TRIGGER AS $$
DECLARE
    activity_fee NUMERIC := 50.0;
BEGIN
    UPDATE student
    SET balance = balance + activity_fee
    WHERE utilizador_userid = OLD.student_utilizador_userid;

    INSERT INTO transactions (
        amount,
        transactions_type,
        transaction_data,
        student_utilizador_userid
    ) VALUES (
        activity_fee,
        'activity_refund',
        CURRENT_DATE,
        OLD.student_utilizador_userid
    );

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger para cobrar ao inscrever
CREATE TRIGGER trg_charge_on_activity_signup
BEFORE INSERT ON activities_extra_student
FOR EACH ROW
EXECUTE FUNCTION charge_on_activity_signup();

-- Trigger para devolver ao sair
CREATE TRIGGER trg_refund_on_activity_withdraw
BEFORE DELETE ON activities_extra_student
FOR EACH ROW
EXECUTE FUNCTION refund_on_activity_withdraw();

CREATE OR REPLACE FUNCTION update_evaluation_period_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE evaluation_period ep
    SET
        num_approved = (
            SELECT COUNT(*) FROM grades g
            WHERE g.evaluation_period_period_id = ep.period_id AND g.status = TRUE AND g.grade >= 10
        ),
        average = (
            SELECT AVG(g.grade)::FLOAT FROM grades g
            WHERE g.evaluation_period_period_id = ep.period_id AND g.status = TRUE
        )
    WHERE ep.period_id = NEW.evaluation_period_period_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_eval_stats ON grades;
CREATE TRIGGER trg_update_eval_stats
AFTER INSERT OR UPDATE OR DELETE ON grades
FOR EACH ROW
EXECUTE FUNCTION update_evaluation_period_stats();



-------------------- Exemplos pra povoar a base de dados ------------------------------------

INSERT INTO activities_extra (type)
VALUES ('esporte'),
('projeto de pesquisa'),
('hackathon'),
('estagio de verao');

INSERT INTO degree_program(degree_id, degree_name)
VALUES (1, 'engenharia informatica'), 
(2, 'engenharia e ciência de dados'), 
(3, 'engenharia de redes');


INSERT INTO course(course_id, course_name)
VALUES (19, 'programação orientada a objetos'),
(20, 'base de dados'),
(21, 'redes de comunicação'),
(22, 'redes de computadores'),
(23, 'sistemas operativos'),
(24, 'programação web'),
(25, 'programação de jogos'),
(26, 'programação de sistemas embarcados'),
(27, 'programação de sistemas operacionais');


INSERT INTO course_course(course_course_id, course_course_id1) --relaciona prerequisitos de cursos
VALUES(20, 19);
--ex: POO é prerequisito de BD


INSERT INTO version(version_name, coordinator, capacity, semester, instructor_utilizador_userid, course_course_id, version_year)
VALUES('BD2023/2024', 'joao', 20, '2024/1', 6, 20, 2023),
('POO2023/2024', 'joao', 45, '2024/1', 6, 19, 2024),
('RC2024/2025', 'joao',  30, '2054/1', 6, 21, 2025),
('RC2023/2024', 'marta', 30, '2024/1', 12, 22, 2023),  -- redes de computadores
('SO2023/2024', 'marta', 25, '2024/1', 12, 23, 2023),  -- sistemas operativos
('PW2024/2025', 'marta', 40, '2025/1', 12, 24, 2024),   -- programação web
('PJ2024/2025', 'caio', 35, '2025/1', 11, 25, 2024),   -- programação de jogos
('PSE2024/2025', 'caio', 20, '2025/1', 11, 26, 2024), -- sistemas embarcados
('PSO2024/2025', 'caio', 20, '2025/1', 11, 27, 2024); -- sistemas operacionais


INSERT INTO classroom(id_classrom, building, floor, capacity)
VALUES(1, 'edificio 1', 1, 20),
(2, 'edificio 2', 2, 30),
(3, 'edificio 3', 3, 40);


INSERT INTO lesson(lesson_type, frequency, version_version_id, instructor_utilizador_userid, classroom_id_classrom)
VALUES('teorica', 2, 1, 1, 1),
('pratica', 2, 1, 1, 3),
('teorica', 2, 29, 6, 1),
('pratica', 1, 29, 6, 2),
('teorica', 2, 28, 6, 1),
('pratica', 1, 28, 6, 3),
('teorica', 2, 30, 6, 2),
('pratica', 1, 30, 6, 3),
('pratica', 1, 31, 5, 1),
('laboratorio', 1, 31, 5, 2),
('teorica', 2, 32, 5, 2),
('pratica', 1, 32, 5, 3),
('teorica', 2, 33, 5, 1),
('pratica', 1, 33, 5, 2),
('teorica', 2, 34, 7, 1),
('laboratorio', 1, 34, 7, 3),
('teorica', 2, 35, 7, 2),
('pratica', 1, 35, 7, 1);



INSERT INTO evaluation_period(start_date, final_date, num_approved, average)
VALUES ('2025-03-01', '2025-06-30', 9, 12),
('2025-03-01', '2025-06-30', 8, 10);

INSERT INTO degree_program_course (degree_program_degree_id, course_course_id)
VALUES
    (1, 19),  -- engenharia informatica e POO
    (1, 20),  -- engenharia informatica e BD
    (1, 21),  -- engenharia informatica e RC
	(3, 22),  -- engenharia de redes e RC
	(3, 23),  -- engenharia de redes e SO
	(2, 24),  -- engenharia e ciencia de dados e PW
	(2, 25),  -- engenharia e ciencia de dados e pj
	(3, 26),  -- engenharia de redes e PSE
	(3, 27);  -- engenharia de redes e PSO