
import streamlit as st
import psycopg2
from configparser import ConfigParser
import pandas as pd
import hashlib
import re
import uuid
import base64
import matplotlib.pyplot as plt
import numpy as np

st.sidebar.title("Welcome to HRD Survey Interface!")

#option = st.sidebar.selectbox("Select user",
#                              ("HRD Admin", "HRD guy"))

radio_list = ["HRD Admin", "HRD guy","Potential candidate"]
app_state = st.experimental_get_query_params()
default_radio = int(app_state["unique_option"][0]) if "unique_option" in app_state else 0
unique_option = st.sidebar.radio("Select user?", radio_list, index = default_radio)
if unique_option:
    st.experimental_set_query_params(unique_option=radio_list.index(unique_option))


def get_config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    return {k: v for k, v in parser.items(section)}

def uuid_url64():
    """Returns a unique, 16 byte, URL safe ID by combining UUID and Base64
    """
    rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    return re.sub(r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)


#-------------HRD Admin------------

if unique_option == "HRD Admin":

    db_info = get_config()
    # Open a cursor to perform database operations
    conn = psycopg2.connect(**db_info)
    cursor = conn.cursor()

    st.subheader("HRD Admin interface")

    # Login
    username = st.sidebar.text_input(label='Please enter your Username:')
    pwd = st.sidebar.text_input(label='Please enter your password',type='password')
    submit_button = st.sidebar.checkbox('Login')
    true_username = 'admin123'
    true_pwd = 'admin123'

    if(submit_button):
        if username == "":
            st.info('Please enter your Username')
        if pwd == "":
            st.info('Please enter your Password')
        else:
            if username == true_username and pwd == true_pwd:
                st.success(f"Welcome, HRD Admin!")

                # Adding a new hr guy in database
                with st.expander("Add new HR guy"):

                    with st.form(key='HR_guys'):
                        # Input
                        first_name = st.text_input(label='First name')
                        last_name = st.text_input(label='Last name')
                        company = st.text_input(label='Company name')
                        email_address = st.text_input(label='Email address')
                        quota = st.slider("Quota: ", 0, 15, 5, key=int)
                        user_name = st.text_input(label='User name')
                        password = st.text_input(label='Password')
                        p_hashed = hashlib.sha256(password.encode()).hexdigest()
                        submit_button = st.form_submit_button(label='Submit')
                        if(submit_button):
                            if first_name == "" or last_name == "" or company == "" or email_address == "" or quota == "" or user_name == "" or password == "":
                                st.warning("Please provide full information.")
                            else:
                                # Check if user_name is already in database
                                cursor.execute(""" SELECT * from hr_guy WHERE user_name = '%s' """ % (user_name))
                                exist = cursor.fetchone()
                                if exist is None:
                                    cursor.execute("""INSERT INTO hr_guy (first_name, last_name, company, email_address, quota_left, user_name, password)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s) returning *""", (first_name, last_name, company, email_address, quota, user_name, p_hashed))
                                    result=cursor.fetchall()
                                    st.success(f"New HR guy {user_name} is added")
                                else:
                                    st.error("HR guy with this User name already exists. Try another one.")

                # Show Database table
                cursor.execute("""SELECT * from hr_guy""")
                result1=cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                df1 = pd.DataFrame(data=result1, columns=column_names)
                st.dataframe(df1)

                # Admit or deny quota
                with st.expander("Info about requested quota"):
                    cursor.execute("""SELECT first_name, last_name, user_name, requested_quota FROM hr_guy WHERE requested_quota != 0""")
                    result2=cursor.fetchone()
                    if result2 is None:
                        st.info('No requested quota.')
                    else:
                        cursor.execute("""SELECT first_name, last_name, user_name, requested_quota FROM hr_guy WHERE requested_quota != 0""")
                        result2=cursor.fetchall()
                        column_names = [desc[0] for desc in cursor.description]
                        df2 = pd.DataFrame(data=result2, columns=column_names)
                        st.dataframe(df2)
                        with st.form(key='quota'):
                            user_name = st.text_input(label='Grant quota for (type User name): ')
                            submit_button = st.form_submit_button(label='Submit')
                            if(submit_button):
                                cursor.execute(""" SELECT * from hr_guy WHERE user_name = '%s' AND requested_quota != 0 """ % (user_name))
                                result3 = cursor.fetchone()
                                if result3 is None:
                                    st.warning('User name is wrong or this user did not request any quota.')
                                else:
                                    cursor.execute("""UPDATE hr_guy SET quota_left = (quota_left+requested_quota) WHERE user_name = '%s'""" % (user_name))
                                    cursor.execute("""UPDATE hr_guy SET requested_quota = '0' WHERE user_name = '%s'""" % (user_name))
                                    st.success(f"You granted quota for {user_name}!")
                        with st.form(key='no_quota'):
                            user_name = st.text_input(label='Deny quota for (type User name): ')
                            submit_button = st.form_submit_button(label='Submit')
                            if(submit_button):
                                cursor.execute(""" SELECT * from hr_guy WHERE user_name = '%s' AND requested_quota != 0 """ % (user_name))
                                result4 = cursor.fetchone()
                                if result4 is None:
                                    st.warning('User name is wrong or this user did not request any quota.')
                                else:
                                    cursor.execute("""UPDATE hr_guy SET requested_quota = '0' WHERE user_name = '%s'""" % (user_name))
                                    st.success(f"You denied quota for {user_name}!")


            else:
                st.error("Wrong Username or Password. Try again.")


    # Close a cursor
    conn.commit()
    conn.close()

    #-------------HR Guy------------

if unique_option == "HRD guy":

    db_info = get_config()
    # Open a cursor to perform database operations
    conn = psycopg2.connect(**db_info)
    cursor = conn.cursor()

    st.subheader("HRD Guy interface")


    # Login
    username=st.sidebar.text_input(label='Please enter your Username:')
    pwd=st.sidebar.text_input(label='Please enter your password',type='password')
    submit_button = st.sidebar.checkbox('Login')

    if(submit_button):
        if username =="":
            st.info('Please enter your Username')
        if pwd =="":
            st.info('Please enter your Password')
        else:
            p_hashed = hashlib.sha256(pwd.encode()).hexdigest()
            cursor.execute("""SELECT * from hr_guy WHERE user_name = '%s' AND password = '%s'""" % (username, p_hashed))
            exist = cursor.fetchone()
            if exist is None:
                st.error("Wrong Username or Password. Try again.")
            else:
                st.success(f"Welcome, {username}!")

                # Show left quota and sent invitations
                cursor.execute("""SELECT first_name, last_name, company, email_address, quota_left, invitations_sent, requested_quota from hr_guy WHERE user_name = '%s'""" % (username))
                result1=cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                df1 = pd.DataFrame(data=result1, columns=column_names)
                st.dataframe(df1)

                # Send a new invitation
                with st.expander("Send a new invitation"):
                    with st.form(key='potential_candidate'):
                        id = st.text_input(label='Set an identification number')
                        first_name = st.text_input(label='First name')
                        last_name = st.text_input(label='Last name')
                        email_address = st.text_input(label='Email address')
                        team_name = st.text_input(label='Team name')
                        submit_button = st.form_submit_button(label='Submit')
                        if(submit_button):
                            #Check if hr guy has quota to send an invitation
                            cursor.execute("""SELECT quota_left FROM hr_guy WHERE user_name = '%s' AND quota_left IN (0)""" % (username))
                            is_quota = cursor.fetchone()
                            if is_quota is None:
                                # Check if an invitation has been already sent to the potential candidate
                                cursor.execute(""" SELECT * from potential_candidate WHERE id = '%s' OR email_address = '%s' """ % (id, email_address))
                                exist = cursor.fetchone()
                                if exist is None:
                                    cursor.execute("""INSERT INTO potential_candidate (id, first_name, last_name, email_address, team_name, hr_guy)
                                            VALUES (%s, %s, %s, %s, %s, %s) returning *""", (id, first_name, last_name, email_address, team_name, username))
                                    result=cursor.fetchall()
                                    cursor.execute("""UPDATE hr_guy SET quota_left = (quota_left-1::numeric) WHERE user_name = '%s'""" % (username))
                                    cursor.execute("""UPDATE hr_guy SET invitations_sent = (invitations_sent+1::numeric) WHERE user_name = '%s'""" % (username))
                                    st.success(f"The invitation for {first_name} {last_name} is sent")
                                    # Email preview
                                    with st.container():
                                        cursor.execute(""" SELECT email_address FROM hr_guy WHERE user_name = '%s' """ % (username))
                                        result=cursor.fetchall()
                                        st.markdown("____")
                                        st.subheader("Email preview:")
                                        st.write(f"**FROM**: {result[0][0]}")
                                        st.write(f"**TO**: {email_address}")
                                        st.write("**SUBJECT**: Invitation to survey")
                                        st.write(f""" Dear {first_name} {last_name},""")
                                        your_link = "hrdsurvey.com/"+uuid_url64()
                                        cursor.execute(""" SELECT company FROM hr_guy WHERE user_name = '%s' """ % (username))
                                        result1 = cursor.fetchall()
                                        st.write(f"""I am happy to inform you that you are invited to submit survey to proceed with the selection process in our company '{result1[0][0]}'. Follow the link: [{your_link}](http://localhost:8501/?unique_option=2) to fill out the survey. Your identification number is **{id}**, please use it to enter the survey system.""" )
                                else:
                                    st.error("User with this id number exists or you have sent the invitation on this email address.")
                            else:
                                st.error("There is no quota left. Please request more qouta to send invitations.")

                #Request quota
                with st.expander("Request more quota"):
                    with st.form(key='requested_quota'):
                        quota = st.slider("Quota: ", 0, 15, 5, key=int)
                        submit_button = st.form_submit_button(label='Submit')
                        if(submit_button):
                            cursor.execute("""UPDATE hr_guy SET requested_quota = (requested_quota + '%s'::numeric) WHERE user_name = '%s'""" % (quota, username))
                            st.success(f"Thank you! Your request has been sent to the administrator.")

                # Update personal information
                with st.expander("Update your personal information"):
                    with st.form(key='Update personal information'):
                         option = st.selectbox(
                         'What do you want to update?',
                         ('First name','Last name', 'Company', 'Email address'))
                         updated_info = st.text_input(label='Enter updated information')
                         submit_button = st.form_submit_button(label='Update')
                         if(submit_button):
                             if option == 'First name':
                                 cursor.execute("""UPDATE hr_guy SET first_name = '%s' WHERE user_name = '%s'""" % (updated_info, username))
                                 st.success(f"Your first name has been changed.")

                             if option == 'Last name':
                                 cursor.execute("""UPDATE hr_guy SET last_name = '%s' WHERE user_name = '%s'""" % (updated_info, username))
                                 st.success(f"Your last name has been changed.")

                             if option == 'Company':
                                 cursor.execute("""UPDATE hr_guy SET company = '%s' WHERE user_name = '%s'""" % (updated_info, username))
                                 st.success(f"Your company name has been changed.")


                             if option == 'Email address':
                                 cursor.execute("""UPDATE hr_guy SET email_address = '%s' WHERE user_name = '%s'""" % (updated_info, username))
                                 st.success(f"Your email address has been changed.")


                # Show the table with the information about teams
                cursor.execute("""SELECT team_name, COUNT(*) AS members FROM potential_candidate WHERE hr_guy = '%s' GROUP BY team_name""" % (username))
                result1=cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                df1 = pd.DataFrame(data=result1, columns=column_names)
                st.dataframe(df1)

                # Teams statistic
                st.subheader("Your teams statistic")
                cursor.execute("""SELECT team_name FROM potential_candidate WHERE hr_guy='%s' GROUP BY team_name"""% (username))
                result2=cursor.fetchall()
                teams=len(list(result2)) # Number of teams
                i=0
                for i in range(teams):
                    team = result2[i][0]
                    with st.expander(f"Team {team}"):
                        cursor.execute("""SELECT first_name, last_name, is_submitted FROM potential_candidate WHERE hr_guy='%s' AND team_name = '%s'"""% (username, team))
                        table=cursor.fetchall()
                        column_names = [desc[0] for desc in cursor.description]
                        df1 = pd.DataFrame(data=table, columns=column_names)
                        st.dataframe(df1)

                        cursor.execute("""SELECT age FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id WHERE hr_guy = '%s' AND team_name = '%s' AND age IS NOT NULL"""% (username, team))
                        age = cursor.fetchone()
                        if age is not None:
                            cursor.execute("""SELECT ROUND(AVG(age), 2) FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id WHERE hr_guy = '%s' AND team_name = '%s' AND age IS NOT NULL"""% (username, team))
                            age = cursor.fetchall()
                            st.write(f'**Average age** of the team is {age[0][0]}')

                        cursor.execute(f"""SELECT gender
                                        FROM survey
                                        INNER JOIN potential_candidate ON survey.id = potential_candidate.id
                                        WHERE hr_guy = '%s' AND team_name = '%s' AND gender IS NOT NULL"""% (username, team))
                        result_gender = cursor.fetchone()
                        if result_gender is not None:
                            st.write('**Gender ratio** (in %) in the team:')
                            cursor.execute(f"""SELECT ROUND((SUM(CASE WHEN gender = 'Male' THEN 1 ELSE 0 END))::numeric / COUNT(*)::numeric,2) as rate_male,
                                                                ROUND((SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END))::numeric / COUNT(*)::numeric,2) as rate_female,
                                                                ROUND((SUM(CASE WHEN gender = 'Genderqueer/Non-Binary' OR gender = 'Prefer not to disclose' THEN 1 ELSE 0 END))::numeric / COUNT(*)::numeric,2) as rate_others
                                                                FROM survey INNER JOIN potential_candidate ON survey.id = potential_candidate.id
                                                                WHERE hr_guy = '%s' AND team_name = '%s' AND gender IS NOT NULL"""% (username, team))
                            result_gender = cursor.fetchone()
                            column_names1 = [desc[0] for desc in cursor.description]
                            df2 = pd.DataFrame(data=[result_gender], columns=column_names1)
                            st.dataframe(df2)

                        cursor.execute(f"""SELECT job_experience FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id WHERE hr_guy = '%s' AND team_name = '%s' AND job_experience IS NOT NULL"""% (username, team))
                        experience = cursor.fetchone()
                        if experience is not None:
                            cursor.execute(f"""SELECT ROUND(AVG(job_experience), 2) FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id WHERE hr_guy = '%s' AND team_name = '%s' AND job_experience IS NOT NULL"""% (username, team))
                            experience = cursor.fetchall()
                            st.write(f'**Average work experience on similar position** of the team is {experience[0][0]}')

                        cursor.execute("""SELECT freetime_activity FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id WHERE hr_guy='%s' AND freetime_activity IS NOT NULL""" % (username))
                        hobbies = cursor.fetchone()
                        if hobbies is not None:
                            st.write("**Hobbies** of the team members are:")
                            cursor.execute("""SELECT freetime_activity FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id WHERE hr_guy='%s' AND freetime_activity IS NOT NULL""" % (username))
                            hobbies = cursor.fetchall()
                            num_hob=len(list(hobbies)) # Number of teams
                            i=0
                            for i in range(num_hob):
                                st.write(f"{i+1}:  {hobbies[i][0]}")

                        cursor.execute("""SELECT action_or_not
                                        FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                                        WHERE hr_guy = '%s' AND team_name = '%s' AND action_or_not IS NOT NULL"""% (username, team))
                        action = cursor.fetchone()
                        if action is not None:
                            cursor.execute("""SELECT (SUM(CASE WHEN action_or_not = 'Near' THEN 1 ELSE 0 END)) as num_near,	(SUM(CASE WHEN action_or_not = 'Away' THEN 1 ELSE 0 END)) as num_away
                            FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                            WHERE hr_guy = '%s' AND team_name = '%s' AND action_or_not IS NOT NULL"""% (username, team))
                            action = cursor.fetchall()
                            bars = ('Near', 'Away')
                            height = [action[0][0], action[0][1]]
                            fig = plt.figure(figsize = (10, 5))
                            plt.bar(bars, height)
                            plt.xlabel("Do you like to sit near the action or away from it?")
                            plt.ylabel("Number")
                            st.pyplot(fig)

                        cursor.execute("""SELECT learning_style
                                                  FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                                                  WHERE hr_guy = '%s' AND team_name = '%s' AND learning_style IS NOT NULL"""% (username, team))
                        learn = cursor.fetchone()
                        if learn is not None:
                            cursor.execute("""SELECT (SUM(CASE WHEN learning_style = 'visual learners (see it done)' THEN 1 ELSE 0 END)) as num_visual,
    		                                          (SUM(CASE WHEN learning_style = 'auditory (hear how to do it)' THEN 1 ELSE 0 END)) as num_auditory,
    		                                          (SUM(CASE WHEN learning_style = 'tactile/kinesthetic (try it out)' THEN 1 ELSE 0 END)) as num_tactile
                                                      FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                                                      WHERE hr_guy = '%s' AND team_name = '%s' AND learning_style IS NOT NULL"""% (username, team))
                            learn = cursor.fetchall()
                            bars = ('Visual', 'Auditory', 'Kinesthetic')
                            height = [learn[0][0], learn[0][1], learn[0][2]]
                            fig = plt.figure(figsize = (10, 5))
                            plt.barh(bars, height)
                            plt.xlabel('What is your preferred learning style?')
                            plt.ylabel("Number")
                            st.pyplot(fig)

                        cursor.execute("""SELECT new_people
                                                  FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                                                  WHERE hr_guy = '%s' AND team_name = '%s' AND new_people IS NOT NULL"""% (username, team))
                        people = cursor.fetchone()
                        if people is not None:
                            cursor.execute("""SELECT (SUM(CASE WHEN new_people = '1' THEN 1 ELSE 0 END)) as num_1, (SUM(CASE WHEN new_people = '2' THEN 1 ELSE 0 END)) as num_2,
    		                                          (SUM(CASE WHEN new_people = '3' THEN 1 ELSE 0 END)) as num_3,	(SUM(CASE WHEN new_people = '4' THEN 1 ELSE 0 END)) as num_4,
    		                                          (SUM(CASE WHEN new_people = '5' THEN 1 ELSE 0 END)) as num_5
                                                      FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                                                      WHERE hr_guy = '%s' AND team_name = '%s' AND new_people IS NOT NULL"""% (username, team))
                            people = cursor.fetchall()
                            pies = ('1-I do not like to meet new people', '2-I would rather prefer to have less contacts', '3-I am indifferent to new acquiaintances','4-It is nice to meet new people', '5-I meet new people every day, it is not a problem for me at all')
                            num = [people[0][0], people[0][1], people[0][2], people[0][3], people[0][4]]
                            fig = plt.figure(figsize=(10, 4))
                            plt.pie(num, labels = pies)
                            st.pyplot(fig)

                        cursor.execute("""SELECT team_or_not
                                            FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                                            WHERE hr_guy = '%s' AND team_name = '%s' AND team_or_not IS NOT NULL"""% (username, team))
                        alone = cursor.fetchone()
                        if alone is not None:
                            cursor.execute("""SELECT (SUM(CASE WHEN team_or_not = 'Teamworker' THEN 1 ELSE 0 END)) as num_team, (SUM(CASE WHEN team_or_not = 'Alone' THEN 1 ELSE 0 END)) as num_alone
                                                FROM potential_candidate INNER JOIN survey ON potential_candidate.id = survey.id
                                                WHERE hr_guy = '%s' AND team_name = '%s' AND team_or_not IS NOT NULL"""% (username, team))
                            alone = cursor.fetchall()
                            bars = ('Teamplayer', 'Alone')
                            height = [alone[0][0], alone[0][1]]
                            fig = plt.figure(figsize = (10, 5))
                            plt.bar(bars, height)
                            plt.xlabel("Do you prefer working independently or on a team?")
                            plt.ylabel("Number")
                            st.pyplot(fig)


    # Close a cursor
    conn.commit()
    conn.close()

    #-------------Potential candidate------------

if unique_option == "Potential candidate":

    db_info = get_config()
    # Open a cursor to perform database operations
    conn = psycopg2.connect(**db_info)
    cursor = conn.cursor()

    st.subheader("Welcome to the HRD survey!")
    # Check the user in database
    id = st.text_input(label='Please enter your identification number from the received email')
    submit_button = st.checkbox(label='I am ready to complete the survey')
    if (submit_button):
        if id == "":
            st.warning('Please enter your id number.')
        else:
            cursor.execute("""SELECT * FROM potential_candidate WHERE id = '%s' """ % (id))
            is_invited = cursor.fetchone()
            if is_invited is None:
                st.error("Sorry, the given id number is not found in the list of invited persons.")
            else:
                cursor.execute("""SELECT * FROM survey WHERE id = '%s' """ % (id))
                is_submitted = cursor.fetchone()
                if is_submitted is None:
                    # The survey interface
                    st.success('Welcome!')
                    st.write('Please answer the following questions. After submitting the survey you will not be able to make any changes or to fill out the survey one more time.')
                    with st.form(key='Survey'):
                        question1 = st.selectbox(
                         'Choose your gender?',
                         ('Male', 'Female', 'Genderqueer/Non-Binary', 'Prefer not to disclose'))
                        question2 = st.slider('How old are you?', 0, 100, 25)
                        question3 = st.number_input('What is your job experience on the similar position (years)?')
                        question4 = st.text_input('What do you prefer to do during your spare time?')
                        question5 = st.radio('Do you like to sit near the action or away from it?',['Near','Away'])
                        question6 = st.selectbox(
                         'Where in the train/airplane do you prefer to sit?',
                         ('Window', 'Middle', 'Aisle'))
                        question7 = st.radio('What is your preferred learning style?',['visual learners (see it done)','auditory (hear how to do it)','tactile/kinesthetic (try it out)'])
                        question8 = st.slider('Is it easy for you to meet new people? (1-I do not like to meet new people, 2-I would rather prefer to have less contacts, 3-I am indifferent to new acquiaintances, 4-It is nice to meet new people, 5-I meet new people every day, it is not a problem for me at all)',1, 5, 3)
                        question9 = st.radio('Do you prefer working independently or on a team?',['Teamworker','Alone'])
                        complete_button = st.form_submit_button(label='Complete')
                        if(complete_button):
                            # Insert all data in DB
                            cursor.execute("""INSERT INTO survey (id, gender, age, job_experience, freetime_activity, action_or_not, seat, learning_style, new_people, team_or_not)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning *""", (id, question1, question2, question3, question4, question5, question6, question7, question8, question9))
                            result=cursor.fetchall()
                            cursor.execute("""UPDATE potential_candidate SET is_submitted = 'TRUE' WHERE id = '%s'""" % (id))
                            st.success(f"Thank you for your answers! You completed the survey.")
                else:
                    st.error("You have already completed the survey.")

    # Close a cursor
    conn.commit()
    conn.close()
