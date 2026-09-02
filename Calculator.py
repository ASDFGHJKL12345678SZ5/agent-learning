# 列表推导式重写计算器（批量数据运算与过滤）


def run_batch_calculator():
    print("=== 批量推导式计算器（输入 'q' 退出）===")

    while True:
        raw_input = input("\n请输入一组数字（用空格隔开，如 10 20 30）: ").strip()
        if raw_input.lower() == "q":
            break

        # 核心：列表推导式批量进行字符串拆分与浮点转换
        try:
            nums = [float(x) for x in raw_input.split()]
        except ValueError:
            print("错误：请确保输入的全部都是有效数字！")
            continue

        if not nums:
            print("错误：输入不能为空！")
            continue

        op = input("请选择统一批量运算 (+, -, *, /): ").strip()
        if op.lower() == "q":
            break

        try:
            val = float(input("请输入操作数值: ").strip())
        except ValueError:
            print("错误：操作数必须是有效数字！")
            continue

        # 核心：利用列表推导式进行批量数值映射
        if op == "+":
            results = [x + val for x in nums]
        elif op == "-":
            results = [x - val for x in nums]
        elif op == "*":
            results = [x * val for x in nums]
        elif op == "/":
            if val == 0:
                print("错误：除数不能为 0！")
                continue
            results = [x / val for x in nums]
        else:
            print("错误：不支持的运算符！")
            continue

        print(f"原数据: {nums}")
        print(f"运算后: {results}")

        # 核心：带条件的列表推导式（过滤正数/及格数示例）
        positives = [x for x in results if x > 0]
        print(f"其中大于0的数值: {positives}")


if __name__ == "__main__":
    run_batch_calculator()