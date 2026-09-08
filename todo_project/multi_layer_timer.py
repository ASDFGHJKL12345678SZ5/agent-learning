"""演示：装饰器套多层时，__name__ 的变化和打印行为。"""
import time


def timer(func):
    def wrapper(*args, **kwargs):
        print(f"  进入 wrapper，此时 func 的名字 = {func.__name__}")
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"  [{func.__name__}] 耗时 {end - start:.4f} 秒")
        return result
    return wrapper


@timer
def greet(name):
    time.sleep(0.05)
    return f"你好，{name}！"


if __name__ == "__main__":
    print(f"装饰 1 层后，greet.__name__ = {greet.__name__}")
    print(f"装饰 1 层后，greet.__wrapped__ 不存在: {not hasattr(greet, '__wrapped__')}")
    print("-" * 40)

    # 再套一层：g2 = timer(greet)
    g2 = timer(greet)
    print(f"装饰 2 层后，g2.__name__ = {g2.__name__}")
    print("-" * 40)

    # 再套一层：g3 = timer(g2)
    g3 = timer(g2)
    print(f"装饰 3 层后，g3.__name__ = {g3.__name__}")
    print("-" * 40)

    print("调用 g3('小红')，观察打印条数：")
    result = g3("小红")
    print("返回值:", result)
