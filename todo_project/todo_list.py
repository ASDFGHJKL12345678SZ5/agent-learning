"""TodoList 类：add / delete / show / save，用 JSON 文件持久化。"""
import json
import os


class TodoList:
    """带文件持久化的待办清单。

    每个待办是一条字典：{"id": 1, "task": "买牛奶", "done": False}
    """

    def __init__(self, filename="todos.json"):
        self.filename = filename          # 保存到哪个文件
        self.todos = self._load()         # 启动时从文件读回来
        # 下一个可用 id = 现有最大 id + 1（这样删了也不重复）
        self._next_id = max((t["id"] for t in self.todos), default=0) + 1

    # ---- 文件持久化两个核心方法 ----
    def _load(self):
        """从 JSON 文件读回清单；文件不存在就返回空清单。"""
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)          # JSON 文本 -> Python 对象
        return []

    def save(self):
        """把当前清单写入 JSON 文件。"""
        with open(self.filename, "w", encoding="utf-8") as f:
            # ensure_ascii=False 让中文正常显示，indent=2 让文件更好读
            json.dump(self.todos, f, ensure_ascii=False, indent=2)

    # ---- 业务方法 ----
    def add(self, task):
        """新增一条待办，并立刻落盘。"""
        if not task or not task.strip():
            raise ValueError("任务内容不能为空")
        self.todos.append({
            "id": self._next_id,
            "task": task,
            "done": False,
        })
        self._next_id += 1
        self.save()                          # 改完马上保存

    def delete(self, task_id):
        """按 id 删除一条待办；找不到就提示。"""
        before = len(self.todos)
        self.todos = [t for t in self.todos if t["id"] != task_id]
        if len(self.todos) == before:
            print(f"没有找到 id={task_id} 的任务")
        else:
            self.save()
            print(f"已删除 id={task_id}")

    def mark_done(self, task_id):
        """把某条任务标记为已完成（顺便演示改单条数据）。"""
        for t in self.todos:
            if t["id"] == task_id:
                t["done"] = True
                self.save()
                print(f"已完成 id={task_id}: {t['task']}")
                return
        print(f"没有找到 id={task_id} 的任务")

    def show(self):
        """打印当前所有待办。"""
        if not self.todos:
            print("（清单是空的）")
            return
        for t in self.todos:
            status = "[x]" if t["done"] else "[ ]"
            print(f"{status} #{t['id']}  {t['task']}")
