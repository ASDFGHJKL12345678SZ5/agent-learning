"""@timer 装饰器 + 用法演示。"""
import time


def timer(func):
    """装饰器：打印函数执行耗时，不影响原函数功能。"""
    def wrapper(*args, **kwargs):
        # *args 接收按位置传入的参数，**kwargs 接收按名称传入的参数。
        # 这样 wrapper 就能把不同函数的参数原样交给原函数。
        start = time.perf_counter()      # 1. 记开始
        result = func(*args, **kwargs)   # 2. 原函数干活
        end = time.perf_counter()        # 3. 记结束
        print(f"[{func.__name__}] 耗时 {end - start:.6f} 秒")
        return result                    # 4. 原样返回结果
    return wrapper


# ---- 用法演示 ----
@timer
def sum_range(n):
    """从 0 加到 n-1。"""
    return sum(range(n))


@timer
def greet(name):
    time.sleep(0.2)          # 假装"想"了 0.2 秒
    return f"你好，{name}！"


if __name__ == "__main__":
    print("sum_range(1_000_000) 的结果:", sum_range(1_000_000))
    print(greet("小明"))

    # 演示装饰器本质：@timer 就是 timer(greet)
    print("\n不写 @ 等价写法：")
    greet2 = timer(greet)
    print(greet2("小红"))
