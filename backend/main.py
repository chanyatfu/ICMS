import logging
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import datetime
import mysql.connector
from pydantic import BaseModel
import check_face
import uuid

load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cnx = mysql.connector.connect(
    user='root',
    password='t8gESx06a5e',
    host='127.0.0.1',
    port=3306,
    database='comp3278'
)

app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def test_fastapi_connection():
    return {"status": "ok"}


@app.get("/db")
def test_db_connection():
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM Class;")
    # using list comprehension
    # rows = [{
    #     'course_id': row[0],
    #     'class_id': row[1],
    #     'class_time': row[2],
    #     'class_location': row[3],
    # } for row in cursor]

    # using zip and cursor.column_names
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "ok", "rows": rows}


@app.get("/student/get/{id}")
def get_student_by_id(id):
    cursor = cnx.cursor()
    cursor.execute(f"SELECT * FROM Student WHERE student_id = {id};")
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "ok", "rows": rows}



@app.get("/timetable/get/{id}")
def get_timetable_by_id(id):
    cursor = cnx.cursor()
    cursor.execute(f"SELECT Class.class_time, Course.course_id, Course.course_name, Classroom.classroom_address FROM Class,Course,Classroom,Student,Enrollment WHERE Student.student_id = '{id}' AND Student.student_id = Enrollment.student_id AND Enrollment.course_id = Course.course_id AND Enrollment.course_id = Class.course_id AND Enrollment.class_id = Class.class_id AND Class.classroom_id = Classroom.classroom_id ORDER BY Class.class_time ASC;")
    '''
    SELECT Class.class_time, Course.course_id, Course.course_name, Classroom.classroom_address
    FROM Class,Course,Classroom,Student,Enrollment
    WHERE Student.student_id = '{id}'
    AND Student.student_id = Enrollment.student_id
    AND Enrollment.course_id = Course.course_id
    AND Enrollment.course_id = Class.course_id
    AND Enrollment.class_id = Class.class_id
    AND Class.classroom_id = Classroom.classroom_id
    ORDER BY Class.class_time ASC;
    '''

    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"Timetable": rows}


@app.get("/teacher-message/get/{course_id}")
def get_teacher_message_by_course_id(course_id):

    cursor = cnx.cursor()
    cursor.execute(f"SELECT TeacherMessage.message_id, TeacherMessage.message, TeacherMessage.message_time FROM TeacherMessage WHERE TeacherMessage.course_id = '{course_id}' ORDER BY message_time DESC;")

    '''
    SELECT TeacherMessage.message_id, TeacherMessage.message, TeacherMessage.message_time
    FROM  TeacherMessage
    WHERE TeacherMessage.course_id = '{course_id}'
    ORDER BY message_time DESC;
    '''
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"Teacher_Messages": rows}



@app.get("/course/get/{student_id}")
def get_courses_enrolled_by_student_id(student_id):
    cursor = cnx.cursor()
    cursor.execute(f"""
        SELECT Course.course_id, Course.course_name
        FROM Student
            LEFT JOIN Enrollment ON (Student.student_id = Enrollment.student_id)
            LEFT JOIN Course ON (Enrollment.course_id = Course.course_id)
        WHERE Student.student_id = {student_id};
    """)
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "okay", "rows": rows}


@app.get("/material/get/{course_id}")
def get_materials_by_course_id(course_id):
    cursor = cnx.cursor()
    command = f"""
        SELECT material_id, title, url, description
        FROM Material
        Where course_id = '{course_id}';
    """
    cursor.execute(command)

    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "okay", "rows": rows}

@app.get("/upcoming-class/get/{id}")
def upcoming_class_get(id: str):
    cursor = cnx.cursor()
    cmd = f"""
        SELECT
            Class.class_time class_time,
            Course.course_id course_id,
            Course.course_name course_name,
            Classroom.classroom_address classroom_address,
            Course.course_id course_id,
            Class.teacher_message teacher_message,
            Class.zoom_link zoom_link
        FROM Student
            LEFT JOIN Enrollment ON (Student.student_id = Enrollment.student_id)
            LEFT JOIN Course ON (Enrollment.course_id = Course.course_id)
            LEFT JOIN Class ON (Enrollment.course_id = Class.course_id)
            LEFT JOIN Classroom ON (Class.classroom_id = Classroom.classroom_id)
        WHERE Student.student_id = '{id}'
            AND Class.class_time BETWEEN NOW() AND NOW() + INTERVAL 1 HOUR
        ORDER BY Class.class_time ASC
        LIMIT 1;
    """
    cursor.execute(cmd)
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "okay", "rows": rows}

@app.get("/login-history/{id}")
def get_login_history(id: str):
    cursor = cnx.cursor()
    cursor.execute(f"SELECT * FROM LoginHistory where student_id = {id};")
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "ok", "rows": rows}

@app.put("/update-login-session/")
def update_login_session(session_id: str):
    cursor = cnx.cursor()
    command = f"""
        UPDATE `LoginHistory`
        SET login_duration = NOW() - login_time
        WHERE session_id = '{session_id}';
    """
    cursor.execute(command)
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "ok", "rows": rows}


@app.post("/add-login-session/")
def add_login_session(session_id: str, student_id: str):
    cursor = cnx.cursor()
    command = f"""
        INSERT INTO `LoginHistory` VALUES ('{student_id}', '{session_id}', 'NOW()', '0');
    """
    cursor.execute(command)
    rows = [dict(zip(cursor.column_names, row)) for row in cursor]
    cursor.close()
    return {"status": "ok", "rows": rows}

@app.post("/face-recognition/post")
def face_to_id():
    result = check_face.check_face()
    if not result:
        return {"student_id": "none"}
    else:
        return {"student_id": result}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
