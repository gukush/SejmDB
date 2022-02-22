import pyodbc
import pandas as pd
import numpy as np
some_pass = "MY_PASSWORD"
some_uid = "MY_USERNAME"
some_server = "MY_SERVER"
cnxn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"+f"Server={some_server};Database=SejmVote;UID={some_uid};PWD={some_pass}")
cursor = cnxn.cursor()

nameQuery="SELECT DISTINCT NAME FROM VOTES"
cursor.execute(nameQuery)
table = cursor.fetchall()
bad_patterns = [' Ł',' Ń',' Ś',' Ą',' Ź',' Ę','  ']
exception="ŁUKASZ"
for row in table:
    #print(row[0])
    temp = row[0]
    if "ŁUKASZ" in temp:
        if '  ' in temp:
            temp2 = temp.replace('  ',' ')
            sql=f"UPDATE VOTES SET NAME='{temp2}' WHERE NAME='{temp}'"
            cursor.execute(sql)
    else:
        for sub in bad_patterns:
            if sub in temp:
                temp2=temp.replace(sub,sub[1])
                sql=f"UPDATE VOTES SET NAME='{temp2}' WHERE NAME='{temp}'"
                cursor.execute(sql)
cursor.commit()


#Polish characters have problems sometimes where they add a space in front of the character, sometimes they dont
