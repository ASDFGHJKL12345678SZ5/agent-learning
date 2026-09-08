"""演示 TodoList 的持久化：运行两次，观察数据还在不在。"""
from todo_list import TodoList

print("=" * 40)
print("第一次运行：添加两条待办")
print("=" * 40)
tl = TodoList("todos.json")
tl.add("买牛奶")
tl.add("给导师回邮件")
tl.add("跑 30 分钟")
tl.show()

print("\n删除 id=2（回邮件那条）再删一条不存在的 id=99：")
tl.delete(2)
tl.delete(99)
tl.show()

print("\n标记 id=3 为已完成：")
tl.mark_done(3)
tl.show()

print("\n程序结束。请再次运行本脚本，看清单是否还在。")
