import time
import datetime
import pickle
import os
class ToDoList:
    def __init__(self, TDL):
        self.to_do_list = []
        self.TimeStampedTDL = TDL

    def add_to_list(self, item):
        # print(datetime.datetime.now())
        # print(time.time())
        v_time = time.time()
        self.to_do_list.append(item)
        print("Task added to To Do List")
        
        self.TimeStampedTDL.add_to_list(item, "add")
    def remove_from_list(self, item):
        v_time = time.time()
        if item in self.to_do_list  :
            self.to_do_list.remove(item) 
            print("Task removed from To Do List")
            self.TimeStampedTDL.add_to_list(item, "rmv")
        else :
            print("Such task is not in To Do List")

    def view_list(self):
        print("Here are the tasks in your To Do List:")
        for item in self.to_do_list:
            print(f"  *{item}*")
        print(f"  Total tasks : {len(self.to_do_list)}")

class TimeStampedToDoList(ToDoList):
    def __init__(self):
        self.to_do_list = []
    def add_to_list(self, item, mode):
        
        self.to_do_list.append( (item,datetime.datetime.now(),mode) )
        # print("Item added to To Do List")

    
    def view_list_with_timestamps(self):
        print("Here are the tasks in your To Do List:")
        for item, timestamp, mode in self.to_do_list:
            if mode == "add":
                print(f"  Task {item} was added on - {timestamp.strftime('%a %d-%b %Y %H:%M')}")
                # print(f"  {timestamp")
            elif mode == "rmv":
                print(f"  Task {item} was comleted on - {timestamp.day}")



time_stampedTDL = TimeStampedToDoList()

to_do_list = ToDoList(time_stampedTDL)
if os.path.exists('history.pickle'):
    with open('history.pickle', 'rb') as f:
        time_stampedTDL.to_do_list = pickle.load(f)
if os.path.exists('current.pickle'):
    with open('current.pickle', 'rb') as f:
        to_do_list.to_do_list = pickle.load(f)

while True:
    action = input("What would you like to do? (add/remove/view/history/save/quit) ")

    if action == "add" or action == "a" or action == "1":
        item = input("What task would you like to add to the To Do List? ")
        to_do_list.add_to_list(item)

    elif action == "remove" or action == "r" or action == "2":
        item = input("What task would you like to remove from the To Do List? ")
        
        to_do_list.remove_from_list(item)
    elif action == "history" or action == "h" or action == "5":
        
        time_stampedTDL.view_list_with_timestamps()
    elif action == "view" or action == "v" or action == "3":
        to_do_list.view_list()
    elif action == "save" or action == "s" or action == "6":
        print("Saving current tasks and history to binary")
        with open('current.pickle', 'wb') as f:
            pickle.dump(to_do_list.to_do_list, f)
        with open('history.pickle', 'wb') as f:
            pickle.dump(time_stampedTDL.to_do_list, f)
    elif action == "quit" or action == "q" or action == "4":
        break

    else:
        print("Invalid input. Please try again.")