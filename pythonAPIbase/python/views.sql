CREATE OR REPLACE VIEW student_grades
AS
SELECT 
    su.name AS student_name,
    g.student_utilizador_userid AS id_stud,
    g.grade,
    g.instructor_utilizador_userid AS id_inst,
	iu.name AS instructor_name,
    v.version_name,
    v.version_id,
    g.evaluation_period_period_id AS ep_id
FROM grades g
JOIN evaluation_period ep ON g.evaluation_period_period_id = ep.period_id
JOIN utilizador su ON g.student_utilizador_userid = su.userid
JOIN utilizador iu ON g.instructor_utilizador_userid = iu.userid
JOIN grades_version gv ON g.evaluation_period_period_id = gv.grades_evaluation_period_period_id
JOIN version v ON gv.version_version_id = v.version_id;


-- View: public.student_full_info

CREATE OR REPLACE VIEW public.student_full_info AS
SELECT
    s.utilizador_userid AS student_id,
    u.name AS student_name,
    ARRAY_AGG(DISTINCT dp.degree_name) AS degrees,
    ARRAY_AGG(DISTINCT c.course_name) AS courses,
    ARRAY_AGG(DISTINCT l.lesson_type) AS lessons,
    ARRAY_AGG(DISTINCT ae.type) AS activities_extra
FROM student s
JOIN utilizador u ON s.utilizador_userid = u.userid
LEFT JOIN enrollment e ON e.student_utilizador_userid = s.utilizador_userid
LEFT JOIN enrollment_degree_program edp ON edp.enrollment_enrollment_id = e.enrollment_id
LEFT JOIN degree_program dp ON edp.degree_program_degree_id = dp.degree_id
LEFT JOIN enrollment_lesson el ON el.enrollment_enrollment_id = e.enrollment_id
LEFT JOIN lesson l ON el.lesson_lesson_id = l.lesson_id
LEFT JOIN version v ON l.version_version_id = v.version_id
LEFT JOIN course c ON v.course_course_id = c.course_id
LEFT JOIN activities_extra_student aes ON aes.student_utilizador_userid = s.utilizador_userid
LEFT JOIN activities_extra ae ON aes.activities_extra_type = ae.type
GROUP BY s.utilizador_userid, u.name;



-- View: public.course_full_info

-- DROP VIEW public.course_full_info;

CREATE OR REPLACE VIEW public.course_full_info
 AS
 SELECT c.course_id,
    c.course_name,
    dp.degree_id,
    dp.degree_name,
    v.version_id,
    v.version_name,
    v.version_year,
    i.utilizador_userid AS instructor_id,
    iu.name AS instructor_name,
    l.lesson_id,
    l.lesson_type,
    l.frequency
   FROM course c
     LEFT JOIN degree_program_course dpc ON dpc.course_course_id = c.course_id
     LEFT JOIN degree_program dp ON dpc.degree_program_degree_id = dp.degree_id
     LEFT JOIN version v ON v.course_course_id = c.course_id
     LEFT JOIN instructor i ON v.instructor_utilizador_userid = i.utilizador_userid
     LEFT JOIN utilizador iu ON i.utilizador_userid = iu.userid
     LEFT JOIN lesson l ON l.version_version_id = v.version_id;

ALTER TABLE public.course_full_info
    OWNER TO postgres;

