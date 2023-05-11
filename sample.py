import simpy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from time import strftime
from tkinter import *
from tkinter.font import BOLD, Font
from tkinter import *
from PIL import Image

root = Tk()
root.geometry('1000x800')
root.title("Factory System Discrete Event Simulation")

N = 50
R = 3
S = 20
R_COST = 3.75
S_COST = 30
H = 8
COST = 0.0
MIN_FAIL_TIME = 132
MAX_FAIL_TIME = 182
MIN_REPAIR_TIME = 4
MAX_REPAIR_TIME = 10
OBSERVE_TIME = []
OBSERVE_COST = []
OBSERVE_SPARES = []
ROW = 6
NOW = datetime.now()
SEED = np.random.randint(1,100)

np.random.seed(SEED)

def generate_time_to_failure():
    global MIN_FAIL_TIME
    global MAX_FAIL_TIME
    return np.random.uniform(MIN_FAIL_TIME,MAX_FAIL_TIME)

def generate_repair_time():
    global MIN_REPAIR_TIME
    global MAX_REPAIR_TIME
    return np.random.uniform(MIN_REPAIR_TIME,MAX_REPAIR_TIME)

def update_NOW(env):
    global NOW

    while True:
        yield env.timeout(8*5)
        NOW = NOW + timedelta(days = 2)

def observe(env, spares):
    global COST
    global OBSERVE_COST
    global OBSERVE_SPARES
    global OBSERVE_TIME

    while True:
        OBSERVE_COST.append(COST)
        OBSERVE_SPARES.append(spares.level)
        OBSERVE_TIME.append(env.now)
        yield env.timeout(1)

def repair_machine(env, name, repairers):
    global ROW
    global NOW

    with repairers.request() as req:
        yield req
        yield env.timeout(generate_repair_time())
        yield spares.put(1)
    print(f"{(NOW + timedelta(hours = env.now)).strftime('%H:%M:%S')} {name} repaired on day {(NOW + timedelta(hours = env.now)).date()}.")

def operate_machine(env, name, repairers, spares):
    global ROW
    global NOW
    global COST

    name = 'Machine ' + str(name)

    while True:
        yield env.timeout(generate_time_to_failure())
        t_broken = env.now
        print(f"{(NOW + timedelta(hours = t_broken)).strftime('%H:%M:%S')} {name} broke on day {(NOW + timedelta(hours = env.now)).date()}.")

        env.process(repair_machine(env, name, repairers))
        flag = 0
        if(spares.level > 0):
            flag = 1
            yield spares.get(1)
        t_replaced = env.now
        print(f"{(NOW + timedelta(hours = t_replaced)).strftime('%H:%M:%S')} {name} replaced on day {(NOW + timedelta(hours = env.now)).date()}.")
        COST = COST + 20*(t_replaced - t_broken)


def factory_run(env, repairers, spares):
    global N
    global COST
    global R_COST
    global S_COST

    for i in range(N):
        env.process(operate_machine(env, i, repairers, spares))

    while True:
        COST = COST + R_COST*H*repairers.capacity + S_COST*spares.capacity
        yield env.timeout(H)

def graph():
    global ROW
    global canvas

    fig, ax = plt.subplots(figsize=(8,6))
    canvas = FigureCanvasTkAgg(fig, master = root) 
    canvas.get_tk_widget().grid(row=ROW, column=0, columnspan=2)
    ROW = ROW + 1

    ax.step(OBSERVE_TIME, OBSERVE_COST, where = "post")
    ax.set_xlabel("Time(Hours)")
    ax.set_ylabel("Cost(USD)")
    ax.set_title("Cost v/s Time", fontweight = "bold")
    ax.grid(True)
    canvas.draw()

def submit():
    global ROW
    global disp
    global env
    global repairers
    global spares

    N = int(machines_entry.get())
    R = int(repairers_entry.get())
    S = int(spares_entry.get())
    R_COST = float(repairers_rate_entry.get())
    S_COST = float(spares_rate_entry.get())

    env = simpy.Environment()
    repairers = simpy.Resource(env, capacity = R)
    spares = simpy.Container(env, init = S, capacity = S)
    env.process(factory_run(env, repairers, spares))
    env.process(observe(env, spares))
    env.process(update_NOW(env))
    env.run(until = 8*5*52) 

    graph()
    print(f"Total Cost Encountered By the Company is: ${COST}")
    disp = Label(root, text = f"Total Cost Encountered By the Company is: ${COST}", font = Font(size=22, weight=BOLD))
    disp.grid(row=ROW, column=0, columnspan=2)
    ROW = ROW + 1
    root.update()

def Reset():
    global disp
    global canvas
    global OBSERVE_TIME
    global OBSERVE_SPARES
    global OBSERVE_COST

    OBSERVE_TIME.clear()
    OBSERVE_SPARES.clear()
    OBSERVE_COST.clear()
    disp.grid_forget()
    canvas.get_tk_widget().grid_forget()

Label1 = Label(root, text = "Number Of Machines: ")
machines_entry = Entry(root)
machines_entry.insert(0,"50")
Label2 = Label(root, text = "Number Of Repairers: ")
repairers_entry = Entry(root)
repairers_entry.insert(0,"3")
Label3 = Label(root, text = "Number Of Spare Machines: ")
spares_entry = Entry(root)
spares_entry.insert(0,"20")
Label4 = Label(root, text = "Repairers Labour Per Hour: ")
repairers_rate_entry = Entry(root)
repairers_rate_entry.insert(0,"3.75")
Label5 = Label(root, text = "Machine Cost Per Hour: ")
spares_rate_entry = Entry(root)
spares_rate_entry.insert(0,"20")

submit_btn = Button(root, text = "Submit", command = submit)
reset_btn = Button(root, text = "Reset", command = Reset, padx = 15)

Label1.grid(row=0, column=0)
machines_entry.grid(row=0, column=1)
Label2.grid(row=1, column=0)
repairers_entry.grid(row=1, column=1)
Label3.grid(row=2, column=0)
spares_entry.grid(row=2, column=1)
Label4.grid(row=3, column=0)
repairers_rate_entry.grid(row=3, column=1)
Label5.grid(row=4, column=0)
spares_rate_entry.grid(row=4, column=1)
submit_btn.grid(row=5, column=0)
reset_btn.grid(row=5, column=1)

root.mainloop()