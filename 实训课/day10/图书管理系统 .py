import pymysql
import time
from datetime import datetime, timedelta

class BookManage:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                user="root",
                password="root123456",
                database="book_db",
                port=3307,
                charset="utf8mb4",
                autocommit=False
            )
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            self.current_user = None
            self._init_tables()
            print("数据库连接成功")
        except Exception as e:
            print("数据库连接失败：", e)
            raise

    def _init_tables(self):
        """创建借阅记录表（如果不存在）"""
        sql = """
        create table if not exists borrow(
            id int auto_increment primary key,
            username varchar(50) not null comment '借阅人用户名',
            book_id int not null comment '图书编号',
            borrow_date date not null comment '借阅日期',
            due_date date not null comment '应还日期（借阅日+7天）',
            return_date date default null comment '实际归还日期',
            foreign key (book_id) references book(book_id) on delete cascade
        )
        """
        self.cursor.execute(sql)
        self.conn.commit()

    def write_log(self, msg):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] {msg}\n")

    # 管理员登录
    def login(self):
        count = 6
        for i in range(1, count + 1):
            print(f"\n========== 管理员登录 ==========")
            username = input("用户名: ")
            password = input("密码: ")
            sql = "select * from admin where username=%s and password=%s"
            self.cursor.execute(sql, (username, password))
            user = self.cursor.fetchone()
            if user:
                print(f"登录成功！欢迎管理员 {username}")
                self.current_user = f"管理员_{username}"
                self.raw_username = username
                self.write_log(f"操作人：{self.current_user} | 操作：登录系统")
                return True
            else:
                print("用户名或密码错误")
                self.write_log(f"操作人：管理员_{username} | 操作：登录失败")
                if i < count:
                    print(f"还剩 {count - i} 次尝试机会，按 'q' 退出，其他键继续")
                    choice = input().strip().lower()
                    if choice == 'q':
                        print("用户主动取消登录。")
                        return False
                else:
                    print("已达到最大尝试次数 (6次)，程序退出。")
        return False

    # 学生登录
    def student_login(self):
        count = 6
        for i in range(1, count + 1):
            print(f"\n========== 学生登录 ==========")
            username = input("学号/用户名: ")
            password = input("密码: ")
            sql = "select * from student where username=%s and password=%s"
            self.cursor.execute(sql, (username, password))
            user = self.cursor.fetchone()
            if user:
                print(f"登录成功！欢迎学生 {username}")
                self.current_user = f"学生_{username}"
                self.raw_username = username
                self.write_log(f"操作人：{self.current_user} | 操作：登录系统")
                return True
            else:
                print("用户名或密码错误")
                self.write_log(f"操作人：学生_{username} | 操作：登录失败")
                if i < count:
                    print(f"还剩 {count - i} 次尝试机会，按 'q' 退出，其他键继续")
                    choice = input().strip().lower()
                    if choice == 'q':
                        print("用户主动取消登录。")
                        return False
                else:
                    print("已达到最大尝试次数 (6次)，程序退出。")
        return False

    def add_book(self, book_id, name, author, classification):
        sql_check = "select book_id from book where book_id = %s"
        self.cursor.execute(sql_check, (book_id,))
        if self.cursor.fetchone():
            print(f"添加失败：图书编号 {book_id} 已存在，请使用不同的编号。")
            return False
        if not name or not author or not classification:
            print("添加失败：书名、作者、分类不能为空。")
            return False
        try:
            sql = "insert into book(book_id, name, author, classification, state) values (%s, %s, %s, %s, %s)"
            self.cursor.execute(sql, (book_id, name, author, classification, '未借阅'))
            self.conn.commit()
            print("添加图书成功")
            operator = self.current_user if self.current_user else "未登录"
            self.write_log(f"操作人：{operator} | 操作：添加图书 | 图书编号：{book_id} | 书名：{name}")
            return True
        except Exception as e:
            print(f"添加失败：{e}")
            return False

    def show_book(self):
        sql = "select * from book"
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        if not res:
            print("暂无图书数据！")
            return
        print("\n========== 图书列表 ==========")
        for book in res:
            print(f"图书编号:{book['book_id']}| 书名:《{book['name']}》| 作者:{book['author']}| 分类:{book['classification']}| 状态:{book['state']}")
        operator = self.current_user if self.current_user else "未登录"
        self.write_log(f"操作人：{operator} | 操作：查看所有图书 | 结果数量：{len(res)}")

    def search_book(self):
        print("\n请选择查询方式：")
        print("1. 按图书编号（精确）")
        print("2. 按书名（模糊查询）")
        print("3. 按作者（模糊查询）")
        print("4. 按图书分类")
        choice = input("请输入序号: ")

        sql = "select * from book where "
        param = None

        if choice == "1":
            bid = input("请输入图书编号: ")
            if not bid.isdigit():
                print("编号必须是数字")
                return None
            sql += "book_id = %s"
            param = (int(bid),)
        elif choice == "2":
            name = input("请输入书名关键字: ")
            sql += "name like %s"
            param = (f"%{name}%",)
        elif choice == "3":
            author = input("请输入作者关键字: ")
            sql += "author like %s"
            param = (f"%{author}%",)
        elif choice == "4":
            classification = input("请输入分类名称: ")
            sql += "classification = %s"
            param = (classification,)
        else:
            print("无效选择")
            return None

        self.cursor.execute(sql, param)
        results = self.cursor.fetchall()

        if not results:
            print("未找到符合条件的图书")
            operator = self.current_user if self.current_user else "未登录"
            self.write_log(f"操作人：{operator} | 操作：多条件查询图书 | 条件类型：{choice} | 结果：未找到")
            return None

        print(f"\n共找到 {len(results)} 本图书：")
        for book in results:
            print(f"编号:{book['book_id']} | 书名:《{book['name']}》 | 作者:{book['author']} | 分类:{book['classification']} | 状态:{book['state']}")

        operator = self.current_user if self.current_user else "未登录"
        self.write_log(f"操作人：{operator} | 操作：多条件查询图书 | 条件类型：{choice} | 结果数量：{len(results)}")
        return results

    def search_by_id(self, book_id):
        sql = "select * from book where book_id = %s"
        self.cursor.execute(sql, (book_id,))
        return self.cursor.fetchone()

    def update_book(self, name, author, classification, book_id):
        try:
            sql = "update book set name=%s, author=%s, classification=%s where book_id=%s"
            self.cursor.execute(sql, (name, author, classification, book_id))
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print("图书基础信息修改成功")
                operator = self.current_user if self.current_user else "未登录"
                self.write_log(f"操作人：{operator} | 操作：修改图书信息 | 图书编号：{book_id} | 新书名：{name} | 新作者：{author} | 新分类：{classification}")
            else:
                print("未找到该图书")
        except Exception as e:
            self.conn.rollback()
            print(f"修改失败：{e}")

    def delete_book(self, book_id):
        print("确定要删除吗：(y/n)")
        a = input('请输入(y/n)')
        if a == 'y':
            try:
                sql = "delete from book where book_id=%s"
                self.cursor.execute(sql, (book_id,))
                self.conn.commit()
                if self.cursor.rowcount > 0:
                    print("已删除")
                    operator = self.current_user if self.current_user else "未登录"
                    self.write_log(f"操作人：{operator} | 操作：删除图书 | 图书编号：{book_id}")
                else:
                    print("未找到该图书")
            except Exception as e:
                self.conn.rollback()
                print(f"删除失败：{e}")
        else:
            print('未删除，已退出')

    def check_book_status(self, book_id):
        sql = "select name, state from book where book_id = %s"
        self.cursor.execute(sql, (book_id,))
        book = self.cursor.fetchone()
        if book:
            print(f"《{book['name']}》当前状态：{book['state']}")
            return book['state']
        else:
            print("图书不存在")
            return None

    def borrow_book(self, book_id):
        book_state = self.check_book_status(book_id)
        if book_state is None:
            return False
        if book_state != '可借阅':
            print("借阅失败：图书已借出")
            return False

        # 检查当前用户未归还的借阅数量
        sql1 = "select count(*) as cnt from borrow where username=%s and return_date is null"
        self.cursor.execute(sql1, (self.raw_username,))
        cnt = self.cursor.fetchone()['cnt']
        if cnt >= 3:
            print("借阅失败：您已达到最大借阅数量（3本），请先归还部分图书")
            return False

        # 检查是否已经借阅同一本且未归还
        sql2 = "select id from borrow where username=%s and book_id=%s and return_date is null"
        self.cursor.execute(sql2, (self.raw_username, book_id))
        if self.cursor.fetchone():
            print("借阅失败：您已经借了这本书，还没归还")
            return False

        try:
            self.conn.begin()
            # 更新图书状态
            sql_update = "update book set state = '已借出' where book_id = %s and state = '可借阅'"
            self.cursor.execute(sql_update, (book_id,))
            # 插入借阅记录
            today = datetime.now().date()
            due = today + timedelta(days=7)
            sql_insert = "insert into borrow (username, book_id, borrow_date, due_date) values (%s, %s, %s, %s)"
            self.cursor.execute(sql_insert, (self.raw_username, book_id, today, due))
            self.conn.commit()
            print(f"借阅成功！应还日期：{due}")
            operator = self.current_user if self.current_user else "未登录"
            self.write_log(f"操作人：{operator} | 操作：借阅图书 | 图书编号：{book_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"借阅过程中发生错误：{e}")
            return False

    def return_book(self, book_id):
        sql_check = "select id from borrow where username=%s and book_id=%s and return_date is null"
        self.cursor.execute(sql_check, (self.raw_username, book_id))
        record = self.cursor.fetchone()
        if not record:
            print("归还失败：您没有借阅这本书或已归还")
            return False

        try:
            self.conn.begin()
            today = datetime.now().date()
            sql_update_record = "update borrow set return_date = %s where id = %s"
            self.cursor.execute(sql_update_record, (today, record['id']))
            sql_update_book = "update book set state = '可借阅' where book_id = %s"
            self.cursor.execute(sql_update_book, (book_id,))
            self.conn.commit()
            print("归还成功！")
            operator = self.current_user if self.current_user else "未登录"
            self.write_log(f"操作人：{operator} | 操作：归还图书 | 图书编号：{book_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"归还过程中发生错误：{e}")
            return False

    def show_borrowed_books(self):
        sql = """
        select b.book_id, b.name, br.borrow_date, br.due_date 
        from borrow br 
        join book b on br.book_id = b.book_id 
        where br.username = %s and br.return_date is null
        """
        self.cursor.execute(sql, (self.raw_username,))
        records = self.cursor.fetchall()
        if not records:
            print("当前没有借阅任何图书")
            return
        print("\n========== 借阅列表 ==========")
        for rec in records:
            print(f"图书编号:{rec['book_id']} | 书名:《{rec['name']}》 | 借阅日期:{rec['borrow_date']} | 应还日期:{rec['due_date']}")
        print("===================================")
        operator = self.current_user if self.current_user else "未登录"
        self.write_log(f"操作人：{operator} | 操作：查看借阅记录 | 结果数量：{len(records)}")

    def register_admin(self, new_username, new_password):
        sql_check = "select * from admin where username=%s"
        self.cursor.execute(sql_check, (new_username,))
        if self.cursor.fetchone():
            print("注册失败：用户名已存在！")
            return False
        try:
            sql_insert = "insert into admin (username, password) values (%s, %s)"
            self.cursor.execute(sql_insert, (new_username, new_password))
            self.conn.commit()
            print("注册成功！新管理员账号已添加。")
            operator = self.current_user if self.current_user else "未登录"
            self.write_log(f"操作人：{operator} | 操作：注册新管理员 | 新用户名：{new_username}")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"注册失败：{e}")
            return False

    def register_student(self, new_username, new_password):
        sql_check = "select * from student where username=%s"
        self.cursor.execute(sql_check, (new_username,))
        if self.cursor.fetchone():
            print("注册失败：学生账号已存在！")
            return False
        try:
            sql_insert = "insert into student (username, password) values (%s, %s)"
            self.cursor.execute(sql_insert, (new_username, new_password))
            self.conn.commit()
            print("注册成功！新学生账号已添加。")
            operator = self.current_user if self.current_user else "未登录"
            self.write_log(f"操作人：{operator} | 操作：注册新学生 | 新用户名：{new_username}")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"注册失败：{e}")
            return False

    def close(self):
        self.cursor.close()
        self.conn.close()
        print("数据库连接已关闭")


def get_int_input(prompt):
    while True:
        try:
            value = int(input(prompt).strip())
            return value
        except ValueError:
            print("输入无效，请输入数字！")

def get_nonempty_input(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("输入不能为空，请重新输入！")

def main():
    manager = BookManage()

    print("\n========== 图书管理系统 ==========")
    print("1. 管理员端")
    print("2. 学生端")
    role = input("请选择您的身份（1/2）：").strip()

    if role == "1":
        if not manager.login():
            print("登录失败，程序退出。")
            manager.close()
            return

        while True:
            print("\n========== 图书管理系统（管理员） ==========")
            print("1. 查看所有图书")
            print("2. 查询图书")
            print("3. 添加图书")
            print("4. 修改图书信息")
            print("5. 删除图书")
            print("6. 借阅图书")
            print("7. 归还图书")
            print("8. 查看图书状态")
            print("9. 注册新管理员账号")
            print("10. 添加学生账号")
            print("11. 查看借阅记录")
            print("0. 退出系统")
            print("============================================")

            choice = input("请输入操作编号：")
            if choice == "1":
                manager.show_book()
            elif choice == "2":
                manager.search_book()
            elif choice == "3":
                bid = get_int_input("图书编号: ")
                name = get_nonempty_input("书名: ")
                author = get_nonempty_input("作者: ")
                classification = get_nonempty_input("分类: ")
                manager.add_book(bid, name, author, classification)
            elif choice == "4":
                bid = get_int_input("请输入要修改的图书编号: ")
                current = manager.search_by_id(bid)
                if not current:
                    print("未找到该图书")
                    continue
                name = input("新书名: ").strip()
                author = input("新作者: ").strip()
                classification = input("新分类: ").strip()
                if name or author or classification:
                    new_name = name if name else current['name']
                    new_author = author if author else current['author']
                    new_classification = classification if classification else current['classification']
                    manager.update_book(new_name, new_author, new_classification, bid)
                else:
                    print("未做任何修改")
            elif choice == "5":
                bid = get_int_input("请输入要删除的图书编号: ")
                manager.delete_book(bid)
            elif choice == "6":
                bid = get_int_input("请输入要借阅的图书编号: ")
                manager.borrow_book(bid)
            elif choice == "7":
                bid = get_int_input("请输入要归还的图书编号: ")
                manager.return_book(bid)
            elif choice == "8":
                bid = get_int_input("请输入图书编号: ")
                manager.check_book_status(bid)
            elif choice == "9":
                new_user = get_nonempty_input("请输入新管理员用户名: ")
                new_pwd = get_nonempty_input("请输入密码: ")
                manager.register_admin(new_user, new_pwd)
            elif choice == "10":
                new_user = get_nonempty_input("请输入新学生学号/用户名: ")
                new_pwd = get_nonempty_input("请输入密码: ")
                manager.register_student(new_user, new_pwd)
            elif choice == "11":
                manager.show_borrowed_books()
            elif choice == "0":
                manager.close()
                print("系统退出成功！")
                break
            else:
                print("无效输入，请输入0-11的数字！")

    elif role == "2":
        if not manager.student_login():
            print("登录失败，程序退出。")
            manager.close()
            return

        while True:
            print("\n========== 图书管理系统（学生端） ==========")
            print("1. 借阅图书")
            print("2. 归还图书")
            print("3. 查看图书状态")
            print("4. 查看我的借阅记录")
            print("0. 退出系统")
            print("============================================")

            choice = input("请输入操作编号：")
            if choice == "1":
                bid = get_int_input("请输入要借阅的图书编号: ")
                manager.borrow_book(bid)
            elif choice == "2":
                bid = get_int_input("请输入要归还的图书编号: ")
                manager.return_book(bid)
            elif choice == "3":
                bid = get_int_input("请输入图书编号: ")
                manager.check_book_status(bid)
            elif choice == "4":
                manager.show_borrowed_books()
            elif choice == "0":
                manager.close()
                print("系统退出成功，再见！")
                break
            else:
                print("无效输入，请输入0-4的数字！")
    else:
        print("无效角色选择，程序退出。")
        manager.close()

if __name__ == "__main__":
    main()