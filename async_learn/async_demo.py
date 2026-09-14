"""异步 vs 同步：用"等待时间是否重叠"一眼看懂异步的价值。"""
import asyncio
import time


# ---------- 同步版：用 time.sleep（阻塞） ----------
def sync_task(name, seconds):
    # seconds 表示等待时长，单位是秒；seconds=1 就是等待 1 秒。
    print(f"  [{name}] 开始")
    # time.sleep(seconds) 会暂停当前线程指定的秒数，期间不能执行其他任务。
    time.sleep(seconds)          # 阻塞：整个程序在这里干等
    print(f"  [{name}] 结束")


# ---------- 异步版：用 await asyncio.sleep（非阻塞） ----------

async def async_task(name, seconds):
    """异步等待：遇到 await 时让出事件循环，等待期间可运行其他任务。"""
    print(f"  [{name}] 开始")
    await asyncio.sleep(seconds)
    print(f"  [{name}] 结束")



async def run_async_concurrent():
    """用 gather 让三个任务"并发"执行。"""
    await asyncio.gather(
        async_task("A", 1),
        async_task("B", 1),
        async_task("C", 1),
    )


async def run_async_sequential():
    """异步但一个接一个 await（没并发），耗时和同步一样。"""
    await async_task("A", 1)
    await async_task("B", 1)
    await async_task("C", 1)


if __name__ == "__main__":
    print("===== 1) 同步：一个一个来 =====")
    start = time.perf_counter()
    sync_task("A", 1)
    sync_task("B", 1)
    sync_task("C", 1)
    print(f"  ⏱ 总耗时: {time.perf_counter() - start:.2f} 秒\n")

    print("===== 2) 异步但顺序 await（没并发）=====")
    start = time.perf_counter()
    asyncio.run(run_async_sequential())
    print(f"  ⏱ 总耗时: {time.perf_counter() - start:.2f} 秒\n")

    print("===== 3) 异步 + gather 并发 =====")
    start = time.perf_counter()
    asyncio.run(run_async_concurrent())
    print(f"  ⏱ 总耗时: {time.perf_counter() - start:.2f} 秒")
