#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <thread>
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
      while (true) {
        cout << "To-do list:" << endl;
        for (const auto& task : tasks) {
          cout << "- " << task << endl;
        }

        // Sleep for 5 seconds before displaying the list again
        this_thread::sleep_for(chrono::seconds(5));
      }
    }

    // User interface for adding and removing tasks from the to-do list
    void run() {
      while (true) {
        // Display the main menu
        cout << "To-do list:" << endl;
        cout << "1. Add a task" << endl;
        cout << "2. Remove a task" << endl;
        cout << "3. Quit" << endl;

        int choice;
        cout << "Enter your choice: ";
        cin >> choice;

        if (choice == 1) {
          // Add a task
          string task;
          cout << "Enter a task: ";
          cin.ignore(); // Ignore the newline character from the previous input
          getline(cin, task);
          addTask(task);
        } else if (choice == 2) {
          // Remove a task
          string task;
          cout << "Enter a task: ";
          cin.ignore(); // Ignore the newline character from the previous input
          getline(cin, task);
          removeTask(task);
        } else if (choice == 3) {
          // Quit the program
          break;
        } else {
          // Invalid choice
          cout << "Invalid choice. Please try again." << endl;
        }
      }
    }
};

int main() {
  TodoList todo;

  // Create a thread to run the user interface for adding and removing tasks
  thread uiThread(&TodoList::run, &todo);

  // Create a thread to display the current status of the to-do list
  thread displayThread(&TodoList::display, &todo);

  // Wait for the threads to finish
  uiThread.join();
  displayThread.join();

  return 0;
}
// g++ -std=c++11 -o out.o TO_DO_List_Updates.cxx && ./out.o