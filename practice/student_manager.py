# 学生成绩管理系统（列表 + 字典实现增删改查）

students = []  # 外层列表：存储所有学生记录


def show_menu():
    print("\n" + "=" * 25)
    print("   学生成绩管理系统")
    print("=" * 25)
    print("1. 添加学生")
    print("2. 删除学生")
    print("3. 修改成绩")
    print("4. 查询单个学生")
    print("5. 显示所有学生")
    print("6. 退出系统")
    print("=" * 25)


def add_student():
    student_id = input("请输入学号: ").strip()
    # 检查学号是否已存在
    for s in students:
        if s["id"] == student_id:
            print("错误：该学号已存在！")
            return

    name = input("请输入姓名: ").strip()
    try:
        score = float(input("请输入成绩: ").strip())
    except ValueError:
        print("错误：成绩必须是有效数字！")
        return

    # 字典存储单条记录，追加到列表中
    student = {"id": student_id, "name": name, "score": score}
    students.append(student)
    print(f"成功添加学生：{name}")


def delete_student():
    student_id = input("请输入要删除的学生学号: ").strip()
    for s in students:
        if s["id"] == student_id:
            students.remove(s)
            print(f"学号 {student_id} 的学生已删除！")
            return
    print("未找到该学号的学生！")


def update_student():
    student_id = input("请输入要修改成绩的学生学号: ").strip()
    for s in students:
        if s["id"] == student_id:
            try:
                new_score = float(input(f"请输入 {s['name']} 的新成绩: ").strip())
            except ValueError:
                print("错误：成绩必须是有效数字！")
                return
            s["score"] = new_score
            print("成绩修改成功！")
            return
    print("未找到该学号的学生！")


def query_student():
    student_id = input("请输入要查询的学生学号: ").strip()
    for s in students:
        if s["id"] == student_id:
            print("\n--- 学生信息 ---")
            print(f"学号: {s['id']} | 姓名: {s['name']} | 成绩: {s['score']}")
            return
    print("未找到该学号的学生！")


def list_all_students():
    if not students:
        print("暂无学生数据！")
        return

    print("\n{:<10} {:<10} {:<10}".format("学号", "姓名", "成绩"))
    print("-" * 30)
    for s in students:
        print("{:<10} {:<10} {:<10}".format(s["id"], s["name"], s["score"]))


def main():
    while True:
        show_menu()
        choice = input("请选择操作 (1-6): ").strip()

        if choice == "1":
            add_student()
        elif choice == "2":
            delete_student()
        elif choice == "3":
            update_student()
        elif choice == "4":
            query_student()
        elif choice == "5":
            list_all_students()
        elif choice == "6":
            print("感谢使用，系统退出。")
            break
        else:
            print("无效输入，请重新输入 1-6 之间的数字！")


if __name__ == "__main__":
    main()