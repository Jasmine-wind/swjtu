import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path='school_db.sqlite'):
        self.db_path = os.path.abspath(db_path)

    def delete_duplicate_courses(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                DELETE FROM 课程表
                WHERE 课程ID NOT IN (
                    SELECT MIN(课程ID)
                    FROM 课程表
                    GROUP BY 课程名称, 开始时间, 结束时间, 地点, 星期, 周数列表
                )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        except Exception as e:
            print(f"Other Error: {e}")

    def insert_course_data(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM 课程表')

                courses = [
                    ('人工智能', '09:50', '11:25', '2号教学楼318', 'W', '1-17', 1),
                    ('英语', '08:00', '09:35', '1号教学楼524', 'G', '2,5,7,9', 3),
                    ('数电', '09:50', '11:25', '1号教学楼413', 'K', '1,3,5,7,9,11,13,15,17', 4),
                    ('概率', '09:50', '12:15', '2号教学楼216', 'M', '1-17', 5),
                    ('数据结构', '08:00', '09:35', '2号教学楼316', 'L', '1,3,5,7,9,11,13,15,17', 1),
                    ('形策', '15:50', '17:25', '1号教学楼314', 'W', '1-17', 4),
                    ('大物', '15:50', '18:15', '2号教学楼316', 'Z', '2,4,6,8,10,12,14,16', 2)
                ]

                cursor.executemany('''
                INSERT INTO 课程表 (课程名称, 开始时间, 结束时间, 地点, 教师ID, 周数列表, 星期)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', courses)
                conn.commit()
        except sqlite3.Error as e:
            print(f"SQLite Error: {e}")
        except Exception as e:
            print(f"Other Error: {e}")

    def query_courses_by_week_and_day(self, week, day):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT 课程名称, 开始时间, 结束时间, 地点, 教师ID, 周数列表
                FROM 课程表
                WHERE 星期 = ?
                ORDER BY 开始时间
                ''', (day,))

                courses = cursor.fetchall()
                filtered_courses = []

                for course in courses:
                    name, start_time, end_time, location, teacher_id, week_list = course

                    if week_list == '1-17':
                        filtered_courses.append(course)
                    else:
                        week_list = [week.strip() for week in week_list.split(',')]
                        if str(week) in week_list:
                            filtered_courses.append(course)

                result_text = ""
                if filtered_courses:
                    for course in filtered_courses:
                        name, start_time, end_time, location, teacher_id = course[:5]
                        result_text += f"课程: {name}, 时间: {start_time} - {end_time}, 地点: {location}, 老师ID: {teacher_id}\n"
                else:
                    result_text = f"第 {week} 周，星期 {day} 没有课程。\n"

                return result_text
        except sqlite3.Error as e:
            return f"SQLite Error: {e}\n"
        except Exception as e:
            return f"Other Error: {e}\n"