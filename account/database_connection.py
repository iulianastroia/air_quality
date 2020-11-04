# -*- coding: utf-8 -*-
import mysql.connector


def db_connect():
    try:
        # my_db = mysql.connector.connect(host='37.156.181.224', user='hartapol_admin', password='Parolamea1234',
        my_db = mysql.connector.connect(host='hartapoluarebrasov.ro', user='hartapol_admin', password='Parolamea1234',
                                        database='hartapol_account')
        my_cursor = my_db.cursor(buffered=True)
        return my_cursor, my_db
    except mysql.connector.Error as err:
        print("Something went wrong with the connection to the database: {}".format(err))


def register_user_db(username_value, password_value, email_value):
    insert_query = "insert into register_table(username,email,password) values(%s,%s,%s)"
    val = (username_value, email_value, password_value)
    mycursor, mydb = db_connect()
    mycursor.execute(insert_query, val)
    mydb.commit()
    print(mycursor.rowcount, "record inserted in user table.")
    close_connection(mycursor, mydb)


def close_connection(mycursor, mydb):
    mycursor.close()
    mydb.close()


def check_login(username, password):
    mycursor, mydb = db_connect()
    mycursor.execute('SELECT * FROM register_table WHERE username = %s AND password = %s', (username, password))
    result = mycursor.fetchall()
    if not result:
        print("user and pass DON'T MATCH")
        close_connection(mycursor, mydb)
        return False
    else:
        print("User and pass match in database: ", result)
        close_connection(mycursor, mydb)
        return True


def edit_user(username):
    mycursor, mydb = db_connect()
    mycursor.execute("SELECT * FROM register_table WHERE username ='" + str(username) + "'")

    result = mycursor.fetchall()
    for db_value in result:
        username = db_value[1]
        email = db_value[2]
        password = db_value[3]
        print("user", username)
        print("email", email)

        print("pass", password)
        close_connection(mycursor, mydb)
    return email, password


def update_values(current_username, email_value, password_value):
    update_query = "update register_table set email=%s,password=%s where username=%s"
    val = (email_value, password_value, current_username)
    mycursor, mydb = db_connect()
    mycursor.execute(update_query, val)
    mydb.commit()
    print(mycursor.rowcount, "record updated in user table.")
    close_connection(mycursor, mydb)
