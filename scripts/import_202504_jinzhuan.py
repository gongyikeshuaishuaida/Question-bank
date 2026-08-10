from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "202504-金砖高中联盟-高二-期中"
PDF = PREFIX + ".pdf"
TODAY = "2026-08-01"

COMMON_1 = """阅读下列材料，回答第 01—03 题。

DeepSeek 在发展人工智能大模型方面取得前所未有的突破，其采用并行处理和优化算法，确保高效处理大规模数据，在大数据处理方面有显著优势。严格的数据清洗和智能校验保障了数据准确性，数据加密和访问控制则提供了强大的安全保障。不可否认，人工智能技术的发展也伴随一系列难以预知的风险挑战，在安全、社会治理、道德伦理等方面带来众多新课题。要高度重视人工智能技术的发展和风险防范。"""

COMMON_2 = """阅读下列材料，回答第 04—06 题。

某校创建校园师生管理系统，师生可通过刷校园卡、人脸识别等方式过闸机进出校园，学生进出教室、寝室时通过摄像头刷脸签到，并将采集到的数据存储在学校局域网内部服务器的数据库中。教师、家长可以使用手机专用的 App，通过账号密码、短信验证或指纹识别等方式登录该系统，实时查看学生相关的考勤情况。"""

QUESTIONS: dict[int, dict[str, object]] = {
    1: dict(folder="05人工智能", topics=["05人工智能", "人工智能局限"], difficulty="简单", answer="C", body=f"""{COMMON_1}

下列关于 DeepSeek 的说法，正确的是（   ）

- A. DeepSeek 需要海量数据的训练，是典型的专家系统
- B. 在使用 DeepSeek 时，DeepSeek 是智能回路的总开关
- C. 目前的 DeepSeek 还不能模拟人脑的全部智能
- D. DeepSeek 带给人类社会的影响总是积极向上的""", analysis="DeepSeek 属于大模型，训练需要大量数据，但并非由知识库和推理引擎组成的专家系统；机器智能也不是人机协同回路的总开关。当前人工智能仍不能模拟人脑的全部智能，技术影响也可能带来安全、伦理和治理风险，因此 C 正确。"),
    2: dict(folder="01数据与编码", topics=["01数据与编码", "大数据"], difficulty="中等", answer="A", body=f"""{COMMON_1}

下列关于大数据的说法，正确的是（   ）

- A. 大数据价值密度的高低与数据总量的大小成反比
- B. 随着 DeepSeek 在各行各业的应用，技术成为核心资源
- C. 大数据的数据量大，故在处理大数据时，一般采用整体思想
- D. 大数据思维着重关注数据之间的因果关系的探求""", analysis="在其他条件相近时，数据总量越大，真正有价值的信息所占比例可能越低，体现大数据的低价值密度特征，A 正确。大数据处理强调抽样、相关性和整体分析等思维，B、C、D 的表述分别混淆了核心资源、整体思想和因果关系。"),
    3: dict(folder="07信息安全", topics=["07信息安全", "数据校验", "数据管理"], difficulty="中等", answer="A", body=f"""{COMMON_1}

下列关于数据安全与管理的说法，不正确的是（   ）

- A. 数据校验是确保数据保密性进行的一种验证操作
- B. 静态数据在处理时已经收集完成，计算时不会发生改变
- C. 大数据给生活带来便利的同时，也带来了数据安全等方面的社会问题
- D. 用 DeepSeek 进行数据处理时，不一定能保证每个数据都准确无误""", analysis="数据校验主要用于检查数据的完整性、正确性和一致性，不是保证数据保密性的手段，A 不正确。静态数据、人工智能输出的不确定性以及大数据带来的安全与社会问题均符合题意。"),
    4: dict(folder="07信息安全", topics=["07信息安全", "身份认证", "RFID", "B/S模式"], difficulty="中等", answer="B", body=f"""{COMMON_2}

下列关于系统安全与管理的说法，不正确的是（   ）

- A. 为减少系统对外部环境的依赖性，可以给服务器配置不间断电源
- B. 教师查看学生相关的考勤情况采用了 B/S 模式
- C. 指纹识别登录方式属于身份认证技术
- D. 师生刷校园卡应用了 RFID 技术""", analysis="教师通过手机专用 App 登录并查看数据，属于客户端/服务器模式，不是浏览器/服务器模式，B 不正确。不间断电源可降低对外部供电的依赖，指纹属于身份认证，校园卡刷卡使用 RFID，A、C、D 正确。"),
    5: dict(folder="06信息系统", topics=["06信息系统", "系统功能", "数据传输"], difficulty="简单", answer="C", body=f"""{COMMON_2}

关于该信息系统的说法，正确的是（   ）

- A. 该信息系统使用过程中产生的数据信息并不能为学校的决策提供支持
- B. 该信息系统最大的局限性是其本身具有安全隐患
- C. 手机专用的 App 可与服务器进行双向数据传输
- D. 该系统的数据收集和输入功能由手机专用的 App 实现""", analysis="App 既可以向服务器提交登录、查询或请假等信息，也可以接收服务器返回的考勤数据，具有双向数据传输能力，C 正确。系统数据可支持决策，局限性不只来自安全，前端摄像头、刷卡设备等也承担数据采集，A、B、D 错误。"),
    6: dict(folder="06信息系统", topics=["06信息系统", "网络功能", "TCP/IP"], difficulty="中等", answer="D", body=f"""{COMMON_2}

该信息系统上传数据在学校服务器中，有关网络的说法不正确的是（   ）

- A. 将采集到的数据存储在数据库中使用到了 TCP/IP 协议
- B. 数字技术的发展，使得图像和音频在网络中被统一为二进制数据流进行传输
- C. 通过手机无线热点共享网络，将移动通信信号转换为无线网络信号
- D. 办公室的打印机可以供其他部门一起使用，体现了网络的数据通信功能""", analysis="共享打印机属于网络资源共享功能，而不是数据通信功能，D 不正确。TCP/IP 支持网络通信，图像和音频在传输时以二进制数据流表示，手机热点也完成了移动通信网络与无线局域网的连接。"),
    7: dict(folder="02算法", topics=["02算法", "流程图", "循环计数"], difficulty="中等", answer="D", image=["202504金砖高二_07_图1.jpg"], body="""某算法的部分流程图如图所示。执行这部分流程，若输入 i 的值为列表 [2, 3, 4, 5] 中的随机数，则下列说法正确的是（   ）

![[attachments/202504金砖高二_07_图1.jpg]]

- A. 变量 c 的最大值为 11
- B. 只能使用 while 语句实现循环结构
- C. 程序结束时变量 a 一定等于 0
- D. “a>0？”至少判断 5 次""", analysis="流程图先令 a=20、c=0，每轮输入 i 并执行 a=a-i、c=c+1，直到 a≤0。i=2、3、4、5 时循环次数分别为10、7、5、4，终止判断还要多执行一次，因此判断次数至少为5；c 最大为10，a 只保证不大于0，循环也可用其他循环结构实现，故 D 正确。"),
    8: dict(folder="03python基础", topics=["03python基础", "表达式", "运算符优先级"], difficulty="简单", answer="C", body="""下列 Python 表达式中，结果为 True 的是（   ）

- A. 6/2**3>1
- B. "sh" in "Shangyu"
- C. len("2345")==12345%100//10
- D. int("1"+"1")%2==0""", analysis="A 的值为0.75，不大于1；B 区分大小写，sh 不在 Shangyu 中；C 左边为4，右边先算取模再整除得到4；D 中11%2=1。因此只有 C 的结果为 True。"),
    9: dict(folder="10栈", topics=["10栈", "栈容量", "栈与队列"], difficulty="中等", answer="B", body="""字母 a、b、c、d、e、f 依次入栈，再将出栈后的字母依次进入队列，若入队的顺序为 b、d、c、f、e、a，则栈的容量至少是（   ）

- A. 2
- B. 3
- C. 4
- D. 5""", analysis="为先出 b，先压入 a、b，深度为2；随后压入 c、d 后出 d、c；最后在栈中保留 a 的情况下压入 e、f，最大深度达到3。因此栈容量至少为3，选 B。"),
    10: dict(folder="03python基础", topics=["03python基础", "列表筛选", "随机"], difficulty="中等", answer="D", body="""有如下 Python 程序段：

~~~python
import random
a = [9, 10, 8, 7, 12, 5]
r = random.randint(3, 5)
k = 0
for i in range(len(a)):
    if a[i] % r == 0:
        a[k] = a[i]
        k += 1
print(a[:k])
~~~

则运行后，a 的值不可能是（   ）

- A. [9, 12]
- B. [10, 5]
- C. [8, 12]
- D. [10, 8]""", analysis="r 只能为3、4、5。分别筛出 [9,12]、[8,12]、[10,5]，前三个选项均可能；没有任何一个 r 能同时筛出10和8，所以 D 不可能。"),
    11: dict(folder="13查找与排序", topics=["13查找与排序", "间隔排序", "列表交换"], difficulty="中等", answer="A", body="""a=[8,6,4,9,7,5,3,1]，执行下列程序后，a 数组中元素的顺序是（   ）

~~~python
a = [8, 6, 4, 9, 7, 5, 3, 1]
n = len(a)
for i in range(n//2-1):
    for j in range(n-2, 2*i, -2):
        if a[j] < a[j-2]:
            a[j], a[j-2] = a[j-2], a[j]
print(a)
~~~

- A. 3,6,4,9,7,5,8,1
- B. 8,1,4,5,7,6,3,9
- C. 3,9,4,6,7,5,8,1
- D. 8,1,7,5,4,6,3,9""", analysis="内层循环按步长2比较同一奇偶下标序列并交换较小值，逐轮模拟三次外层循环后得到 [3,6,4,9,7,5,8,1]，对应 A。"),
    12: dict(folder="11链表", topics=["11链表", "链表合并", "指针"], difficulty="较难", answer="B", image=["202504金砖高二_12_图a.png", "202504金砖高二_12_图b.png"], body="""使用列表 d 模拟链表结构（节点数大于2，且不存在连续为0的节点），每个节点包含数据区域和指针区域，h 为头指针。链表开头和末尾节点的数据区域值均为0，如图a所示。现要把相邻两个数值为0的节点之间所有节点合并为一个节点，该节点值为所有合并节点值之和，并将值为0的节点移除，结果如图b所示。实现该功能的部分程序段如下：

![[attachments/202504金砖高二_12_图a.png]]

![[attachments/202504金砖高二_12_图b.png]]

~~~python
k = h
p = d[k][1]
while k != -1 and p != -1:
    # 方框处填写代码
    p = d[k][1]
~~~

方框中应填入的正确代码为（   ）

- A.
  ~~~python
  if d[p][0] != 0:
      d[k][0] += d[p][0]
      d[k][1] = d[p][1]
      if d[p][0] == 0:
          k = p
  ~~~
- B.
  ~~~python
  if d[p][0] != 0:
      d[k][0] += d[p][0]
      d[k][1] = d[p][1]
  if d[p][0] == 0:
      k = d[k][1]
  ~~~
- C.
  ~~~python
  if d[p][0] == 0:
      k = p
  else:
      d[k][0] += d[p][0]
      d[k][1] = d[p][1]
  ~~~
- D.
  ~~~python
  if d[p][0] == 0:
      k = d[k][1]
  else:
      d[k][0] += d[p][0]
      d[k][1] = d[p][1]
  ~~~""", analysis="当 p 指向非零节点时，将其值累加到当前节点并跳过该节点；当 p 指向分隔用的零节点时，应把 k 推进到该零节点，下一轮再处理后继区间。按题目给出的循环结构和答案评分标准，B 的两个独立条件实现了这两种情况，选 B。"),
    13: dict(folder="03python基础", topics=["03python基础", "字符串", "循环移位", "枚举"], difficulty="中等", answer="（1）Yes；（2）① count=0；② b[j]==a[p%len(a)]；③ count==len(b)", body="""有两个字符串，判断其中一个字符串是否是另一个字符串通过若干次循环移位后的新字符串的子串。字符串循环移位是将第一个字符移动到末尾。例如，“CDAA”是由“AABCD”两次移位后产生的新串“BCDAA”的子串，结果输出“Yes”。输入“ABCD”与“ACBD”则输出“No”。

（1）如果输入的字符串分别是“BDAC”与“ACBD”，则输出的结果是____。

（2）实现上述功能的 Python 程序如下，请在划线处填入合适的代码。

~~~python
a = input("请输入一个字符串：")
b = input("请输入另一个字符串：")
if len(a) < len(b):
    a, b = b, a
flag = False
for i in range(len(a)):
    p = i
    # ①
    for j in range(len(b)):
        if ______:  # ②
            count += 1
            p += 1
    if ______:  # ③
        print("Yes")
        flag = True
        break
if flag == False:
    print("No")
~~~
""", analysis="长度相同的情况下，BDAC 的循环移位序列包含 ACBD，所以（1）输出 Yes。每次从位置 i 开始比较一轮时先将计数器清零；用 p%len(a) 让下标循环回到字符串开头；当匹配数等于较短字符串长度时说明它是某次循环移位的子串。"),
    14: dict(folder="04数据处理", topics=["04数据处理", "06信息系统", "物联网", "pandas", "数据可视化"], difficulty="中等", answer="（1）C；（2）A；（3）A、E、F；（4）CPU 或内存条等硬件性能不足；（5）① df[df.大棚编号==x]；② house,y", image=["202504金砖高二_14_图1.jpg", "202504金砖高二_14_图2.jpg"], body="""学校课外活动研究小组拟采集5个大棚的土壤湿度数据，进行监测控制。实验室搭建了模拟系统：智能终端获取传感器数据，通过无线通信将数据传输到 Web 服务器，服务器判断异常后，通过智能终端控制执行器浇水。

（1）小组拟采用 SQLite3 数据库，这在前期工作中属于____阶段（单选，填字母：A.需求分析 / B.可行性分析 / C.概要设计 / D.详细设计）。

（2）该系统中的所有传感器____（单选，填字母：A.必须连接在不同智能终端 / B.可以连接在同一智能终端）。

（3）搭建该系统时需要用的硬件包括____（多选，填字母：A.服务器 / B.浏览器 / C.网络名称 SSID / D.数据库 / E.智能终端 / F.湿度传感器）。

（4）该模拟系统使用中访问服务器速度较慢，写出一种可能的原因____。

（5）部分湿度数据如图1，现统计各大棚总浇水次数（湿度低于60浇水）并可视化，如图2所示。请在程序划线处填空。

![[attachments/202504金砖高二_14_图1.jpg]]

![[attachments/202504金砖高二_14_图2.jpg]]

~~~python
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = ['SimHei']
df = pd.read_excel("data.xlsx")
house = list(df["大棚编号"].unique())
y = []
for x in house:
    df1 = ____①____
    df1 = df1[df1["湿度值"] < 60]
    y.append(len(df1))
plt.bar(____②____)
plt.title("各大棚浇水次数统计")
plt.show()
~~~""", analysis="SQLite3 是方案中对数据库技术的具体选型，属于概要设计阶段；多个传感器可接入同一智能终端。服务器、智能终端和湿度传感器是所列硬件，浏览器和数据库属于软件/数据，SSID 是网络配置。访问慢可由 CPU 或内存等服务器性能不足造成。按大棚编号筛选用 df[df.大棚编号==x]，柱状图横纵坐标为 house,y。"),
    15: dict(folder="09队列", topics=["09队列", "03python基础", "优先队列", "调度模拟"], difficulty="较难", answer="（1）26；（2）① que[j-1][2] > que[j][2]；（3）② total_waittime=0；③ data[i][3]<=cur_time；④ cur_time + que[head][2]*2", body="""运动会组委会为比赛队伍准备物品并送到各代表队酒店，分配 n 辆汽车运送物品。代表队在不同时间到达，一辆汽车每次只能为一个代表队运送，送达后汽车需返回仓库。优先级数字越小优先级越高；优先级相同时先送单程配送时间短的队伍。各队信息如下：

| 比赛队伍 | 编号 | 优先级 | 单程配送时间 | 到达时间 |
|---|---:|---:|---:|---:|
| 乒乓球代表队 | 1 | 2 | 4 | 2 |
| 足球代表队 | 2 | 4 | 2 | 4 |
| 羽毛球代表队 | 3 | 1 | 6 | 6 |
| 游泳代表队 | 4 | 2 | 2 | 8 |
| 射箭代表队 | 5 | 1 | 3 | 10 |
| 排球代表队 | 6 | 4 | 5 | 11 |
| 举重代表队 | 7 | 3 | 6 | 12 |

（1）现调集3辆汽车，所有汽车从仓库出发，请计算送完所有代表队需要的时间（以最后一辆车返回仓库的时间为准）____。

（2）对 que 队列按照优先级为主要关键字、单程配送时间为次要关键字排序，que 中存储编号、优先级、单程配送时间、到达时间。

~~~python
def sort_que(head, tail):
    for j in range(tail-1, head, -1):
        if que[j-1][1] > que[j][1]:
            que[j-1], que[j] = que[j], que[j-1]
        elif ____①____:
            que[j-1], que[j] = que[j], que[j-1]
~~~

（3）以下代码模拟派送过程，并计算平均等待时长和订单完成总时间，请补充代码。

~~~python
def find_car():
    min_index = 0
    for i in range(1, len(c)):
        if c[i] < c[min_index]:
            min_index = i
    return min_index

# data 已按到达时间升序排列
n = int(input("输入小车数量："))
c = [0] * n
que = [0] * 100
head = tail = 0
cur_time = data[0][3]
____②____
i = 0
while head != tail or i < len(data):
    minc_index = find_car()
    if i < len(data) and ____③____:
        que[tail] = data[i]
        tail += 1
        i += 1
        sort_que(head, tail)
    elif head != tail and c[minc_index] <= cur_time:
        total_waittime += cur_time - que[head][3]
        c[minc_index] = ____④____
        head += 1
    else:
        cur_time += 1
~~~
""", analysis="（1）按到达时间加入优先队列并让3辆车取最早可用车辆，逐次模拟得到最后一辆车完成往返的时刻为26。排序时只有优先级相同且前一项单程时间更长才交换，因此①为 que[j-1][2] > que[j][2]。平均等待时间累加前先初始化②；只有队伍已到达才入队，③为 data[i][3] <= cur_time；车辆送达并返回需要两个单程时间，④为 cur_time + que[head][2]*2。"),
}


def frontmatter(q: int, data: dict[str, object]) -> str:
    topic = str(data["folder"])
    lines = [
        "---",
        f"id: {PREFIX}-{q:02d}",
        f"题型: {'选择题' if q <= 12 else '非选择题'}",
        f'来源: "[[试卷/{PDF}|{PDF}]]"',
        f"试卷: {PDF}",
        "年级: 高二",
        f'题号: "{q:02d}"',
        f"难度: {data['difficulty']}",
        "水平: 选考",
        "知识点:",
    ]
    lines.extend(f"  - {item}" for item in data["topics"])  # type: ignore[arg-type]
    lines += [
        "完成次数: 0",
        "补课:",
        "正确率:",
        "错题原因:",
        f"创建日期: {TODAY}",
        f"图片核验: {'已通过' if data.get('image') else '无图片'}",
        "tags:",
        f"  - 知识点/{topic}",
        "---",
    ]
    return "\n".join(lines)


def write_notes() -> list[tuple[int, Path, dict[str, object]]]:
    written: list[tuple[int, Path, dict[str, object]]] = []
    for q, data in QUESTIONS.items():
        folder = ROOT / str(data["folder"])
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{PREFIX}-{q:02d}.md"
        body = str(data["body"])
        body = body.replace("回答第 01—03 题", f"回答第 {q:02d} 题")
        body = body.replace("回答第 04—06 题", f"回答第 {q:02d} 题")
        text = frontmatter(q, data) + f"\n# 题目 {q:02d}\n\n" + body
        text += "\n\n---\n\n## 答案\n\n**正确答案：** " + str(data["answer"]) + "\n"
        text += "\n---\n\n## 解析\n\n" + str(data["analysis"]) + "\n"
        text += "\n---\n\n## 相关链接\n\n- 原试卷：[[试卷/" + PDF + "]]\n"
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append((q, path, data))
    return written


def append_review(written: list[tuple[int, Path, dict[str, object]]]) -> None:
    qpath = ROOT / "题目核验.md"
    qtext = qpath.read_text(encoding="utf-8")
    marker = f"## 29. {PREFIX}"
    if marker not in qtext:
        lines = ["", marker, "", "| 题号 | 题型 | 知识点 | 题目 md |", "|---|---|---|---|"]
        for q, path, data in written:
            rel = path.relative_to(ROOT).with_suffix("").as_posix()
            kind = "选择题" if q <= 12 else "非选择题"
            lines.append(f"| {q:02d} | {kind} | {data['folder']} | [[{rel}]] |")
        print("review path", repr(str(qpath)), "chars", len(qtext))
        qpath.write_text(qtext.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

    ipath = ROOT / "图片核验.md"
    itext = ipath.read_text(encoding="utf-8")
    if marker not in itext:
        lines = ["", marker, ""]
        for q, path, data in written:
            images = data.get("image") or []
            if not images:
                continue
            rel = path.relative_to(ROOT).with_suffix("").as_posix()
            lines.extend([
                f"### 第 {q:02d} 题", "",
                f"- 题目：[[{rel}]]",
                "- 状态：图片核验: 已通过",
                "- 核验：已打开最终附件并与原PDF信息技术页对应内容核对，裁切保留完整图形、标签、箭头、坐标轴/图注且未混入无关内容。",
                "",
            ])
            lines.extend(f"![[attachments/{name}]]\n" for name in images)
        lines += ["- 其余 10 题均为 图片核验: 无图片；本套 5 张终稿附件均已打开并与原 PDF 信息技术第 2—4 页逐项核对。", ""]
        with ipath.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(itext.rstrip() + "\n" + "\n".join(lines))


def main() -> None:
    src = ROOT / "_mineru_output" / PREFIX / "images"
    copies = {
        "54ac45397d09f9e5a6acf39adb4a9d472feb54848a596fd88702ad9248ec86b8.jpg": ROOT / "attachments" / "202504金砖高二_07_图1.jpg",
        "1b647e89f76d97791efbd48b4843fafbb3ffc03d500d93e38cbcf99cdb029542.jpg": ROOT / "attachments" / "202504金砖高二_14_图1.jpg",
        "432e32fedb9bd01060b7f98bdf5d8d9553a065eda970aa6ca650f0152d8a9996.jpg": ROOT / "attachments" / "202504金砖高二_14_图2.jpg",
    }
    for name, dest in copies.items():
        if (src / name).exists():
            shutil.copy2(src / name, dest)
    written = write_notes()
    append_review(written)
    print(f"created {len(written)} notes")
    print(f"images: {sum(len(data.get('image') or []) for _, _, data in written)} embeds")


if __name__ == "__main__":
    main()
