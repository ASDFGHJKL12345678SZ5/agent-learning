"""斐波那契生成器 + 用法演示。"""
from itertools import islice


def fib():
    """无限斐波那契生成器：0, 1, 1, 2, 3, 5, 8, ...

    用 yield 实现"按需一个个吐"，内存只占一个数。
    因为是无限序列，绝不能用 return 一次算完。
    """
    a, b = 0, 1
    while True:            # 永不停——反正你只取走你要的那几个
        yield a            # 吐出当前 a，然后暂停
        a, b = b, a + b    # 滚动到下一对；下次 next() 从这里继续


def fib_n(n):
    """用 list 前 n 个斐波那契数（演示小规模时可以直接接住）。"""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


if __name__ == "__main__":
    # 方法1：for 循环逐个取（推荐，惰性、省内存）
    print("前 8 个斐波那契数（for 循环逐个拿）：")
    for i, v in zip(range(8), fib()):
        print(v, end=" ")
    print()

    # 方法2：手动 next() 一个个拿，体会"暂停/继续"
    print("\n手动 next() 逐个取：")
    g = fib_n(4)
    print(next(g))          # 0
    print(next(g))          # 1
    print(next(g))
    print(next(g))          # 1
    # print(next(g))        # 到这里会抛 StopIteration，因为没有第 4 个了

    # 方法3：用 islice 掐前几个
    # islice 用来对迭代器做切片；这里取 fib() 产生的前 10 个值，
    # 不会一次性生成无限序列。
    print("\nislice 取前 10 个：", list(islice(fib(), 10)))

    # 演示内存优势：惰性生成，一次只算一个，不把整个序列存进内存。
    # 取第 1000 个斐波那契数：普通列表法要先把前面 1000 个全算出来，
    # 生成器则一个个滚过去，内存几乎不涨。
    gen = fib()
    # 这也是一种导入写法：从 itertools 模块导入 islice，并在本文件中
    # 用别名 _islice 引用它。等价于：import itertools，然后写
    # itertools.islice(...)。这里的 _islice 没有实际使用，可删除；上面
    # 已经通过 from itertools import islice 导入了同一个函数。
    from itertools import islice as _islice
    value_1000 = next(_islice(fib(), 999, 1000))   # 跳过前 999 个，取第 1000 个
    print("\n第 1000 个斐波那契数有", len(str(value_1000)), "位")
    print("而生成器对象本身的内存占用:", end=" ")
    print(f"{__import__('sys').getsizeof(gen)} 字节（和数字大小无关）")
