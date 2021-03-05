import tkinter as tk
from tkinter import messagebox

import time
import threading
import queue

############################################################################

class Node:
    def __init__(self, val, left, path):
        self.val = val
        self.left = left
        self.path = path

        self.totalused = 0
        self.need = left.copy()
        for r in self.need:
            self.need[r] = resistors[r] - self.need[r]
            self.totalused += self.need[r]

    def fromVal(val, resistors):
        left = resistors.copy()
        left[val] -= 1
        path = str(val)
        return Node(val, left, path)

    def fromNode(lastNode, newNode, t):
        val = 0
        if t == "+":
            val = lastNode.val + newNode.val
        else:
            val = lastNode.val * newNode.val / (lastNode.val + newNode.val)
        
        left = lastNode.left.copy()
        for r in left:
            left[r] -= newNode.need[r]
        
        path = "({} {} {})".format(lastNode.path, t, newNode.path)
        return Node(val, left, path)

############################################################################

resistors = None
results = []

epsVar = None
targetVar = None
lb = None
statusLbl = None
m = None
resistorFrame = None

valueList = []
amountList = []

queue = queue.Queue()

############################################################################

class ThreadedClient(threading.Thread):
    def __init__(self, queue, fcn):
        threading.Thread.__init__(self)
        self.queue = queue
        self.fcn = fcn
    def run(self):
        time.sleep(1)
        self.queue.put(self.fcn())

def spawnthread(fcn):
    thread = ThreadedClient(queue, fcn)
    thread.start()
    periodiccall(thread)

def periodiccall(thread):
    if(thread.is_alive()):
        m.after(100, lambda: periodiccall(thread))

############################################################################


############################################################################
def generateOptions():
    global results
    global resistors

    resistors = {}

    for i in range(len(valueList)):
        val = valueList[i].get()
        amount = amountList[i].get()

        if val == 0 or amount == 0:
            messagebox.showerror("Error", "Resistor property is 0")
            return

        resistors[val] = amount

    target = targetVar.get()
    eps = epsVar.get()

    nodes = [Node.fromVal(i, resistors) for i in resistors]
    queue = [i for i in range(len(nodes))]

    lb.delete(0, tk.END)
    statusLbl.config(text="Calculations started")
    
    results = []

    while len(queue) != 0:
        
        now_idx = queue.pop(0)

        if now_idx % 100 == 0:
            statusLbl.config(text="Calculations started. Analysed {} configurations".format(str(now_idx)))

        now = nodes[now_idx]

        for idx in range(now_idx+1):
            add_node = nodes[idx]

            possible = True
            for r in add_node.need:
                if add_node.need[r] > now.left[r]:
                    possible = False
                    break

            if not possible:
                continue
            
            for way in ["+", "||"]:

                newNode = Node.fromNode(now, add_node, way)
                nodes.append(newNode)

                queue.append(len(nodes)-1)

                if abs(newNode.val - target) <= eps:
                    results.append({
                        "val": round(newNode.val),
                        "path": newNode.path[1: len(newNode.path)-1]
                    })

                    lb.insert(tk.END, "{:<8}    x{:<2}        {}\n".format(
                        str(round(newNode.val)) + " Ω", 
                        newNode.totalused,
                        newNode.path[1: len(newNode.path)-1])
                    )

                    if len(results) >= 10:
                        statusLbl.config(text="Calculated 10 results. Analysed {} configurations".format(len(nodes)))

                        # SORT RESULTS

                        return
    
    statusLbl.config(text="Calculations done. Analysed {} configurations".format(len(nodes)))

############################################################################


############################################################################

def addLine(val=0, amount=0):
    valueList.append(tk.IntVar())
    valueList[ len(valueList) -1 ].set(val)
    amountList.append(tk.IntVar())
    amountList[ len(amountList) -1 ].set(amount)

    tk.Entry(resistorFrame, textvariable=valueList[ len(valueList) -1 ], justify="right").grid(row=len(valueList), column=0)
    tk.Label(resistorFrame, text=" Ω x ").grid(row=len(valueList), column=1)
    tk.Entry(resistorFrame, textvariable=amountList[ len(amountList) -1 ]).grid(row=len(amountList), column=2)

def loadResistorList():
    try:
        f = open("resistors.txt")
    except:
        f = open("resistors.txt", "w")
        f.write("220 2\n1000 2\n10000 2")
        f.close()
        f = open("resistors.txt")
        return

    lines = f.readlines()

    if len(lines) == 0:
        addLine(220, 2)
        addLine(1000, 2)
        addLine(10000, 2)
    else:
        for l in lines:
            words = l.split(" ")
            addLine(int(words[0]), int(words[1]))

############################################################################


############################################################################

def showGUI():
    global epsVar, targetVar
    global lb
    global m
    global statusLbl
    global resistorFrame

    m = tk.Tk()
    m.title("Resistor calculator")
    m.geometry("500x500")

    m.option_add("*Font", ("Segoe UI", 10))

    ########################################################################
    tk.Label(m, text="OWNED RESISTORS", font=("Segoe UI", 20)).pack()
    resistorFrame = tk.Frame()
    resistorFrame.pack()
    tk.Button(m, text="Add new resistor", font=("Segoe UI", 10), command=addLine).pack()
    ########################################################################


    ########################################################################
    tk.Label(m, text="CALCULATION VALUES", font=("Segoe UI", 20)).pack()

    f = tk.Frame()
    targetVar = tk.IntVar()
    tk.Label(f, text="Target").grid(row=0, column=0)
    tk.Entry(f, textvariable=targetVar).grid(row=1, column=0)
    targetVar.set(440)

    epsVar = tk.IntVar()
    tk.Label(f, text="Maximum error").grid(row=0, column=1)
    tk.Entry(f, textvariable=epsVar).grid(row=1, column=1)
    epsVar.set(10)
    
    f.pack()
    tk.Button(m, text="Calculate", command=lambda: spawnthread(generateOptions)).pack()
    ########################################################################

    ########################################################################
    f = tk.Frame(m)
    
    scrollbar = tk.Scrollbar(f)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    lb = tk.Listbox(f, yscrollcommand=scrollbar.set)
    lb.insert(tk.END, "Press \"Calculate\"")
    lb.pack(fill=tk.BOTH)

    scrollbar.config(command = lb.yview)

    f.pack(fill=tk.BOTH)
    ########################################################################

    statusLbl = tk.Label(m, text="Calculations not started")
    statusLbl.pack()

    loadResistorList()
    m.mainloop()

############################################################################


showGUI()