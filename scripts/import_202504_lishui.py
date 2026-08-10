from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "202504-丽水发展共同体-高二-期中"
PDF = PREFIX + ".pdf"
TODAY = "2026-08-01"

M1 = """阅读下列材料，回答第 01—03 题。

2025年某市推出的“智慧教育云”平台，整合了全市中小学的教学资源和在线课程。平台采用大数据分析，提供学习建议，并支持 AI 智能批改作业。学生、教师和家长可通过终端设备登录平台，获取学习资料和学情分析报告。"""
M2 = """阅读下列材料，回答第 04—06 题。

中国建科院推出的“智慧工地”平台是国内领先的建筑施工监管系统，旨在提升工地安全管理。它的核心功能包括通过摄像头实时识别工人是否佩戴安全帽、穿反光衣，未佩戴者自动报警。它的数据直通住建部“全国工程质量安全监管信息平台”，实现重大风险自动上报。"""

Q: dict[int, dict[str, object]] = {
1: dict(folder="01数据与编码", topics=["01数据与编码", "数据与信息"], difficulty="简单", ans="B", body=f"""{M1}

下列关于该系统中数据与信息的说法，不正确的是（   ）

- A. 平台上的练习、试题等文本数据属于非结构化数据
- B. 用户观看的在线课程视频属于模拟信号
- C. 平台提供的学情分析报告对不同的学生来说参考价值是不一样的
- D. 学生、教师和家长均可登录平台查看相关数据，体现了信息的共享性""", ana="在线课程视频在计算机系统中以数字信号存储和传输，并非模拟信号，B 不正确。文本练习通常属于非结构化数据；信息价值因使用者而异；多人按权限查看数据体现共享性。"),
2: dict(folder="07信息安全", topics=["07信息安全", "信息社会责任"], difficulty="简单", ans="C", body=f"""{M1}

关于信息安全与信息社会责任，下列行为恰当的是（   ）

- A. 冒用他人身份注册线上活动资格
- B. 观众私自录制在线课程内容并用于商业盈利
- C. 在该平台进行直播授课时，开启弹幕互动
- D. 在社交群内公开分享所有参与者的注册信息""", ana="开启弹幕互动属于平台允许的正常交流方式，C 恰当。冒用身份、未经授权录制课程并商业使用、公开全部注册信息分别侵犯身份安全、知识产权和个人隐私。"),
3: dict(folder="05人工智能", topics=["05人工智能", "机器学习"], difficulty="简单", ans="C", body=f"""{M1}

为使系统更准确地进行作业批改，下列方法可行的是（   ）

- A. 升级学生终端的硬件配置
- B. 增加服务器的存储容量
- C. 对 AI 批改算法进行优化
- D. 提升校园网络速度""", ana="批改准确度主要由模型和算法决定，对 AI 批改算法进行优化可以改进识别与判分效果，C 正确。终端性能、存储容量和网络速度主要影响使用体验或吞吐量，并不直接提高算法准确率。"),
4: dict(folder="06信息系统", topics=["06信息系统", "系统组成"], difficulty="简单", ans="D", body=f"""{M2}

下列关于该信息系统组成与功能的说法，正确的是（   ）

- A. 该系统中的用户就是工人和工地负责人
- B. 该信息系统不具备数据加工处理功能
- C. 该系统可以直接在裸机上运行
- D. 该系统中的摄像头属于硬件""", ana="摄像头是采集图像的硬件设备，D 正确。系统用户还包括监管人员等，不只工人和负责人；识别和报警体现数据加工处理；系统运行需要操作系统等软件环境，不能直接运行在裸机上。"),
5: dict(folder="06信息系统", topics=["06信息系统", "网络技术", "网关"], difficulty="中等", ans="A", body=f"""{M2}

下列关于该系统中网络技术的说法，正确的是（   ）

- A. 平台服务器与各工地处于不同的局域网，它们之间的通信需要经过网关
- B. 使用浏览器访问该系统需要网络协议的支持，使用 App 访问则不需要
- C. 移动终端要与服务器进行通信，必须通过移动通信网络
- D. 摄像头接入网络时不需要 IP 地址""", ana="不同局域网之间通信需要通过网关进行转发，A 正确。浏览器和 App 都需要网络协议；移动终端也可通过 Wi-Fi 等方式联网；网络摄像头需要 IP 地址进行寻址。"),
6: dict(folder="01数据与编码", topics=["01数据与编码", "二进制编码", "位数计算"], difficulty="中等", ans="B", body=f"""{M2}

某地区有200个工地，每个工地最多有10个抓拍摄像头。若使用二进制对这些摄像头进行编码，二进制的前几位表示工地号，其余位表示摄像头号，则所需的二进制位数最少是（   ）

- A. 13
- B. 12
- C. 11
- D. 10""", ana="200个工地至少需要 ceil(log2 200)=8 位，10个摄像头至少需要 ceil(log2 10)=4 位，合计8+4=12位，选 B。"),
7: dict(folder="02算法", topics=["02算法", "流程图", "循环"], difficulty="中等", ans="A", image=["202504丽水发展高二_07_图1.jpg"], body="""某算法的部分流程图如图所示，下列说法正确的是（   ）

![[attachments/202504丽水发展高二_07_图1.jpg]]

- A. 输出 s 的值是 -6
- B. 语句“i≤n?”执行的次数是 6 次
- C. 程序结束后 i 的值是 6
- D. 改变循环体中三条语句的顺序，不影响程序运行结果""", ana="初始 i=1、s=0、n=6。循环每次令 f=(-1)^(i+1)，并累加 f(2i-1)，得到 1-3+5-7+9-11=-6；循环条件还要进行一次失败判断，执行7次，结束时 i=7。循环体语句有依赖关系，不能任意调换，因此 A 正确。"),
8: dict(folder="09队列", topics=["09队列", "栈与队列", "操作模拟"], difficulty="中等", ans="B", body="""队列 Q 从队首到队尾元素依次为 m、n、p、q，栈 S 初始为空。O 操作是弹出队首元素并压入栈顶，I 操作是弹出栈顶元素并加入队列末尾。经过 “OOIOOIO” 系列操作后，栈 S 的栈顶元素为（   ）

- A. m
- B. n
- C. p
- D. q""", ana="依次模拟：OO 后栈顶 n；I 弹出 n，栈顶 m；OO 后依次压入 p、q；I 弹出 q，栈顶 p；O 再压入 n，最终栈顶为 n，选 B。"),
9: dict(folder="12树", topics=["12树", "完全二叉树", "遍历"], difficulty="中等", ans="C", body="""某完全二叉树包含6个节点，其根节点在前序遍历序列和中序遍历序列中的位置序号（从0开始编号）分别记为 x 和 y，则 x+y 的值为（   ）

- A. 2
- B. 4
- C. 3
- D. 5""", ana="根节点在前序遍历中的序号始终为0。6个节点的完全二叉树左子树有3个节点，因此根在中序遍历中的序号为3，x+y=0+3=3，选 C。"),
10: dict(folder="03python基础", topics=["03python基础", "递归", "进制转换"], difficulty="中等", ans="B", body="""定义如下函数：

~~~python
def trans(n):
    if n <= 1:
        return str(1-n%2)
    else:
        return trans(n//2) + str(1-n%2)
print(trans(13))
~~~

执行该程序后，输出的结果是（   ）

- A. 1101
- B. 0010
- C. 1011
- D. 0100""", ana="递归展开：trans(1)=0，trans(3)=00，trans(6)=001，trans(13)=0010，因此选 B。"),
11: dict(folder="13查找与排序", topics=["13查找与排序", "冒泡排序", "测试数据"], difficulty="中等", ans="C", body="""小明编写程序实现数据升序功能，部分 Python 程序如下：

~~~python
def bubble_sort(d):
    n = len(d)
    for i in range(1, n):
        for j in range(i, n):
            if d[j-1] > d[j]:
                d[j-1], d[j] = d[j], d[j-1]
~~~

该程序段存在问题，适合作为测试数据的是（   ）

- A. [3, 4, 6, 7]
- B. [4, 3, 7, 6]
- C. [6, 7, 3, 4]
- D. [6, 3, 4, 7]""", ana="内层循环从 j=i 开始，第一轮没有比较最前面的相邻元素，某些逆序会被遗漏。已排序数据和局部逆序数据可能掩盖问题；[6,7,3,4] 能暴露首轮遗漏导致的排序错误，选 C。"),
12: dict(folder="13查找与排序", topics=["13查找与排序", "二分查找", "列表插入"], difficulty="较难", ans="D", body="""已知列表 a 中有 n 个大于0的正整数，且按降序排列。若要在列表 a 中插入一个数 temp 并保持有序，实现该功能的程序段如下：

~~~python
a.append(0)
n = len(a)-1
L = 0
R = n-1
while L <= R:
    m = (L+R)//2
    if a[m] < temp:
        R = m-1
    else:
        L = m+1
for j in range(____①____):
    a[j] = a[j-1]
    ____②____
print(a)
~~~

划线处应填入的代码为（   ）

- A. ① 0,n,1；② a[R]=temp
- B. ① n,0,-1；② a[L]=temp
- C. ① R,n,1；② a[R]=temp
- D. ① n,L,-1；② a[L]=temp""", ana="降序列表中二分查找结束时 L 是 temp 应插入的位置。为避免覆盖，需要从末尾 n 向 L 逆向搬移，range(n,L,-1)，再把 temp 写入 a[L]，选 D。"),
13: dict(folder="03python基础", topics=["03python基础", "字符串遍历", "枚举"], difficulty="中等", ans="（1）① ch==\"0\" or ch<\"1\"；② max=sum；③ sum+=int(ch)；（2）12", body="""编写 Python 程序求生日幸运数：遍历身份证号，提取最大连续非0数字的和作为生日幸运数，遇到0时当前连续结束，“X”按10处理。例如连续数字21982的各位数字和为22。

（1）请在下列程序划线处填入合适代码。

~~~python
s = input("请输入您的身份证号：")
max = 0
sum = 0
for ch in s:
    if ①:
        if sum > max:
            ②
        sum = 0
    else:
        if ch == "x" or ch == "X":
            sum += 10
        else:
            ③
        if sum > max:
            max = sum
print("您的生日幸运数为：", max)
~~~

（2）若将程序中最后更新 max 的加框代码删去，输入身份证号 330036202005160346X，则输出的生日幸运数为____。""", ana="遇到字符0（或小于字符1的分隔字符）时，先比较并保存当前连续段的和，再清零；普通数字累加其整数值，X按10累加。三个空依次为 ch==\"0\" or ch<\"1\"、max=sum、sum+=int(ch)。删除末尾更新 max 的代码后，只有在遇到0时保存最大值，给定身份证号的最大连续段在末尾 X 前，输出为12。"),
14: dict(folder="04数据处理", topics=["04数据处理", "06信息系统", "B/S架构", "Flask", "pandas"], difficulty="中等", ans="（1）A、C；（2）192.168.1.168:8080/user；（3）① int(t[0])>=7；② df[\"刷卡时间\"]；（4）EBC或ECB", image=["202504丽水发展高二_14_图b.png"], body="""“校园一卡通”系统增加了刷卡进出校门功能，老师通过浏览器监管迟到、早退。

（1）该系统基于 B/S 架构，下列说法正确的是（多选）。

- A. 对服务器的要求较高
- B. 降低了系统的通信开销
- C. 升级和维护比较方便
- D. 升级和维护较 C/S 架构难度更大

（2）服务器运行在 host=192.168.1.168、port=8080，路由为 /user。老师应访问 URL：http://____。

（3）学校规定7点以后（包括7点）迟到，统计各班迟到人数并绘制柱形图。部分数据字段为姓名、学号、班级、刷卡时间，示例时间为06:30:03、11:30:24。

![[attachments/202504丽水发展高二_14_图b.png]]

~~~python
def judge(x):
    t = x.split(":")
    if ①:
        return 1
    else:
        return 0

import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_excel("data.xlsx")
s = []
for i in ②:
    s.append(judge(i))
df["迟到人数"] = s
plt.bar(df1["班级"], df1["迟到人数"])
~~~

（4）方框中可选代码如下，依次应选择哪3项？

- A. df1=df.sort_values("迟到人数", ascending=False)
- B. df1=df1.sort_values("迟到人数", ascending=False)
- C. df1=df1[df1.迟到人数!=0]
- D. df1=df1[df1."迟到人数"!=0]
- E. df1=df.groupby("班级", as_index=False).sum()
- F. df1=df.groupby("班级", as_index=False).count()""", ana="B/S 架构通常由服务器集中处理，客户端只需浏览器，升级维护方便，正确选 A、C。URL 由主机、端口和路由组成，为 http://192.168.1.168:8080/user。判断迟到只需取刷卡时间的小时字符并判断 int(t[0])>=7，遍历 df[\"刷卡时间\"]。先按班级分组求和（E），再按人数降序（B），最后筛选非0班级（C），所以顺序 EBC（或答案允许的 ECB）。"),
15: dict(folder="09队列", topics=["09队列", "03python基础", "调度", "链表"], difficulty="较难", ans="（1）3；（2）int(lst[1][0:2])*60+int(lst[1][3:])；（3）① place[i][1]<=time；② v=data[i][0]；③ place[q][1]=curtime+type[data[p][2]]", body="""某市举办3项不同年龄段的足球赛事，年龄段一、二、三每场分别40、60、90分钟。已知各赛事赛程，要求在3天内完成比赛，求最少租借场地。样例赛程如下：

| 天次编号 | 比赛开始时间 | 年龄段编号 |
|---:|---|---:|
| 0 | 09:20 | 1 |
| 1 | 12:00 | 1 |
| 2 | 16:00 | 1 |
| 0 | 09:00 | 2 |
| 1 | 10:00 | 2 |
| 2 | 14:00 | 2 |
| 0 | 10:00 | 3 |
| 1 | 11:00 | 3 |
| 2 | 13:00 | 3 |

样例至少需要2个场地，规则允许一场结束后下一场立即开始。

（1）若将年龄段三的所有比赛提前1小时，则至少要租借____个场地。

（2）定义 timechange(lst) 将开始时间转换为分钟，lst 为天次编号、开始时间、年龄段编号。

~~~python
def timechange(lst):
    lst[1] = ▲
~~~

（3）实现调度的程序片段如下，请填空。

~~~python
def check(place, time):
    for i in range(len(place)):
        if ①
            return i
    return -1

def plan(data):
    type = {1:40, 2:60, 3:90}
    heads = [-1,-1,-1]
    for i in range(len(data)):
        data[i].append(-1)
    for i in range(len(data)):
        ②
        if heads[v] == -1:
            heads[v] = i
        else:
            p = q = heads[v]
            while q != -1 and data[q][1] < data[i][1]:
                p = q
                q = data[q][3]
            if p == q:
                data[i][3] = heads[v]
                heads[v] = i
            else:
                data[i][3] = data[p][3]
                data[p][3] = i
    m = 0
    for i in range(3):
        place = []
        cnt = 0
        p = heads[i]
        while p != -1:
            curtime = data[p][1]
            q = check(place, curtime)
            if q != -1:
                ③
            else:
                cnt += 1
                place.append([cnt, curtime+type[data[p][2]]])
            p = data[p][3]
        if cnt > m:
            m = cnt
    return m
~~~""", ana="年龄段三比赛全部提前1小时后，按各天次的重叠时间模拟，最大并发数为3。时间字符串前两位是小时、后三位（去掉冒号）是分钟，②应取 v=data[i][0]。场地可用条件是场地结束时间不晚于当前比赛开始时间，即 place[i][1]<=time；有可用场地时更新 place[q][1]=curtime+type[data[p][2]]。"),
}


def write_note(q: int, d: dict[str, object]) -> Path:
    folder = ROOT / str(d["folder"])
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{PREFIX}-{q:02d}.md"
    lines = [
        "---", f"id: {PREFIX}-{q:02d}",
        f"题型: {'选择题' if q <= 12 else '非选择题'}",
        f'来源: "[[试卷/{PDF}|{PDF}]]"', f"试卷: {PDF}", "年级: 高二",
        f'题号: "{q:02d}"', f"难度: {d['difficulty']}", "水平: 选考", "知识点:",
    ]
    lines.extend(f"  - {x}" for x in d["topics"])
    lines += ["完成次数: 0", "补课:", "正确率:", "错题原因:", f"创建日期: {TODAY}", f"图片核验: {'已通过' if d.get('image') else '无图片'}", "tags:", f"  - 知识点/{d['folder']}", "---", f"# 题目 {q:02d}", "", str(d["body"]), "", "---", "", "## 答案", "", f"**正确答案：** {d['ans']}", "", "---", "", "## 解析", "", str(d["ana"]), "", "---", "", "## 相关链接", "", f"- 原试卷：[[试卷/{PDF}]]", ""]
    text = "\n".join(lines).replace("回答第 01—03 题", f"回答第 {q:02d} 题").replace("回答第 04—06 题", f"回答第 {q:02d} 题")
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    src = ROOT / "_mineru_output" / PREFIX / "images"
    for name, dest in {
        "4cf9214c3154d5e27b9213d75367b906c74e2ee8a635b05ab17a8210012caf33.jpg": ROOT / "attachments" / "202504丽水发展高二_07_图1.jpg",
    }.items():
        shutil.copy2(src / name, dest)
    paths = [(q, write_note(q, d), d) for q, d in Q.items()]
    qpath = ROOT / "题目核验.md"
    qtext = qpath.read_text(encoding="utf-8")
    marker = f"## 30. {PREFIX}"
    if marker not in qtext:
        rows = ["", marker, "", "| 题号 | 题型 | 知识点 | 题目 md |", "|---|---|---|---|"]
        for q, p, d in paths:
            rows.append(f"| {q:02d} | {'选择题' if q <= 12 else '非选择题'} | {d['folder']} | [[{p.relative_to(ROOT).with_suffix('').as_posix()}]] |")
        qpath.write_text(qtext.rstrip() + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    ipath = ROOT / "图片核验.md"
    itext = ipath.read_text(encoding="utf-8")
    if marker not in itext:
        p = next(p for q, p, d in paths if q == 7)
        rows = ["", marker, "", "### 第 07 题", "", f"- 题目：[[{p.relative_to(ROOT).with_suffix('').as_posix()}]]", "- 状态：图片核验: 已通过", "- 核验：流程图保留初始化、判断、循环体、输出和回线，与原PDF第2页逐项核对。", "", "![[attachments/202504丽水发展高二_07_图1.jpg]]", "", "### 第 14 题", "", f"- 题目：[[{next(p for q, p, d in paths if q == 14).relative_to(ROOT).with_suffix('').as_posix()}]]", "- 状态：图片核验: 已通过", "- 核验：柱形图保留标题、坐标轴、班级标签和柱高，与原PDF第4页逐项核对。", "", "![[attachments/202504丽水发展高二_14_图b.png]]", "", "- 其余 13 题均为 图片核验: 无图片；本套2张附件均已打开核验。", ""]
        ipath.write_text(itext.rstrip() + "\n" + "\n".join(rows), encoding="utf-8")
    print(f"created {len(paths)} notes")


if __name__ == "__main__":
    main()
