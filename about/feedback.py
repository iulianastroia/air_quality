import smtplib  # mail protocol
from validate_email import validate_email
import os


def check_email(sender_email):
    is_email_valid = validate_email(sender_email)
    print('is MAIL VALID? ', is_email_valid)

    if is_email_valid:
        print("valid e-mail")
    else:
        print("please enter a valid e-mail address")
    return is_email_valid


def send_email(sender_email, sender_name, sender_feedback, sender_phone):
    try:
        print("send e-mail to developer")
        print("email is: ", sender_email)
        print("name is: ", sender_name)
        print("feedback message is: ", sender_feedback)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # encrypt connection
        # environment variables->used to hide sender's e-mail and password
        #todo let os.environ.get
        # app_email = os.environ.get("SENDER_EMAIL")
        app_email = "air.pollution.brasov@gmail.com"
        #todo let os.environ.get
        # app_password = os.environ.get("SENDER_PASSWORD")
        app_password ="lvmddgrboatxwbrg"
        server.login(app_email, app_password)

        subject = f"New feedback from: {sender_name}"
        msg = sender_feedback

        msg = f"Subject: {subject} \n\n Sender's feedback: {msg} \n\n Sender's e-mail: {sender_email} \n \n Sender's phone number: {sender_phone}"

        is_email_valid = check_email(sender_email)

        if ((not sender_name and not sender_email and not sender_feedback) or (
                not sender_email and not sender_feedback) or (not sender_email and not sender_name) or (
                not sender_name and not sender_feedback)):
            print('please fill the empty fields')
            return 'please fill the empty fields'


        elif not sender_feedback:  # check if empty feedback message
            print("Please enter a feedback message.")
            return "Please enter a feedback message."
        elif not sender_email:
            print("Please enter your e-mail.")
            return "Please enter your e-mail."
        elif not sender_name:
            print("Please enter your name.")
            return "Please enter your name."

        else:
            if is_email_valid:
                print("Thank you for your message. We will get back to you shortly.")
                server.sendmail(
                    # from,to,message
                    'air.pollution.brasov@gmail.com',
                    'iuliana.stroia97@gmail.com',
                    msg
                )
                print("E-MAIL HAS BEEN SENT!")
                return "Thank you for your message. We will get back to you shortly."
            else:
                return "Please enter a valid e-mail."
        server.quit()

    except Exception as e:
        print(e)
        print('Problem with feedback_popup(e-mail)')


pass
