#include <iostream>
#include <vector>
#include <string>
#include <algorithm> 
using namespace std;

// To-do list class
class TodoList {
  private:
    vector<string> tasks; // List of tasks

  public:
    // Add a task to the to-do list
    void addTask(const string& task) {
      tasks.push_back(task);
    }

    // Remove a task from the to-do list
    void removeTask(const string& task) {
      auto it = find(tasks.begin(), tasks.end(), task);
      if (it != tasks.end()) {
        tasks.erase(it);
      }
    }

    // Display the to-do list
    void display() const {
      cout << "To-do list:" << endl;
      for (const auto& task : tasks) {
        cout << "- " << task << endl;
      }
    }
};

int main() {
  TodoList todo;

  // Add some tasks to the to-do list
  todo.addTask("Learn C++");
  todo.addTask("Finish homework");
  todo.addTask("Buy groceries");

  // Display the to-do list
  todo.display();

  // Remove a task from the to-do list
  todo.removeTask("Finish homework");

  // Display the updated to-do list
  todo.display();

  return 0;
}
// g++ -std=c++11 -o out.o TO_DO_List.cxx && ./out.os
// g++ -std=c++11 -o todo todo.cpp