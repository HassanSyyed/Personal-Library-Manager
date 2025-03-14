import streamlit as st
import json
from datetime import datetime
import pandas as pd

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'username' not in st.session_state:
    st.session_state.username = None

# File paths
BOOKS_FILE = "library_data.json"
USERS_FILE = "users.json"

# Load or create data files
def load_data():
    try:
        with open(BOOKS_FILE, 'r') as f:
            books = json.load(f)
    except FileNotFoundError:
        books = []
        save_books(books)
    
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {
            'admin': {'password': 'admin123', 'type': 'admin'},
            'user1': {'password': 'user123', 'type': 'user', 'borrowed_books': []}
        }
        save_users(users)
    
    return books, users

def save_books(books):
    with open(BOOKS_FILE, 'w') as f:
        json.dump(books, f, indent=4)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# Authentication
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        users = load_data()[1]
        if username in users and users[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.user_type = users[username]['type']
            st.session_state.username = username
            st.sidebar.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials")

# Admin Functions
def add_book():
    st.subheader("Add New Book")
    title = st.text_input("Title")
    author = st.text_input("Author")
    isbn = st.text_input("ISBN")
    quantity = st.number_input("Quantity", min_value=1, value=1)
    
    if st.button("Add Book"):
        books = load_data()[0]
        new_book = {
            "title": title,
            "author": author,
            "isbn": isbn,
            "quantity": quantity,
            "available": quantity,
            "added_date": datetime.now().strftime("%Y-%m-%d")
        }
        books.append(new_book)
        save_books(books)
        st.success(f"Book '{title}' added successfully!")

def view_inventory():
    st.subheader("Library Inventory")
    books = load_data()[0]
    if books:
        df = pd.DataFrame(books)
        st.dataframe(df)
    else:
        st.info("No books in inventory")

def manage_users():
    st.subheader("User Management")
    users = load_data()[1]
    
    # Add new user
    with st.expander("Add New User"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        user_type = st.selectbox("User Type", ["user", "admin"])
        
        if st.button("Add User"):
            if new_username not in users:
                users[new_username] = {
                    "password": new_password,
                    "type": user_type,
                    "borrowed_books": []
                }
                save_users(users)
                st.success(f"User '{new_username}' added successfully!")
            else:
                st.error("Username already exists!")
    
    # View users
    st.subheader("User List")
    user_data = []
    for username, data in users.items():
        user_data.append({
            "Username": username,
            "Type": data["type"],
            "Borrowed Books": len(data.get("borrowed_books", []))
        })
    st.dataframe(pd.DataFrame(user_data))

def remove_book():
    st.subheader("Remove Book")
    books = load_data()[0]
    if books:
        book_titles = [book['title'] for book in books]
        book_to_remove = st.selectbox("Select book to remove", book_titles)
        if st.button("Remove Book"):
            books = [book for book in books if book['title'] != book_to_remove]
            save_books(books)
            st.success(f"Book '{book_to_remove}' removed successfully!")
            st.rerun()
    else:
        st.info("No books in inventory to remove")

# User Functions
def search_books():
    st.subheader("Search Books")
    search_term = st.text_input("Enter book title or author")
    books = load_data()[0]
    
    if search_term:
        results = [book for book in books if 
                  search_term.lower() in book['title'].lower() or 
                  search_term.lower() in book['author'].lower()]
        if results:
            st.dataframe(pd.DataFrame(results))
        else:
            st.info("No books found matching your search.")

def borrow_return_books():
    st.subheader("Borrow/Return Books")
    books, users = load_data()
    user = users[st.session_state.username]
    
    # Show borrowed books
    st.write("Your Borrowed Books:")
    borrowed_books = user.get("borrowed_books", [])
    if borrowed_books:
        borrowed_df = pd.DataFrame(borrowed_books)
        st.dataframe(borrowed_df)
        
        # Return books
        book_to_return = st.selectbox("Select book to return", 
                                    [book['title'] for book in borrowed_books])
        if st.button("Return Book"):
            # Update user's borrowed books
            user['borrowed_books'] = [book for book in borrowed_books 
                                    if book['title'] != book_to_return]
            # Update book availability
            for book in books:
                if book['title'] == book_to_return:
                    book['available'] += 1
            
            save_books(books)
            save_users(users)
            st.success(f"Book '{book_to_return}' returned successfully!")
            st.rerun()
    else:
        st.info("You haven't borrowed any books.")
    
    # Borrow books
    st.write("Available Books:")
    available_books = [book for book in books if book['available'] > 0]
    if available_books:
        book_to_borrow = st.selectbox("Select book to borrow",
                                    [book['title'] for book in available_books])
        if st.button("Borrow Book"):
            for book in books:
                if book['title'] == book_to_borrow and book['available'] > 0:
                    book['available'] -= 1
                    borrowed_book = {
                        'title': book['title'],
                        'author': book['author'],
                        'borrow_date': datetime.now().strftime("%Y-%m-%d")
                    }
                    if 'borrowed_books' not in user:
                        user['borrowed_books'] = []
                    user['borrowed_books'].append(borrowed_book)
                    
                    save_books(books)
                    save_users(users)
                    st.success(f"Book '{book_to_borrow}' borrowed successfully!")
                    st.rerun()
                    break

def display_statistics():
    st.subheader("Library Statistics")
    books, users = load_data()
    
    # Books Statistics
    st.write("📚 Books Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Books", len(books))
    
    total_quantity = sum(book['quantity'] for book in books)
    with col2:
        st.metric("Total Copies", total_quantity)
    
    available_copies = sum(book['available'] for book in books)
    with col3:
        st.metric("Available Copies", available_copies)
    
    # Genre Statistics if books exist
    if books:
        st.write("📊 Books by Author")
        author_counts = {}
        for book in books:
            author = book['author']
            author_counts[author] = author_counts.get(author, 0) + 1
        
        author_df = pd.DataFrame(list(author_counts.items()), 
                               columns=['Author', 'Number of Books'])
        st.bar_chart(author_df.set_index('Author'))
    
    # User Statistics
    st.write("👥 User Statistics")
    col1, col2 = st.columns(2)
    
    total_users = len([u for u in users.values() if u['type'] == 'user'])
    with col1:
        st.metric("Total Users", total_users)
    
    total_borrowed = sum(len(u.get('borrowed_books', [])) 
                        for u in users.values())
    with col2:
        st.metric("Total Borrowed Books", total_borrowed)
    
    # Most Active Users
    st.write("📈 Most Active Users")
    user_activity = []
    for username, data in users.items():
        if data['type'] == 'user':  # Only show regular users
            borrowed_count = len(data.get('borrowed_books', []))
            user_activity.append({
                'Username': username,
                'Books Borrowed': borrowed_count
            })
    
    if user_activity:
        activity_df = pd.DataFrame(user_activity)
        activity_df = activity_df.sort_values('Books Borrowed', ascending=False)
        st.dataframe(activity_df)

# Main App
st.title("📚 Library Management System")

# Sidebar navigation
if not st.session_state.authenticated:
    login()
else:
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_type = None
        st.session_state.username = None
        st.rerun()
    
    # Admin Panel
    if st.session_state.user_type == "admin":
        st.sidebar.title("Admin Panel")
        option = st.sidebar.selectbox("Choose operation",
                                    ["Add Book", "Remove Book", "Search Books", 
                                     "View Inventory", "Statistics", "Manage Users"])
        
        if option == "Add Book":
            add_book()
        elif option == "Remove Book":
            remove_book()
        elif option == "Search Books":
            search_books()
        elif option == "View Inventory":
            view_inventory()
        elif option == "Statistics":
            display_statistics()
        elif option == "Manage Users":
            manage_users()
    
    # User Panel
    elif st.session_state.user_type == "user":
        st.sidebar.title("User Panel")
        option = st.sidebar.selectbox("Choose operation",
                                    ["Search Books", "Borrow/Return Books"])
        
        if option == "Search Books":
            search_books()
        elif option == "Borrow/Return Books":
            borrow_return_books() 