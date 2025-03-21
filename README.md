# The Quiz Master - V1  

## Description  
Repository for **The Quiz Master - V1** – IITM BS Course Project.  

The Quiz Master - V1 is an interactive multi-user application designed to help users improve their exam preparation through targeted quizzes and performance tracking. The platform supports two roles: **User** and **Admin**. Users can attempt quizzes, track their scores, and monitor progress through performance insights. Admins can manage subjects, chapters, quizzes, and user data, with additional access to platform-wide performance metrics.  

This project was completed as part of the **IITM BS Course**, where I achieved a **Grade: 90 / S Grade (Top Grade)**. 

---

## 🛠️ Technologies Used  
- **Python** – Core programming language for the development stack  
- **HTML, CSS** – For building and styling the frontend  
- **Jinja2** – Template engine for dynamic HTML generation in Flask  
- **Flask** – Web framework for handling backend functionality  
- **Flask-SQLAlchemy** – ORM for streamlined database management  
- **SQLite** – Database for storing user, quiz, and performance data  
- **Matplotlib** – For generating performance charts and visual insights  

---

## 🏛️ Architecture and Features  
The application follows the standard **MVC architecture**:  
- **Model** – Built using Flask-SQLAlchemy with SQLite for relational data storage  
- **View** – Built using HTML and Jinja2 for dynamic content rendering  
- **Controller** – Implemented using Flask to handle user requests and responses  

### 🌟 **Key Features**  
✅ **User authentication** – Signup and login for users and admins  
✅ **Admin dashboard** – Manage subjects, chapters, quizzes, and users  
✅ **User dashboard** – Attempt quizzes, view scores, and track progress  
✅ **Quiz functionality** – Create, edit, and delete quizzes (admin); attempt quizzes and receive scores (user)  
✅ **Performance tracking** – Graphical insights using Matplotlib  
✅ **Search functionality** – Search for subjects, quizzes, and users  
✅ **Data relationships** – Clear relational structure between subjects, chapters, quizzes, and users  
✅ **CRUD operations** – Full create, read, update, and delete functionality for quizzes and user data  

---

## 📂 Database Schema  
1. **User Table** – Stores user details and authentication data  
2. **Subject Table** – Stores subjects with related chapter data  
3. **Chapter Table** – Links subjects to quizzes  
4. **Quiz Table** – Stores quiz metadata and links to questions and scores  
5. **Question Table** – Contains questions and answers for each quiz  
6. **Score Table** – Tracks user performance and quiz attempts  

