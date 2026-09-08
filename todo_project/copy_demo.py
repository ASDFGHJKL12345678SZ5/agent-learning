"""浅拷贝 vs 深拷贝 —— copy.copy vs copy.deepcopy"""
import copy

# 一个"外层列表套着一个内层列表"的结构
original = [1, 2, [3, 4]]

# 三种得到新变量的方式
alias     = original            # 1. 只是贴标签（同一个对象！）
shallow   = copy.copy(original)     # 2. 浅拷贝
deep      = copy.deepcopy(original) # 3. 深拷贝


def show(name, obj):
    print(f"{name:8} = {obj}")


print("### 拷贝前的三个比较（is 判断是否同一个对象）")
print("alias   is original?  ", alias   is original)   # True，它们根本是同一个
print("shallow is original?  ", shallow is original)   # False，外层是新对象
print("deep    is original?  ", deep    is original)   # False，外层是新对象

print("\n### 关键：外层里那个 [3,4]，它们是否共享？")
print("shallow[2] is original[2]?  ", shallow[2] is original[2])  # True! 内层还共用
print("deep[2]    is original[2]?  ", deep[2]    is original[2])  # False，内层也复制了

print("\n### 改动实验：分别修改它们的内层列表，看谁互相影响")
# 只有 shallow 的内层和 original 是共用的
shallow[2].append(99)     # 改 shallow 的内层
print("改完 shallow[2] 加 99 后：")
show("original", original)
show("shallow", shallow)
show("deep", deep)
print("→ original 也出现 99（被浅拷贝连累），deep 不受影响")

print("\n### 补充：在外层 append 一个元素，会不会互相影响？")
alias.append(100)
print("alias 加了 100（它们同一个对象，original 也会有）：")
show("original", original)

shallow.append(200)
deep.append(300)
print("shallow/deep 各自在外层 append：")
show("original", original)   # 不受影响，因为外层本来就是新对象
show("shallow", shallow)
show("deep", deep)
