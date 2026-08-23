def run_Calculator():
    print("===CLI计算器（输入q退出）===")
    while True:
        num1=input("\n请输入第一个数字：")
        if num1.lower()=='q':
            break

        operator=input("请输入运算符（+，-，*，/）：")
        if operator.lower()=='q':
            break

        num2=input("请输入第二个数字：")
        if num2.lower()=='q':
            break

        try:
            num1=float(num1)
            num2=float(num2)
        except ValueError:
            print("输入无效，请输入数字。")
            continue

        if operator=='+':
            result=num1+num2
        elif operator=='-':
            result=num1-num2
        elif operator=='*':
            result=num1*num2
        elif operator=='/':
            if num2==0:
                print("除数不能为零。")
                continue
            result=num1/num2
        else:
            print("无效的运算符，请输入 +，-，* 或 /。")
            continue

        print(f"结果：{num1} {operator} {num2} = {result}") 

if __name__=="__main__":
    run_Calculator()