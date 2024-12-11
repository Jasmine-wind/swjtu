import tkinter as tk
import sqlite3
from course_recommender import CourseRecommender
from tkinter import ttk
from tkinter import scrolledtext
from database import DatabaseManager
from gpt_handler import GPTHandler
from voice_handler import VoiceHandler

API_KEY = 'sk-9mbpR0wT83vpuLs1K0Lo8ThfNkqDjoebIKSAH1Oyg5KcN0Ei'

class CourseQueryApp:
    def __init__(self, master):
        self.master = master
        master.title("Course Query System")

        self.db_manager = DatabaseManager()
        self.gpt_handler = GPTHandler(API_KEY)
        self.voice_handler = VoiceHandler()

        self.init_database()
        self.create_ui()

        self.recommender = CourseRecommender()
        self.init_recommender()
        self.add_recommendation_ui()

    def init_database(self):
        self.db_manager.insert_course_data()
        self.db_manager.delete_duplicate_courses()

    def init_recommender(self):
        """初始化推荐系统"""
        # 从数据库获取所有课程数据
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                   SELECT 课程名称, 开始时间, 结束时间, 地点, 星期, 周数列表
                   FROM 课程表
               ''')
            courses = cursor.fetchall()

        # 将课程数据转换为字典列表
        self.all_courses = [
            {
                '课程名称': name,
                '开始时间': start_time,
                '结束时间': end_time,
                '地点': location,
                '星期': weekday,
                '周数列表': week_list
            }
            for name, start_time, end_time, location, weekday, week_list in courses
        ]

        # 训练推荐模型
        self.recommender.train(self.all_courses)

    def add_recommendation_ui(self):
        """添加推荐系统UI"""
        # 添加课程选择下拉框
        tk.Label(self.master, text="选择课程获取推荐:").pack()

        course_names = [course['课程名称'] for course in self.all_courses]
        self.course_var = tk.StringVar()

        course_dropdown = ttk.Combobox(self.master,
                                       textvariable=self.course_var,
                                       values=course_names)
        course_dropdown.pack()

        recommend_button = tk.Button(self.master,
                                     text="获取推荐课程",
                                     command=self.show_recommendations)
        recommend_button.pack()

    def show_recommendations(self):
        """显示推荐课程"""
        selected_course = self.course_var.get()
        if not selected_course:
            self.result_text.insert(tk.END, "请先选择一个课程！\n")
            return

        recommended_courses = self.recommender.recommend_courses(
            selected_course,
            self.all_courses
        )

        self.result_text.insert(tk.END, f"\n推荐课程 (基于 {selected_course}):\n")
        for course in recommended_courses:
            self.result_text.insert(tk.END,
                                    f"- {course['课程名称']}"
                                    f" (时间: {course['开始时间']}-{course['结束时间']},"
                                    f" 地点: {course['地点']})\n"
                                    )
        self.result_text.insert(tk.END, "\n")
    def create_ui(self):
        tk.Label(self.master, text="请输入查询内容 (格式: 周数 星期):").pack()

        self.query_entry = tk.Entry(self.master, width=50)
        self.query_entry.pack()

        query_button = tk.Button(self.master, text="查询", command=self.query_courses)
        query_button.pack()

        gpt_button = tk.Button(self.master, text="gpt查询", command=self.gpt_query)
        gpt_button.pack()

        voice_button = tk.Button(self.master, text="语音查询", command=self.voice_query)
        voice_button.pack()

        clear_button = tk.Button(self.master, text="清除内容", command=self.clear_content)
        clear_button.pack()

        self.result_text = scrolledtext.ScrolledText(self.master, width=60, height=15)
        self.result_text.pack()

    def query_courses(self):
        try:
            week, day = map(int, self.query_entry.get().split())
            result = self.db_manager.query_courses_by_week_and_day(week, day)
            self.result_text.insert(tk.END, result + "\n")
        except ValueError:
            self.result_text.insert(tk.END, "请输入有效的周数和星期，如 '1 1' 表示第1周的星期一。\n")

    def gpt_query(self):
        query_text = self.query_entry.get()
        gpt_result = self.gpt_handler.chat_with_gpt(
            f"请提取并仅返回关键信息，按照 '周数 星期' 的格式返回（例如 '1 1'）。问题:  {query_text}"
        )

        try:
            week, day = map(int, gpt_result.split())
            result = self.db_manager.query_courses_by_week_and_day(week, day)
            self.result_text.insert(tk.END, result + "\n")
        except ValueError:
            self.result_text.insert(tk.END, f"GPT Parsing Error: {gpt_result}\n")

    def voice_query(self):
        query_text = self.voice_handler.recognize_speech()
        if query_text:
            self.result_text.insert(tk.END, f"You said: {query_text}\n")
            gpt_result = self.gpt_handler.chat_with_gpt(
                f"请提取并仅返回关键信息，按照 '周数 星期' 的格式返回（例如 '1 1'）。问题: {query_text}"
            )

            try:
                week, day = map(int, gpt_result.split())
                result = self.db_manager.query_courses_by_week_and_day(week, day)
                self.result_text.insert(tk.END, result + "\n")
            except ValueError:
                self.result_text.insert(tk.END, f"GPT Parsing Error: {gpt_result}\n")

    def clear_content(self):
        self.result_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = CourseQueryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()